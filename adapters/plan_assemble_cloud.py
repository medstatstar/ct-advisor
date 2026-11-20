#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plan_assemble_cloud.py — Plan 结果的二次 Coze 综合拼装（2026-11-18，D4）。

职责
====
第一次 Coze 判断「答不了」并产出 plan → 本地 plan_runner 执行完 → 本模块把
结构化结果作为 tool_results 再发一次 ct-advisor Coze 端点，云端「带结果重入」
节点跳过判定直接综合出最终答案。

🔴 出域约束（F33）：
  tool_results 只含结构化摘要（{skill,status,expect,summary,error}），禁止
  原始产物 / doc_context / 附件 / 方案 / 受试者数据。发起前做 forbidden 字段扫描。

🔴 失败语义：
  二次 Coze 不通 / 未授权 → 与首次调用同一套硬失败通道（无本地拼装兜底），
  由 orchestrate 的 build_output 渲染错误提示，绝不返回未经精校的占位内容。

用法
====
    python adapters/plan_assemble_cloud.py --self-test   # 离线自测，不触网
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
for _p in (str(SCRIPT_DIR), str(SKILL_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

CONTRACT_PATH = SKILL_ROOT / "config" / "plan_contract.json"


def load_contract() -> dict:
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 出域安全：结构化摘要 + forbidden 扫描 ───────────────────────────────────

def build_tool_results(original_question: str, first_draft: str,
                       plan_results: List[dict], cfg: Optional[dict] = None) -> dict:
    """构造 tool_results 信封，只保留契约允许的字段（出域最小化）。

    任何 forbidden 字段出现在摘要中即整条丢弃其值（改填占位），绝不外发。
    """
    spec = cfg or load_contract()
    allowed_fields = set(spec["assemble"]["plan_result_fields"])
    forbidden = set(spec["assemble"]["forbidden_fields"])
    clean_results = []
    for r in (plan_results or []):
        if not isinstance(r, dict):
            continue
        item = {}
        for k in allowed_fields:
            if k not in r:
                continue
            v = r[k]
            if k in forbidden:
                continue
            if isinstance(v, str):
                v = v[:4000]
            item[k] = v
        # summary 是 dict：递归剔除 forbidden 键
        if isinstance(item.get("summary"), dict):
            item["summary"] = _strip_forbidden(item["summary"], forbidden)
        clean_results.append(item)
    return {
        "original_question": str(original_question or "")[:2000],
        "first_draft_answer": str(first_draft or "")[:8000],
        "plan_results": clean_results,
    }


def _strip_forbidden(obj: Any, forbidden: set, depth: int = 0) -> Any:
    """递归剔除 dict 中的 forbidden 键（大小写不敏感、含子串匹配）。"""
    if depth > 6:
        return "[truncated]"
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            kl = str(k).lower()
            if any(f.lower() in kl for f in forbidden):
                continue
            out[k] = _strip_forbidden(v, forbidden, depth + 1)
        return out
    if isinstance(obj, list):
        return [_strip_forbidden(x, forbidden, depth + 1) for x in obj[:50]]
    if isinstance(obj, str):
        return obj[:4000]
    return obj


def assert_no_forbidden(tool_results: dict, cfg: Optional[dict] = None) -> bool:
    """出站前断言：tool_results 序列化后不含任何 forbidden 键名。"""
    spec = cfg or load_contract()
    forbidden = set(spec["assemble"]["forbidden_fields"])
    blob = json.dumps(tool_results, ensure_ascii=False).lower()
    return not any(f.lower() in blob for f in forbidden)


# ── 二次 Coze 调用 ──────────────────────────────────────────────────────────

def assemble(req, config_path: str, plan_results: List[dict]) -> Any:
    """二次调用 ct-advisor Coze 端点，返回 RefineResult（或抛异常由调用方硬失败）。

    req 为首次调用的 RefineRequest（含 query_meta / original_question / locale 等）。
    本函数构造一个**新的** RefineRequest：保留原问题与 query_meta，draft_answer 置
    首次草稿，tool_results 挂结构化摘要；复用 build_refiner.refine_forward 发请求。
    """
    from adapters import RefineRequest  # 延迟导入，避免自测期加载重模块
    spec = load_contract()

    tool_results = build_tool_results(
        req.original_question, req.draft_answer, plan_results, spec)
    if not assert_no_forbidden(tool_results, spec):
        raise ValueError("tool_results 含 forbidden 字段，拒绝出域")

    second = RefineRequest(
        query_meta=dict(req.query_meta or {}),
        original_question=req.original_question,
        draft_answer=req.draft_answer,
        doc_context="",            # 🔴 F33：二次调用禁带原始文档
        scope_hint="",
        conversation_history=list(getattr(req, "conversation_history", []) or []),
        is_followup=getattr(req, "is_followup", False),
        tool_results=tool_results,
    )
    second.normalize()
    from adapters import build_refiner
    return build_refiner(config_path=config_path).refine_forward(second)


# ── 离线自测 ────────────────────────────────────────────────────────────────

def self_test() -> int:
    cfg = load_contract()
    ok = True

    def chk(label: str, cond: bool) -> None:
        nonlocal ok
        print("  [%s] %s" % ("PASS" if cond else "FAIL", label))
        ok = ok and cond

    print("plan_assemble_cloud 离线自测（不触网）")
    print("-" * 62)
    results = [
        {"skill": "ct-registry", "status": "ok", "expect": "registry_landscape",
         "summary": {"total_hits": 12, "phase_counts": {"II": 5}}, "error": ""},
        {"skill": "ct-safety", "status": "error", "expect": "safety_signal",
         "summary": {}, "error": "BRIEF_FAILED"},
    ]
    tr = build_tool_results("某药格局和信号？", "草稿", results, cfg)
    chk("原问题透传", tr["original_question"] == "某药格局和信号？")
    chk("首次草稿透传", tr["first_draft_answer"] == "草稿")
    chk("结果数一致", len(tr["plan_results"]) == 2)
    chk("ok 步骤 summary 保留", tr["plan_results"][0]["summary"]["total_hits"] == 12)
    chk("error 步骤 error 保留", "BRIEF_FAILED" in tr["plan_results"][1]["error"])
    chk("无 forbidden 字段", assert_no_forbidden(tr, cfg))

    # forbidden 注入被剔除
    dirty = [{"skill": "ct-registry", "status": "ok", "expect": "registry_landscape",
              "summary": {"total_hits": 3, "doc_context": "SECRET", "protocol": "SECRET"},
              "error": ""}]
    tr2 = build_tool_results("q", "d", dirty, cfg)
    chk("doc_context 被剔除", "doc_context" not in json.dumps(tr2, ensure_ascii=False))
    chk("protocol 被剔除", "protocol" not in json.dumps(tr2, ensure_ascii=False))
    chk("注入后仍无 forbidden", assert_no_forbidden(tr2, cfg))

    # 非白名单字段被过滤
    extra = [{"skill": "ct-samplesize", "status": "ok", "expect": "samplesize_number",
              "summary": {"n": 100}, "error": "", "raw_artifact": "BIG"}]
    tr3 = build_tool_results("q", "d", extra, cfg)
    chk("未知字段 raw_artifact 被过滤",
        "raw_artifact" not in json.dumps(tr3, ensure_ascii=False))
    print("-" * 62)
    print("结论：%s" % ("✅ 全部通过" if ok else "❌ 存在 FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Plan 二次 Coze 拼装器")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    print("用法：python adapters/plan_assemble_cloud.py --self-test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
