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

  输出：stdout = <<<CT_ANSWER_START>>> ... <<<CT_ANSWER_END>>> + sha256
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import subprocess
from pathlib import Path

# UTF-8 强制（三流统一）
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
for _p in (str(SCRIPT_DIR), str(SKILL_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── 下游代码模块 ──────────────────────────────────────────────────────────────
from route import is_vague
from orchestrate import (
    ANSWER_START, ANSWER_END, _wrap,
    run_orchestrate,
)
from doc_memory import build_file_payload

# 定界符常量
TOOL_DELEGATE_START = "<<<CT_TOOL_DELEGATE>>>"
TOOL_DELEGATE_END = "<<<CT_TOOL_DELEGATE_END>>>"

# 5MB 体积门
MAX_FILE_BYTES = 5 * 1024 * 1024


def _safe_wrap_with_checksum(text: str) -> str:
    """sha256 校验包裹（与 orchestrate._wrap 同格式）"""
    return _wrap(text)


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
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "office_to_md.py"), str(p)],
            capture_output=True, text=True, timeout=120
        )
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
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "clarify_loop.py"),
         "--payload-inline", payload],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout)
    except Exception:
        return {"status": "decidable", "ambiguous": False, "questions": []}


def _extract_delegate_card(output: str) -> str | None:
    """从输出中提取 CT_TOOL_DELEGATE 块的 card JSON（若有）"""
    if TOOL_DELEGATE_START not in output:
        return None
    start = output.index(TOOL_DELEGATE_START) + len(TOOL_DELEGATE_START)
    end = output.index(TOOL_DELEGATE_END)
    block = output[start:end].strip()
    try:
        card = json.loads(block)
        return json.dumps(card, ensure_ascii=False)
    except Exception:
        return None


def _run_card_inline(card_json: str, config_path: str) -> str:
    """代码执行 ct 技能并缝合（跳过 LLM 决策）"""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "refine_answer.py"),
         "--card-inline", card_json,
         "--config", config_path],
        capture_output=True, text=True, timeout=300
    )
    return result.stdout


def main():
    ap = argparse.ArgumentParser(
        description="ct-advisor 唯一代码入口（本地 LLM 唯一允许动作）"
    )
    ap.add_argument("--q", required=True, help="用户问题")
    ap.add_argument("--attach", default=None, help="附件路径")
    ap.add_argument("--q-meta", default=None, help="可选 query_meta JSON")
    ap.add_argument("--config", default=str(SKILL_ROOT / "config.json"))
    ap.add_argument("--max-clarify", type=int, default=3, help="澄清轮数上限")
    args = ap.parse_args()

    original_question = args.q
    query_meta = json.loads(args.q_meta) if args.q_meta else {}
    doc_context = ""

    # ── 1) 附件判断 ─────────────────────────────────────────────────────────
    if args.attach:
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

    payload = json.dumps({
        "query_meta": query_meta,
        "original_question": original_question,
        "draft_answer": "",
        "doc_context": doc_context,
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

    # ── 5) 发往 Coze ────────────────────────────────────────────────────────
    sys.stderr.write("[entry] 发往 Coze...\n")
    try:
        output = run_orchestrate(payload, args.config)
    except Exception as e:
        sys.stderr.write(f"[entry] orchestrate 异常: {type(e).__name__}: {e}\n")
        output = _safe_wrap_with_checksum(
            f"⚠️ Coze 服务暂时不可用（{type(e).__name__}），"
            f"请稍后重试或检查网络连接。"
        )

    # ── 6) 检测 CT_TOOL_DELEGATE → 代码自动执行 card-inline ─────────────
    card_json = _extract_delegate_card(output)
    if card_json:
        sys.stderr.write("[entry] 检测到工具委托，代码自动执行 card-inline\n")
        try:
            output = _run_card_inline(card_json, args.config)
        except Exception as e:
            sys.stderr.write(f"[entry] card-inline 异常: {type(e).__name__}: {e}\n")

    sys.stdout.write(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
