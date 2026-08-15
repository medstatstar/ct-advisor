#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ct-advisor — 代码全自动编排器（2026-08-15，模式 B + 委托本地大模型）

设计定位（与用户确认）：
  - 🔴 代码是**全自动编排器 / 决策者**：判定难度、前端高置信预判、并行触发
    Coze 与预判的 ct 技能、合并两边结果、**由代码决定「信息是否已足够」**。
  - 本地大模型**不是**编排器；但「任何代码过程中需要调用其他 ct 技能」这一步
    被**委托给本地大模型执行**（通过 <<<CT_TOOL_DELEGATE>>> 标记块）。
  - 本地大模型只做两件事（只决策 + 代码缝合）：
      1) 补全 / 追问执行卡参数（need_params 时向用户追问，不编造）；
      2) 把执行卡交给 `refine_answer.py` 由**代码**执行技能 + 确定性缝合 + 包裹答案。
  - 本地大模型**不**判断「信息是否足够」、**不**重写 Coze 文本。

与既有协议的关系：
  - 信息足够 → 复用 refine_answer.py 的 <<<CT_ANSWER_START>>>…<<<CT_ANSWER_END>>> 定界包裹
    （含 sha256 校验和），本地大模型只做原样透传（pipe），与 --ship 同协议。
  - 仍需 ct 技能 → 输出 <<<CT_TOOL_DELEGATE>>>…<<<CT_TOOL_DELEGATE_END>>> 结构化块，
    本地大模型读取后执行（见下方「委托协议」），最终仍由 --card-inline 走代码缝合。

委托协议（本地大模型收到 <<<CT_TOOL_DELEGATE>>> 后的动作）：
  1. 读取块内 need_tool / params / draft_answer / original_question；
  2. 若 params 完整 → 直接 `python scripts/refine_answer.py --card-inline '<执行卡 JSON>'`；
  3. 若缺失 → 向用户追问补齐（不编造），再执行上述 --card-inline；
  --card-inline 会由代码执行技能 + 缝合 Coze 草稿 + 包裹最终答案（大模型不重写）。

用法：
  python scripts/orchestrate.py --payload-inline '<3变量 JSON>'
        → 输出 <<<CT_ANSWER_START>>>…<<<CT_ANSWER_END>>>（信息足够，pipe 透传）
          或 <<<CT_TOOL_DELEGATE>>>…<<<CT_TOOL_DELEGATE_END>>>（委托大模型调 ct 技能）
  python scripts/orchestrate.py --payload-inline '<JSON>' --no-prefetch
        → 跳过前端预判预取，仅走 Coze；Coze 判定需工具时仍委托大模型
  python scripts/orchestrate.py --self-test
        → 跑内置编排决策自测（mock Coze / 预判，无网络 / 无本地技能调用）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
for _p in (str(SCRIPT_DIR), str(SKILL_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# 复用 refine_answer.py 的权威包裹 / 执行原语（单一数据源，避免漂移）
from refine_answer import (  # noqa: E402
    _merge_answer, _run_handle_need_tool,
    _check_outbound_authorization, _get_endpoint_from_config,
    ANSWER_START, ANSWER_END, NEED_PARAMS_MARKER,
)
# 复用入口预判（模式 B 前端高置信预取）
from route_tool import predict as predict_tool  # noqa: E402
from adapters import build_refiner, RefineRequest, RefineResult  # noqa: E402

# 编码统一（与 refine_answer.py 一致）：三流强制 UTF-8，避免 CJK/℃ 在 Windows cp936 下乱码
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

# 委托标记（本编排器新增；与 ANSWER_START/END 同家族，供本地大模型识别）
TOOL_DELEGATE_START = "<<<CT_TOOL_DELEGATE>>>"
TOOL_DELEGATE_END = "<<<CT_TOOL_DELEGATE_END>>>"


# ---------------------------------------------------------------------------
# 输出构造（确定性，无 LLM）
# ---------------------------------------------------------------------------

def _wrap(text: str) -> str:
    """把最终答案用定界符包裹 + sha256 校验和（与 refine_answer._emit_wrapped 同格式）。"""
    checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{ANSWER_START}\n{text}\n{ANSWER_END}\nchecksum: {checksum}\n"


def _enrich_coze_params(orig_q: str, coze_tool: str | None, coze_params: dict) -> dict:
    """用本地 route_tool 预判补全 Coze 判定工具的真实入参（Coze 仅判类别、不抽真实参数）。

    与 refine_answer.py --ship 同策略：route_tool 抽到的真实参数（cond/drug/topic/test/p1/p2）
    覆盖 Coze 默认值（max/top/alpha/power），使「代码走本地全流程」在 need_tool 场景成立，
    避免「Coze 需不同工具」分支(2c)委托时只带 Coze 默认值、再弹一轮 need_params。
    """
    if not coze_tool:
        return dict(coze_params)
    pred = predict_tool(orig_q)
    if pred.get("need_tool") != coze_tool:
        return dict(coze_params)
    out = dict(coze_params)
    for k, v in (pred.get("params") or {}).items():
        if v not in (None, ""):
            out.setdefault(k, v)
    return out


def _render_delegate(orig_q: str, tool: str, params: dict,
                     draft_answer: str, missing: list | None = None,
                     prefetch_satisfied: dict | None = None,
                     note: str | None = None) -> str:
    """构造 <<<CT_TOOL_DELEGATE>>> 结构化块（供本地大模型执行 ct 技能）。

    大模型读取后：补全/追问参数 → 调 `refine_answer.py --card-inline '<执行卡>'`
    由代码执行技能 + 缝合 + 包裹。大模型不重写 Coze 文本。
    """
    if missing is None:
        missing = []
    if prefetch_satisfied is None:
        prefetch_satisfied = {}
    block = {
        "need_tool": tool,
        "params": params or {},
        "draft_answer": draft_answer or "",
        "original_question": orig_q or "",
        "missing_params": missing,
        "prefetch_satisfied": prefetch_satisfied,
        "note": note or (
            "代码预判 / Coze 判定需调用 ct 系列技能补充信息，委托本地大模型执行。"
            "请：①确认或补全执行卡参数（缺失则向用户追问、不编造）；"
            "②将执行卡 JSON 传给 `python scripts/refine_answer.py --card-inline '<JSON>'`，"
            "由代码执行技能并确定性缝合 + 包裹最终答案（本地大模型只做透传，不重写 Coze 文本）。"
        ),
    }
    return (f"{TOOL_DELEGATE_START}\n"
            f"{json.dumps(block, ensure_ascii=False, indent=2)}\n"
            f"{TOOL_DELEGATE_END}\n")


# ---------------------------------------------------------------------------
# 并行触发：Coze + 前端预判 ct 技能
# ---------------------------------------------------------------------------

def _fire_coze(req: RefineRequest, config_path: str) -> RefineResult:
    """线程内调用 Coze 全量直发；任何异常回退草稿（不抛，交由决策逻辑处理）。"""
    try:
        return build_refiner(config_path=config_path).refine_forward(req)
    except Exception:  # noqa: BLE001
        return RefineResult(final_answer=req.draft_answer, need_tool=None)


def _fire_prefetch(card: dict) -> dict:
    """线程内机械执行预判的 ct 技能（代码内 subprocess，无 LLM）。"""
    return _run_handle_need_tool(card)


# ---------------------------------------------------------------------------
# 核心决策：合并 + 判定信息是否足够（纯代码，无 LLM）
# ---------------------------------------------------------------------------

def build_output(orig_q: str, coze_result: RefineResult,
                 prefetch_out: dict | None, prefetch_tool: str | None,
                 prefetch_params: dict | None) -> str:
    """返回最终应输出字符串（包裹答案 或 委托块）。

    decision（代码决定，非 LLM）：
      - 预判已执行且 ok，且 Coze 未要求其他工具 → 信息足够 → 包裹答案。
      - 预判已执行且 ok，但 Coze 要求**不同**工具 → 仍委托（Coze 工具），
        预判结果作为补充并入 draft_answer。
      - 预判 need_params / error，且存在待调工具 → 委托（补全参数或重试）。
      - 无预判但 Coze 要求工具 → 委托。
      - Coze 未要求工具且预判无有效补充 → Coze 答案足够 → 包裹。
    """
    coze_answer = coze_result.final_answer or ""
    coze_tool = coze_result.need_tool
    # P2 修复（2026-08-15）：对 Coze 判定工具做本地 route_tool 参数富集，
    # 避免「Coze 需不同工具」分支(2c)委托时只带 Coze 默认值、再弹一轮 need_params。
    coze_params = _enrich_coze_params(orig_q, coze_tool, coze_result.params or {})

    # ---- 有预判执行结果 ----
    if prefetch_out is not None:
        status = prefetch_out.get("status")
        tool = prefetch_out.get("tool") or prefetch_tool
        if status == "ok":
            if coze_tool is None or coze_tool == tool:
                # 信息足够：Coze 答案 + 预判技能结果
                return _wrap(_merge_answer(coze_answer, prefetch_out))
            # Coze 要求不同工具：预判结果并入草稿，委托 Coze 工具
            base = _merge_answer(coze_answer, prefetch_out) if coze_answer.strip() else \
                f"## 补充信息（来源：{tool}）\n\n" + _render_skill_text(prefetch_out)
            return _render_delegate(
                orig_q, coze_tool, coze_params, base,
                prefetch_satisfied={tool: prefetch_out.get("result")},
                note="预判技能已执行；Coze 另需补充「%s」信息，委托本地大模型执行该技能。" % coze_tool,
            )
        if status == "need_params":
            # 预判参数不完整 → 委托大模型追问后执行
            missing = (prefetch_out.get("result") or {}).get("missing", [])
            return _render_delegate(
                orig_q, tool, prefetch_params or {}, coze_answer, missing=missing,
                note="预判技能参数不完整（%s），委托本地大模型向用户追问后执行。" % "; ".join(missing),
            )
        # error：预判执行失败
        if coze_tool:
            return _render_delegate(
                orig_q, coze_tool, coze_params, coze_answer,
                note="预判技能执行出错，Coze 仍判定需补充「%s」，委托本地大模型重新执行。" % coze_tool,
            )
        # 预判失败且无 Coze 工具 → 仅 Coze 答案（若有）或兜底警告
        if coze_answer.strip():
            return _wrap(coze_answer)
        return _wrap("⚠️ 预判技能执行出错且 Coze 未返回有效答案，请基于本地知识库兜底作答并告知用户。")

    # ---- 无预判 ----
    if coze_tool:
        return _render_delegate(orig_q, coze_tool, coze_params, coze_answer)
    if coze_answer.strip():
        return _wrap(coze_answer)
    return _wrap("⚠️ Coze 返回为空，请基于本地知识库作答并告知用户。")


def _render_skill_text(tool_out: dict) -> str:
    """把技能主产物渲染为可读文本（与 refine_answer._render_skill_result 同逻辑）。"""
    res = tool_out.get("result")
    if isinstance(res, (dict, list)):
        try:
            return json.dumps(res, ensure_ascii=False, indent=2)
        except Exception:
            return str(res)
    return str(res) if res is not None else ""


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def _build_request(raw: str) -> RefineRequest:
    obj = json.loads(raw)
    req = RefineRequest(
        query_meta=obj.get("query_meta", "") if isinstance(obj, dict) else "",
        original_question=str((obj or {}).get("original_question", "")),
        draft_answer=str((obj or {}).get("draft_answer", "")),
    )
    return req


def run_orchestrate(raw: str, config_path: str, no_prefetch: bool = False) -> str:
    req = _build_request(raw)
    req.normalize()

    orig_q = req.original_question or ""

    # 1) 前端高置信预判（模式 B 预取）—— 仅高置信才触发，漏判由 Coze 兜底
    pred = predict_tool(orig_q) if not no_prefetch else {"need_tool": None, "params": {}}
    prefetch_tool = pred.get("need_tool")
    prefetch_params = pred.get("params") or {}

    # 2) 并行触发：Coze（需授权）+ 预判 ct 技能（本地执行，免授权）
    coze_result = [None]
    prefetch_out = [None]
    threads = []

    def _coze_job():
        if not _check_outbound_authorization(_get_endpoint_from_config(config_path), config_path):
            coze_result[0] = RefineResult(final_answer=req.draft_answer, need_tool=None)
            return
        coze_result[0] = _fire_coze(req, config_path)

    t_coze = threading.Thread(target=_coze_job, name="coze")
    t_coze.start()
    threads.append(t_coze)

    t_pre = None
    if prefetch_tool:
        card = {
            "need_tool": prefetch_tool,
            "params": prefetch_params,
            "draft_answer": "",
            "original_question": orig_q,
        }
        def _pre_job():
            prefetch_out[0] = _fire_prefetch(card)
        t_pre = threading.Thread(target=_pre_job, name="prefetch")
        t_pre.start()
        threads.append(t_pre)

    for t in threads:
        t.join()

    return build_output(orig_q, coze_result[0], prefetch_out[0], prefetch_tool, prefetch_params)


# ---------------------------------------------------------------------------
# 内置自测（mock Coze / 预判，无网络 / 无本地技能调用）
# ---------------------------------------------------------------------------

def _mk_coze(final_answer: str, need_tool: str | None = None, params: dict | None = None) -> RefineResult:
    return RefineResult(final_answer=final_answer, need_tool=need_tool, params=params or {})


def _mk_prefetch(tool: str, status: str, result=None) -> dict:
    return {"tool": tool, "status": status, "result": result or {}, "draft_answer": "", "elapsed_sec": 0.0}


SELF_TEST = [
    # (描述, orig_q, coze, prefetch_out, prefetch_tool, prefetch_params, 期望标记)
    ("预判ok且Coze无需工具 → 包裹答案",
     "算样本量 ORR 30% vs 45%", _mk_coze("Coze说算一下"), _mk_prefetch("ct-samplesize", "ok", {"n": 120}),
     "ct-samplesize", {"p1": 0.3, "p2": 0.45}, "CT_ANSWER_START"),

    ("Coze需同工具且预判ok → 包裹答案（不重复调）",
     "算样本量", _mk_coze("Coze草稿", "ct-samplesize", {}), _mk_prefetch("ct-samplesize", "ok", {"n": 99}),
     "ct-samplesize", {}, "CT_ANSWER_START"),

    ("预判need_params → 委托（列出缺失）",
     "算样本量", _mk_coze("Coze草稿", "ct-samplesize", {}),
     _mk_prefetch("ct-samplesize", "need_params", {"missing": ["效应量参数(任选其一): p1 / p2"]}),
     "ct-samplesize", {}, "CT_TOOL_DELEGATE"),

    ("预判ok但Coze需不同工具 → 委托（并入预判）",
     "查PD-1三期试验并算样本量", _mk_coze("Coze草稿", "ct-registry", {"cond": "PD-1"}),
     _mk_prefetch("ct-samplesize", "ok", {"n": 88}), "ct-samplesize", {},
     "CT_TOOL_DELEGATE"),

    ("无预判且Coze需工具 → 委托",
     "XX药文献", _mk_coze("Coze草稿", "ct-literature", {"topic": "XX药"}),
     None, None, {}, "CT_TOOL_DELEGATE"),

    ("Coze答案足够且无预判 → 包裹",
     "什么是SDTM", _mk_coze("SDTM是...", None, {}),
     None, None, {}, "CT_ANSWER_START"),

    ("Coze空 + 无工具 → 兜底警告包裹",
     "边缘问题", _mk_coze("", None, {}),
     None, None, {}, "CT_ANSWER_START"),

    ("预判error但Coze需同工具 → 委托重试",
     "查XX药安全性", _mk_coze("Coze草稿", "ct-safety", {"drug": "XX"}),
     _mk_prefetch("ct-safety", "error", "rc=1"), "ct-safety", {"drug": "XX"},
     "CT_TOOL_DELEGATE"),
]


def run_self_test() -> int:
    print("orchestrate.py 编排决策自测")
    print("=" * 60)
    ok = 0
    for desc, q, coze, pre, pt, pp, expect_marker in SELF_TEST:
        out = build_output(q, coze, pre, pt, pp)
        hit = expect_marker in out
        mark = "✓" if hit else "✗"
        if hit:
            ok += 1
        # 校验包裹格式 / 委托格式之一
        if expect_marker == "CT_ANSWER_START":
            valid = ANSWER_START in out and ANSWER_END in out and "checksum:" in out
        else:
            valid = TOOL_DELEGATE_START in out and TOOL_DELEGATE_END in out
        print(f"  {mark} [{('OK' if valid else 'BADFMT'):<6}] {desc}")
    total = len(SELF_TEST)
    print("-" * 60)
    print(f"  准确率: {ok}/{total} = {ok / total * 100:.1f}%")
    return 0 if ok == total else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="ct-advisor code-only orchestrator (Mode B + LLM delegate)")
    ap.add_argument("--payload-inline", help="inline JSON payload (3变量: query_meta/original_question/draft_answer)")
    ap.add_argument("--payload", help="path to JSON payload file (legacy)")
    ap.add_argument("--config", default=str(SKILL_ROOT / "config.json"), help="path to config.json")
    ap.add_argument("--no-prefetch", action="store_true", help="跳过前端预判预取，仅走 Coze")
    ap.add_argument("--tone", default=None, help="path to tone_profile.json (style-only)")
    ap.add_argument("--memory", default=None, help="path to ct-advisor-memory.json")
    ap.add_argument("--self-test", action="store_true", help="运行内置编排决策自测")
    args = ap.parse_args()

    if args.self_test:
        return run_self_test()

    # 读取 payload（优先 inline，其次文件，再次 stdin）
    if args.payload_inline:
        raw = args.payload_inline
    elif args.payload:
        p = Path(args.payload)
        if not p.exists():
            sys.stderr.write(f"[ct-advisor] payload 文件未找到: {args.payload}\n")
            sys.exit(2)
        raw = p.read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()

    try:
        out = run_orchestrate(raw, args.config, no_prefetch=args.no_prefetch)
    except Exception as e:  # noqa: BLE001
        # 编排器本身崩溃：绝不静默，输出明确兜底，交给调用方本地兜底
        sys.stderr.write(f"[ct-advisor][ORCH-FAIL] {type(e).__name__}: {e}\n")
        sys.stdout.write(
            "⚠️ 编排器执行异常，未产出结构化答案。请基于本地知识库作答并告知用户此警告。"
        )
        sys.exit(0)

    sys.stdout.write(out)
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
