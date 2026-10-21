#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ct-advisor — 唯一代码入口（本地 LLM 唯一允许的动作）

架构原则（最高优先级）：
  本地大模型（LLM）在本技能中**唯一允许的动作**是调用本脚本，并把 stdout
  原样透传给终端用户。任何难度判定、附件预处理、Coze 调用、结果缝合均由本脚本内部代码完成。

正确流程（2026-09-25 修正）：
  1) 附件判断：>5MB 本地转 Markdown 后按 .md 附件上传；<5MB 原文件直接上传
     （两条路径统一走 doc_context 通道，Coze 端拿到的都是文件附件）
  2) 难度分级：仅判断 vague / non-vague
  3) vague → 本地澄清循环；non-vague → 直接发 Coze

用法：
  python scripts/entry.py --q "用户问题"
  python scripts/entry.py --q "用户问题" --attach "/path/to/file.docx"

  输出：stdout = <<<CT_ANSWER_B64_START>>> {base64 载荷} <<<CT_ANSWER_B64_END>>> + sha256
  （v1.3.9：base64 ASCII-safe 出口，免疫 PowerShell cp936 捕获乱码；agent 先解码再校验）
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import subprocess
import time
from pathlib import Path

# UTF-8 强制（三流统一）+ stdout 恒 LF（2026-10-15：控制台回传链路会把 \n
# 转 \r\n，源头输出 LF + 校验和按 LF 口径计算，双保险免疫 CRLF 损耗）
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
for _p in (str(SCRIPT_DIR), str(SKILL_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Windows 子进程无控制台窗口（2026-10-15）─────────────────────────────────
# python.exe 是控制台子系统程序：父进程自身没有控制台时（如 WorkBuddy 桌面端
# 宿主直接拉起本脚本），下方 office_to_md / clarify_loop / refine_answer 等
# 子进程会让 Windows 新建控制台 → 屏幕闪出前台弹窗。CREATE_NO_WINDOW
# （+ STARTF_USESHOWWINDOW / SW_HIDE 双保险）令子进程完全后台运行；
# 三处调用均为 capture_output 管道捕获，取值不受影响。
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


def _hidden_kwargs() -> dict:
    """返回抑制控制台弹窗的 subprocess 关键字参数（非 Windows 平台返回 {}）。"""
    if not sys.platform.startswith("win"):
        return {}
    kw = {"creationflags": _CREATE_NO_WINDOW}
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        kw["startupinfo"] = si
    except Exception:
        pass
    return kw

# ── 下游代码模块 ──────────────────────────────────────────────────────────────
from route import is_vague
from orchestrate import (
    ANSWER_START, ANSWER_END, _wrap,
    ANSWER_B64_START, ANSWER_B64_END,
    run_orchestrate,
)

# ── B1 task 推断（2026-10-08）：payload 增加 suggested_task 辅助 Coze 端标注 ──
# 2026-10-16 修复：suggested_task 此前被 orchestrate._build_request 静默丢弃。
# 现通过 query_meta.task_category 透传到 Coze（orchestrate.py 同步修改）。
TASK_KEYWORDS = {
    "pairwise_meta": ["meta分析", "荟萃分析", "meta-analysis", "pooled", "合并效应量", "森林图"],
    "subgroup_analysis": ["亚组", "subgroup", "分层分析"],
    "single_group_meta": ["单组率", "单组均值", "metaprop", "metamean"],
    "nma": ["网状meta", "network meta", "nma", "multiple treatments"],
    "metareg": ["元回归", "metareg", "meta-regression"],
    "samplesize": ["样本量", "sample power", "检验效能", "power"],
    "survival_meta": ["生存meta", "hr", "hazard ratio", "km曲线"],
    "diagnostic_meta": ["诊断meta", "灵敏度", "特异度", "auc", "roc"],
}

def _infer_task(question: str) -> str:
    q = (question or "").lower()
    for task, kws in TASK_KEYWORDS.items():
        if any(kw.lower() in q for kw in kws):
            return task
    return "unclassified"

# §16.9 适配层：常驻编排服务的本地 HTTP 客户端（出站 urllib 逻辑已下沉）
from adapters.local_service_client import run_orchestrate_via_server

# 定界符常量
TOOL_DELEGATE_START = "<<<CT_TOOL_DELEGATE>>>"
TOOL_DELEGATE_END = "<<<CT_TOOL_DELEGATE_END>>>"

# 5MB 体积门
MAX_FILE_BYTES = 5 * 1024 * 1024


def _safe_wrap_with_checksum(text: str) -> str:
    """sha256 校验包裹（与 orchestrate._wrap 同格式）"""
    return _wrap(text)


def _extract_plain(output: str) -> str:
    """从出口载荷（<<<CT_ANSWER_B64_START>>>…<END>>> + sha256）解出纯答案文本。

    非包裹形态（本地澄清提示 / 降级提示）原样返回。用于会话历史记录——Coze 注入的
    conversation_history 需要可读摘要，而非 B64 包裹。
    """
    try:
        m = re.search(
            re.escape(ANSWER_B64_START) + r"\s*(.*?)\s*" + re.escape(ANSWER_B64_END),
            output or "", re.S,
        )
        if not m:
            return output or ""
        return base64.b64decode(m.group(1).strip()).decode("utf-8")
    except Exception:  # noqa: BLE001
        return output or ""


def _emit_output(output: str, args) -> None:
    """统一出口（2026-10-22）：处理 --out 落盘 / stdout 透传，并正常退出。

    抽离原因：短路（dedup/cache 命中）与真实出站两路最终都走同一出口，
    避免出口逻辑散落导致「--out 只在某路径生效」的不一致。
    """
    if args.out:
        try:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output, encoding="utf-8")
            sys.stdout.write(f"[entry] 结果已写入 {out_path} ({len(output)} chars)\n")
        except Exception as e:  # noqa: BLE001
            sys.stderr.write(f"[entry] --out 写入失败: {type(e).__name__}: {e}\n")
            sys.stdout.write(output)
    else:
        sys.stdout.write(output)
    sys.exit(0)


def _handle_attachment_oversized(attach_path: str, question: str) -> tuple:
    """附件 >5MB：本地转 Markdown 后**按 .md 附件上传**（doc_context 通道）。

    返回 (question, doc_context)。Coze 端拿到的是一份标准 .md 文件
    （经 /upload_file → mode=file_id），与 <5MB 原文件上传同一条通道。
    解析失败 / 格式不支持时返回 (带 ⚠️ 提示的 question, "")。
    """
    import tempfile
    p = Path(attach_path)
    ext = p.suffix.lower()

    if ext in (".docx", ".xlsx", ".pptx"):
        # 2026-10-16 修复：subprocess.run 的 TimeoutExpired / OSError 此前未被捕获，
        # 大附件转换卡住或拉起失败会让 main 直接崩溃（stdout 为空，agent 无从交代）。
        # 附件转换是**可选增强**，失败应降级为「带提示的无附件提问」继续主流程。
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "office_to_md.py"), str(p)],
                capture_output=True, text=True, timeout=120, **_hidden_kwargs()
            )
        except Exception as _e:  # noqa: BLE001
            return question + (
                f"\n\n⚠️ 附件《{p.name}》本地转换失败（{type(_e).__name__}），未能上传。请精简内容至 5MB 以下后重试。"
            ), ""
        if result.returncode != 0:
            return question + f"\n\n⚠️ 附件《{p.name}》解析失败，未能上传: {result.stderr[:200]}", ""
        md = result.stdout
    elif ext in (".txt", ".md", ".csv", ".tsv", ".json"):
        md = p.read_text(encoding="utf-8", errors="replace")
    else:
        return question + (
            f"\n\n⚠️ 附件《{p.name}》体积超过 5MB，格式 {ext} 暂不支持本地转换。"
            f"请精简内容至 5MB 以下后重试，或另存为 .docx/.xlsx/.pptx/.txt/.md。"
        ), ""

    # 写出临时 .md，按 md 格式走统一上传通道（<5MB 同一套账）
    md_path = Path(tempfile.gettempdir()) / f"ctadv_{p.stem}_oversized.md"
    md_path.write_text(md, encoding="utf-8")
    sys.stderr.write(f"[entry] >5MB 已转 md: {md_path} ({md_path.stat().st_size / 1024:.1f} KB)\n")
    payload_json, doc_id = build_file_payload(
        path=str(md_path),
        instruction=question,
        allow_upload=True,
    )
    note = (
        f"\n\nℹ️ 附件《{p.name}》体积超过 5MB，已转换为 Markdown 版并随问题上传，"
        f"云端将基于转换后的 .md 全文作答。"
    )
    return question + note, payload_json


def _handle_attachment_normal(attach_path: str, question: str) -> str:
    """附件 <5MB：调用 build_file_payload 构建 doc_context（JSON 字符串）。

    allow_upload=True 强制走上传通道（mode=file_id）——Coze 端原生解析原始文件，
    保真度高于本地转 md；上传失败时 build_file_payload 内部自动降级老通道
    （mode=file 转发 base64），仍不可行返回空串。
    """
    payload_json, doc_id = build_file_payload(
        path=attach_path,
        instruction=question,
        allow_upload=True,
    )
    return payload_json


def _run_clarify(original_question: str, max_rounds: int = 3) -> dict:
    """调用 clarify_loop 获取澄清问题（纯本地，无网络）"""
    payload = json.dumps({
        "original_question": original_question,
        "previous_answers": [],
        "round": 0,
        "max_rounds": max_rounds,
    }, ensure_ascii=False)
    # 2026-10-16 修复：subprocess.run 的 TimeoutExpired / OSError 此前落在 try 之外，
    # clarify_loop 卡住或拉起失败会让 main 直接崩溃。澄清是**可选**增强步骤，
    # 任何失败都必须降级为「可直接作答」并继续主流程，绝不阻断。
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "clarify_loop.py"),
             "--payload-inline", payload],
            capture_output=True, text=True, timeout=30, **_hidden_kwargs()
        )
        return json.loads(result.stdout)
    except Exception as _e:  # noqa: BLE001
        sys.stderr.write(
            f"[entry] 澄清循环不可用（降级为直接作答）: {type(_e).__name__}: {_e}\n"
        )
        return {"status": "decidable", "ambiguous": False, "questions": []}


def _extract_delegate_card(output: str) -> str | None:
    """从输出中提取 CT_TOOL_DELEGATE 块的 card JSON（若有）。

    2026-10-16 修复：此前 `output.index(TOOL_DELEGATE_END)` 在「有 START 无 END」
    （输出被截断 / 拼接异常）时抛 ValueError，而调用方没有 try → main 直接崩溃、
    stdout 为空。现整段包在 try 内，任何形态异常一律降级为 None（当作无委托处理，
    由上游的 B64 包裹校验兜底）。
    """
    try:
        if TOOL_DELEGATE_START not in output or TOOL_DELEGATE_END not in output:
            return None
        start = output.index(TOOL_DELEGATE_START) + len(TOOL_DELEGATE_START)
        end = output.index(TOOL_DELEGATE_END)
        if end <= start:
            return None
        card = json.loads(output[start:end].strip())
        return json.dumps(card, ensure_ascii=False)
    except Exception:  # noqa: BLE001
        return None


def _run_card_inline(card_json: str, config_path: str) -> str:
    """代码执行 ct 技能并缝合（跳过 LLM 决策）"""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "refine_answer.py"),
         "--card-inline", card_json,
         "--config", config_path],
        capture_output=True, text=True, timeout=300, **_hidden_kwargs()
    )
    return result.stdout


# ── L1：常驻编排服务（减少重模块重复导入，2026-09-25）──────────────────────
# 出站（urllib）逻辑已全部下沉到 adapters/local_service_client.py（§16.9）；
# entry.py 仅保留一个薄封装调用，详见该适配器。
def _run_orchestrate(payload: str, config: str) -> str:
    """常驻编排服务薄封装（出站入口）。

    2026-10-22 重构：本地答案缓存 / 去重短路已上移到 main() 统一由 session_store
    负责（跨 entry / proxy 一致），本函数仅做「常驻服务 → 内联」转发，
    不再内部查 answer_cache（避免与 session_store 双重维护、且无法区分「是否真实出站」）。
    """
    return run_orchestrate_via_server(payload, config)


def main():
    ap = argparse.ArgumentParser(
        description="ct-advisor 唯一代码入口（本地 LLM 唯一允许动作）"
    )
    ap.add_argument("--q", required=True, help="用户问题")
    ap.add_argument("--attach", default=None, help="附件路径")
    ap.add_argument("--q-meta", default=None, help="可选 query_meta JSON")
    ap.add_argument("--config", default=str(SKILL_ROOT / "config.json"))
    ap.add_argument("--max-clarify", type=int, default=3, help="澄清轮数上限")
    ap.add_argument("--out", default=None,
                    help="把完整 stdout（含 B64 块与 checksum）写入该文件；"
                         "stdout 只打印一行确认，避免长载荷经过 agent 上下文")
    ap.add_argument("--session", default="",
                    help="会话标识（跨轮上下文/去重键）：proxy 或飞书应传入稳定 ID；"
                         "缺失则退化为单轮（仍享全局答案缓存，仅无多轮上下文）")
    args = ap.parse_args()

    # ── 0) 依赖预检（2026-10-15 修订：requests 已改为可选） ──
    # 传输层切换为 stdlib urllib（refiner._call_coze）后 requests 不再是必需依赖：
    # 「依赖缺失」作为一类用户可见失败被整体消灭。此处仅留痕，不再 fail-fast 退出——
    # 装了 requests 行为不变，没装也经 urllib 正常出站。
    try:
        import requests  # noqa: F401
    except ImportError:
        sys.stderr.write("[entry] 未检测到 requests，使用 stdlib urllib 传输（功能不受影响）\n")

    original_question = args.q
    # 2026-10-16 修复：非法 --q-meta JSON 此前会让 main 抛 JSONDecodeError 崩溃
    # （stdout 为空）。query_meta 只是可选元信息，解析失败应降级为空 dict 并继续。
    query_meta = {}
    if args.q_meta:
        try:
            _qm = json.loads(args.q_meta)
            if isinstance(_qm, dict):
                query_meta = _qm
            else:
                sys.stderr.write("[entry] --q-meta 不是 JSON 对象（已忽略）\n")
        except Exception as _e:  # noqa: BLE001
            sys.stderr.write(
                f"[entry] --q-meta 非法 JSON（已忽略）: {type(_e).__name__}: {_e}\n"
            )
    doc_context = ""

    # ── 1) 附件判断 ─────────────────────────────────────────────────────────
    if args.attach:
        # 延迟导入（性能修复）：doc_memory(45KB) 仅在确有附件时才加载，避免无附件提问被拖慢
        from doc_memory import build_file_payload
        p = Path(args.attach)
        if not p.exists():
            original_question += f"\n\n⚠️ 附件未找到: {args.attach}"
        else:
            file_size = p.stat().st_size
            sys.stderr.write(f"[entry] 附件: {args.attach}, 体积: {file_size / 1024:.1f} KB\n")

            if file_size > MAX_FILE_BYTES:
                # >5MB：本地转 md 后，按 .md 附件上传（doc_context 通道）
                sys.stderr.write("[entry] 附件 >5MB，转 md 后按 md 格式上传\n")
                original_question, doc_context = _handle_attachment_oversized(args.attach, original_question)
                if doc_context:
                    sys.stderr.write(f"[entry] md doc_context 构建完成 ({len(doc_context)} chars)\n")
            else:
                # <5MB：直接上传（doc_context 通道）
                sys.stderr.write("[entry] 附件 <5MB，构建 doc_context 直接上传\n")
                doc_context = _handle_attachment_normal(args.attach, original_question)
                if doc_context:
                    sys.stderr.write(f"[entry] doc_context 构建完成 ({len(doc_context)} chars)\n")
                else:
                    sys.stderr.write("[entry] doc_context 构建失败，回退为无附件模式\n")

    # ── 2) 难度分级（仅判断 vague）──────────────────────────────────────────
    vague = is_vague(original_question)
    sys.stderr.write(f"[entry] vague: {vague}\n")

    # ── 3) 构建 payload ─────────────────────────────────────────────────────
    # query_meta 仅保留 difficulty（non-vague 统一标记为 forwarded，Coze 端自行判断）
    query_meta["difficulty"] = "vague" if vague else "forwarded"

    # 2026-10-16 修复：scope_hint 主链路缺失。此前 scope_guard 仅在 forward_guards
    # 中生效（refine_answer 路径），entry.py 主链路不调用。现加入 payload，
    # 使 Coze 端能获得范围路由标签（如 medical_writing）。
    _scope_hint = ""
    try:
        from scope_guard import assess as _assess_scope
        _in_scope, _tag, _ = _assess_scope(original_question)
        if not _in_scope and _tag:
            _scope_hint = _tag
            sys.stderr.write(f"[entry] scope_guard: out-of-scope tag={_tag}\n")
    except Exception:
        pass

    # ── 3b) 注入会话上下文（P0-3 修复：主链路此前从未调用 context_stitch，
    # 导致 Coze 永远只拿到单轮问题，用户被迫在「承接上一轮」里手工复述背景）────
    session_id = (args.session or "").strip()
    conversation_history = []
    try:
        import session_store as _ss
        conversation_history = _ss.history(session_id)
        if conversation_history:
            sys.stderr.write(
                f"[entry] 注入会话上下文 {len(conversation_history)} 轮 "
                f"(P0-3 修复)\n")
    except Exception:  # noqa: BLE001
        pass

    payload = json.dumps({
        "query_meta": query_meta,
        "original_question": original_question,
        "draft_answer": "",
        "doc_context": doc_context,
        "suggested_task": _infer_task(original_question),
        "scope_hint": _scope_hint,
        "conversation_history": conversation_history,
    }, ensure_ascii=False)

    # ── 4) vague → 澄清循环 ─────────────────────────────────────────────────
    if vague:
        sys.stderr.write("[entry] 进入澄清循环\n")
        clarify_result = _run_clarify(original_question, args.max_clarify)
        status = clarify_result.get("status", "decidable")
        if status == "need_clarify":
            questions = clarify_result.get("questions", [])
            q_text = "\n".join(f"  - {q}" for q in questions)
            sys.stderr.write(f"[entry] 需澄清 {len(questions)} 项\n")
            sys.stdout.write(_safe_wrap_with_checksum(
                f"在回答之前，需要澄清以下问题：\n\n{q_text}\n\n"
                f"请针对以上问题逐一回复后，我将基于您的补充信息继续分析。"
            ))
            sys.exit(0)
        # decidable / forced_decide → 继续发 Coze

    # ── 5) 短路：近窗去重 + 全局答案缓存（P0-2 修复）────────────────────
    # 对所有路径生效：vague 的 need_clarify 已在步骤 4 提前 exit，不会误短路；
    # 此处仅对「真正会出站」的问题做本地复用（覆盖重复发送澄清类问题也省出站）。
    shortcut = False
    _output_format = query_meta.get("output_format", "") or ""
    try:
        import session_store as _ss
        _dh, _dans, _dsecs = _ss.dedup_check(session_id, original_question,
                                            output_format=_output_format)
        if _dh and _dans:
            sys.stderr.write(
                f"[entry] 近窗重复命中（{_dsecs}s 前）→ 本地短路复用，不出站\n")
            output = _wrap(_dans)
            shortcut = True
        else:
            _cached = _ss.cache_get(
                original_question, doc_context,
                query_meta.get("difficulty", ""),
                output_format=_output_format)
            if _cached:
                sys.stderr.write(
                    "[entry] 全局答案缓存命中 → 本地短路复用，不出站\n")
                output = _wrap(_cached)
                shortcut = True
    except Exception:  # noqa: BLE001
        pass

    if not shortcut:
        # ── 5a) 真实出站 ───────────────────────────────────────────────
        sys.stderr.write("[entry] 进入编排（出站 Coze）...\n")
        try:
            output = _run_orchestrate(payload, args.config)
        except Exception as e:
            sys.stderr.write(f"[entry] orchestrate 异常: {type(e).__name__}: {e}\n")
            output = _safe_wrap_with_checksum(
                f"⚠️ Coze 服务暂时不可用（{type(e).__name__}），"
                f"请稍后重试或检查网络连接。"
            )

        # ── 6) 检测 CT_TOOL_DELEGATE → 代码自动执行 card-inline ──────
        card_json = _extract_delegate_card(output)
        if card_json:
            sys.stderr.write("[entry] 检测到工具委托，代码自动执行 card-inline\n")
            _ci_out = ""
            try:
                _ci_out = _run_card_inline(card_json, args.config)
            except Exception as e:  # noqa: BLE001
                sys.stderr.write(f"[entry] card-inline 异常: {type(e).__name__}: {e}\n")
            if ANSWER_B64_START in _ci_out and ANSWER_B64_END in _ci_out:
                output = _ci_out
            else:
                sys.stderr.write("[entry] card-inline 产物形态异常，降级为人读提示\n")
                output = _safe_wrap_with_checksum(
                    "⚠️ 技能结果缝合失败：委托执行的本地技能未能返回有效结果。\n\n"
                    "可能原因：技能参数不完整、技能执行超时或该技能当前不可用。\n"
                    "请补充必要信息后重试；若持续失败，请把本条提示与上方 stderr 反馈给技能维护者。"
                )

        # ── 6b) 记录会话历史（仅真实出站；短路命中不重复记轮）────────
        try:
            import session_store as _ss
            _plain = _extract_plain(output)
            if _plain.strip():
                _ss.record(
                    session_id, original_question, answer=_plain,
                    difficulty=query_meta.get("difficulty", ""),
                    doc_context=doc_context,
                    output_format=_output_format,
                )
        except Exception:  # noqa: BLE001
            pass

    # ── 7) 出口 ──────────────────────────────────────────────────────
    _emit_output(output, args)


if __name__ == "__main__":
    # 2026-10-16 顶层兜底（主流程出口契约）：任何未被内部捕获的异常此前都会让
    # Python 打印 traceback 并**留下空 stdout**——agent 只能看到「empty stdout」，
    # 无法向用户交代任何原因。这里统一转成合法的人读提示（B64 包裹），
    # 保证 stdout 永远可交付，agent 侧零决策。
    try:
        main()
    except SystemExit:
        raise
    except BaseException as _e:  # noqa: BLE001
        try:
            sys.stderr.write(f"[entry] 未捕获异常: {type(_e).__name__}: {_e}\n")
            sys.stdout.write(_safe_wrap_with_checksum(
                "⚠️ 技能执行出现未预期错误，无法生成答案。\n\n"
                f"{type(_e).__name__}: {_e}\n\n"
                "请稍后重试；若持续出现，请把本条提示与上方 stderr 反馈给技能维护者。"
            ))
        except Exception:  # noqa: BLE001
            pass
        sys.exit(1)
