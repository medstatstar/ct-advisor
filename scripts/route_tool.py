#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ct-advisor — 入口代码级 ct 技能预判（确定性，无 LLM）

设计目标（2026-08-15，模式 B 编排器前置）：
  在问题进入时（route.py 判定难度之后、转发 Coze 之前），用确定性正则
  预判「是否需要调用 ct 系列技能补充信息」，作为 Coze need_tool 判断的
  **前端高置信预取**信号。

  - 高置信才输出 need_tool（命中明确工具触发词 + 非 vague + 非定义/标准操作）。
  - 漏判由 Coze 的 need_tool 判断兜底（本脚本**不替代** Coze，仅预取）。
  - 参数尽力抽取：test 类用 tool_mapping.json 的 test_hints 推断；百分比
    自动转比例；其余留空，由 handle_need_tool.py 补全或 need_params 追问。

  ⚠️ 与 route.py 的分工：route.py 判「难度」（vague 偏多），本脚本判「是否
  需调 ct 技能」（高置信才触发）。两者都确定性、都无 LLM。

用法：
  python scripts/route_tool.py "用户问题原文"
        → 打印一个标签：none | ct-samplesize | ct-registry | ct-safety | ct-literature
  python scripts/route_tool.py --json "用户问题原文"
        → 打印 {"need_tool": "...", "params": {...}, "confidence": "high"}
  python scripts/route_tool.py --self-test
        → 跑内置预判自测，输出每例命中/预期与准确率
"""

import argparse
import json
import re
import sys
from pathlib import Path

# 复用 route.py 的入口信号（同目录 import；route.py 的 main 在 __main__ 守卫内，import 安全）
sys.path.insert(0, str(Path(__file__).resolve().parent))
from route import is_vague, DEF  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _load_mapping() -> dict:
    try:
        return json.loads((ROOT / "scripts" / "tool_mapping.json").read_text(encoding="utf-8"))
    except Exception:
        return {"skills": {}}


# ---------------------------------------------------------------------------
# 工具触发词（从 route.py CPLX + tool_mapping.json 提取，确定性、可单测）
# 探针验证（2026-08-15）：明确查询 6/6 全中；定义题/纯方法论应排除；隐晦需求
# 漏判（由 Coze need_tool 兜底，不强行放宽以免误触发）。
# ---------------------------------------------------------------------------
TOOL_TRIGGERS = {
    "ct-samplesize": re.compile(
        r"样本量|检验效能|power|把握度|样本数|估算|计算|假设检验|n\s*="),
    "ct-registry": re.compile(
        r"在研|临床试验|注册|招募|适应症|试验数量|pipeline|竞品|在研药物|三期|二期|剂量"),
    "ct-safety": re.compile(
        r"faers|安全性信号|不良事件信号|信号检测|disproportionality|\bprr\b|\bror\b|\bebgm\b"),
    "ct-literature": re.compile(
        r"文献|综述|发表|pubmed|引用|文献检索"),
}

# 方法论询问（仅问注意事项/因素/步骤，无明确数值或计算动作）→ 不预判，
# 避免对"样本量计算要注意什么"这类题突兀地追问效应量参数。明确查询（含动作/数值）
# 即使带"这个/文献/vs"也预判——工具触发词盖过代词歧义。
METHOD = re.compile(
    r"要注意|注意什么|注意事项|哪些因素|需要考虑|如何做|怎么做|如何考虑|"
    r"区别|差异|对比|为什么需要|如何保证|怎么看|怎么理解")


def _extract_params(tool: str, q: str) -> dict:
    """尽力抽取执行卡参数；抽不到的留空（handle_need_tool 补全/追问）。"""
    params: dict = {}
    mapping = _load_mapping()
    cfg = mapping.get("skills", {}).get(tool, {})

    if tool == "ct-samplesize":
        # test 类：复用 tool_mapping 的 test_hints（单一数据源，避免漂移）
        hints = cfg.get("test_hints", {})
        for pattern, value in hints.items():
            if any(kw in q for kw in pattern.split("|")):
                params["test"] = value
                break
        # 百分比 → 比例：ORR 30% vs 45% → p1=0.3, p2=0.45
        m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:vs|对|比|～|~)\s*(\d+(?:\.\d+)?)\s*%", q, re.I)
        if m:
            try:
                params["p1"] = round(float(m.group(1)) / 100, 4)
                params["p2"] = round(float(m.group(2)) / 100, 4)
            except ValueError:
                pass
    elif tool == "ct-registry":
        # 抽取检索主词 cond（覆盖 药/抑制剂/单抗/药物/化合物/制剂/类 等形态）。
        # 取 drug 后缀前紧邻的实体、并裁剪前导动词（检索/查/针对…），避免把动词当检索词。
        # ⚠️ 键必须是 tool_mapping.json 的 required_params 值「cond」（非 drug）：
        #   抽成 drug 会与 required_params 对不上 → handle_need_tool 仍判 need_params，
        #   前端预判对 registry 形同虚设（已踩过 REKEY 坑，详见 v0.9.68 修复记录）。
        SUFFIX = r"(?:抑制剂|单抗|药物|药|化合物|制剂|类)"
        m = re.search(SUFFIX, q)
        if m:
            pre = q[: m.start()].strip()
            runs = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+(?:[-][\u4e00-\u9fa5A-Za-z0-9]+)*", pre)
            BLACK = {"检索", "查询", "查", "看", "关于", "针对", "治疗", "了解",
                     "找", "这个", "该", "那", "适应症", "在研", "试验", "有", "哪些"}
            ent = ""
            for r in reversed(runs):
                if r not in BLACK:
                    ent = r
                    break
            if ent:
                params["cond"] = ent + m.group(0)
    # ct-safety / ct-literature：drug / topic 多需语义抽取，留空（need_params 追问）
    return params


def predict(q: str) -> dict:
    """返回 {'need_tool': str|None, 'params': dict, 'confidence': 'high'|None}。

    高置信约束：命中工具触发词 AND 非「纯代词无工具意图」AND 非纯定义 AND 非方法论询问。
    工具触发词是强信号，命中时盖过代词歧义（如"这个适应症在研药物"仍预判 registry）。
    多工具场景取首个命中（其余由 Coze need_tool 兜底补）。
    """
    q = (q or "").strip()
    if not q:
        return {"need_tool": None, "params": {}, "confidence": None}
    # 工具触发词是强信号：命中时不因代词歧义排除（意图明确）
    has_tool = any(rx.search(q.lower()) for rx in TOOL_TRIGGERS.values())
    # 纯代词短句且无工具意图 → 不预判（交给 vague 流程或 Coze）
    if is_vague(q) and not has_tool:
        return {"need_tool": None, "params": {}, "confidence": None}
    # 纯定义 → 不预判（避免"什么是样本量"误触发 samplesize）
    if DEF.search(q):
        return {"need_tool": None, "params": {}, "confidence": None}
    # 方法论询问（无明确数值/动作）→ 不预判（避免对"注意事项"题突兀追问参数）
    if METHOD.search(q):
        return {"need_tool": None, "params": {}, "confidence": None}

    hits = [t for t, rx in TOOL_TRIGGERS.items() if rx.search(q.lower())]
    if not hits:
        return {"need_tool": None, "params": {}, "confidence": None}

    tool = hits[0]
    return {"need_tool": tool, "params": _extract_params(tool, q), "confidence": "high"}


def predict_tool(q: str):
    """兼容接口：仅返回 need_tool 字符串或 None（供编排器快速判定）。"""
    return predict(q).get("need_tool")


# ---------------------------------------------------------------------------
# 内置自测
# ---------------------------------------------------------------------------

SELF_TEST = [
    # (问题, 期望 need_tool) — 明确查询应高置信命中；定义/方法论/隐晦需求应 none
    ("算下样本量，ORR 30% vs 45%", "ct-samplesize"),
    ("检索 PD-1 抑制剂三期试验有哪些", "ct-registry"),
    ("computing sample size with power 80%", "ct-samplesize"),
    ("FAERS 里 XX 药心血管信号", "ct-safety"),
    ("查 XX 药的文献", "ct-literature"),
    ("估算检验效能 power 80%", "ct-samplesize"),
    ("这个适应症在研药物有哪几个", "ct-registry"),
    # 定义 / 标准操作 / 方法论 → none（不误触发）
    ("什么是样本量", "none"),
    ("样本量的定义", "none"),
    ("样本量计算要注意什么", "none"),
    ("SAE 上报时限是多少", "none"),
    ("为什么 AE 需要分级", "none"),
    # 隐晦需求 → none（漏判由 Coze need_tool 兜底，不强行放宽）
    ("XX 药在肺癌的疗效如何", "none"),
    ("鼻咽癌目前的治疗手段", "none"),
    ("评估下这个方案的可行性", "none"),
]

# 参数抽取断言（REKEY 防护）：确认前端预判抽到的键与 tool_mapping.required_params 对齐。
# registry 必须抽「cond」（非 drug）；samplesize 必须抽 p1/p2；无真实参数可抽时为空。
PARAM_TEST = [
    ("算下样本量，ORR 30% vs 45%", {"p1": 0.3, "p2": 0.45}),
    ("检索 PD-1 抑制剂三期试验有哪些", {"cond": "PD-1抑制剂"}),
    ("computing sample size with power 80%", {}),  # 仅预设，无真实参数可抽
]


def run_self_test() -> int:
    print("route_tool.py 预判自测")
    print("=" * 56)
    ok = 0
    for q, expect in SELF_TEST:
        got = predict_tool(q) or "none"
        mark = "✓" if got == expect else "✗"
        if got == expect:
            ok += 1
        print(f"  {mark} [{got:<13}] 期望 {expect:<13} | {q}")
    total = len(SELF_TEST)
    print("-" * 56)
    print(f"  工具命中准确率: {ok}/{total} = {ok / total * 100:.1f}%")

    # 参数抽取断言（REKEY 防护）
    print("参数抽取断言（REKEY 防护）")
    print("-" * 56)
    pok = 0
    for q, expect_params in PARAM_TEST:
        got_params = predict(q).get("params") or {}
        okp = all(got_params.get(k) == v for k, v in expect_params.items())
        # 额外防护：registry 绝不能再抽出已废弃的 "drug" 键（会导致与 required_params 失配）
        no_drug = "drug" not in got_params
        if okp and no_drug:
            pok += 1
            pm = "✓"
        else:
            pm = "✗"
        print(f"  {pm} [{got_params}] 期望含 {expect_params} | {q}")
    ptotal = len(PARAM_TEST)
    print("-" * 56)
    print(f"  参数断言准确率: {pok}/{ptotal} = {pok / ptotal * 100:.1f}%")
    return 0 if (ok == total and pok == ptotal) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="ct-advisor deterministic ct-tool predictor (Mode B prefetch)")
    ap.add_argument("question", nargs="?", help="用户问题原文")
    ap.add_argument("--json", action="store_true", help="输出 JSON（含 params / confidence）")
    ap.add_argument("--self-test", action="store_true", help="运行内置预判自测")
    args = ap.parse_args()

    if args.self_test:
        return run_self_test()

    if not args.question:
        ap.print_help()
        return 2

    res = predict(args.question)
    if args.json:
        print(json.dumps(res, ensure_ascii=False))
    else:
        print(res.get("need_tool") or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
