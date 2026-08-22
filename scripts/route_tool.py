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
        r"样本量|检验效能|power|把握度|样本数|估算|计算|假设检验|n\s*=|"
        r"sample size|sample-size"),  # 2026-08-21：补英文别名（README 示例 4/8 实测漏判根因）
    "ct-registry": re.compile(
        r"在研|临床试验注册|临床试验登记|临床试验信息|临床试验数据|临床试验进展|"
        r"注册临床试验|在研临床试验|注册试验|登记试验|试验注册|试验登记|"
        r"招募|适应症|试验数量|pipeline|竞品|在研药物|三期|二期|剂量|"
        r"registered trial|trial registration|clinical trial registry|register(?:d)?\s+trial|"
        r"clinical trials?|competitive.?intel|landscape|oncology trial|\btrials?\b"),
        # 2026-08-21：补英文别名（README 示例 3/4/8 实测漏判根因；裸 trials 靠 METHOD/DEF 过滤兜底）
    "ct-safety": re.compile(
        r"faers|安全性信号|不良事件信号|信号检测|disproportionality|\bprr\b|\bror\b|\bebgm\b|"
        r"safety signals?|pharmacovigilance|adverse event signals?"),  # 2026-08-21：英文别名（示例 3/7）
    "ct-literature": re.compile(
        r"文献|综述|发表|pubmed|引用|文献检索|病例报告|个案报告|已发表|系统综述|meta\s*分析|证据摘要|药物警戒|"
        r"\bliterature\b|published|systematic[- ]reviews?|case reports?|evidence summary"),  # 2026-08-21：英文别名（示例 3/8）
}

# 文献检索意图优先规则（2026-08-20）：当 ct-literature 与 ct-safety 同时命中时，
# 若问题含强文献检索意图词（已发表/病例报告/综述/检索…），优先文献（定性证据）
# 而非 FAERS 信号统计——README 示例 7 场景（QA 要「检索已发表文献评估支持度」）。
LIT_FIRST = re.compile(
    r"检索|搜索|查找|已发表|病例报告|个案报告|综述|系统综述|meta\s*分析|证据摘要|引用|"
    r"search|published|case reports?|systematic reviews?|\bliterature\b")  # 2026-08-21：英文等价词

# 试验格局意图（registry 主导，2026-08-21）：出现时文献优先规则让位、按字典序（registry 在前）
# 预判——避免英文示例 3（trials+safety+literature 竞品情报）被文献意图抢走 registry 主判。
REG_INTENT = re.compile(
    r"\btrials?\b|landscape|competitive.?intel|在研|注册|登记|试验数量|pipeline")

# 方法论询问（仅问注意事项/因素/步骤，无明确数值或计算动作）→ 不预判，
# 避免对"样本量计算要注意什么"这类题突兀地追问效应量参数。明确查询（含动作/数值）
# 即使带"这个/文献/vs"也预判——工具触发词盖过代词歧义。
METHOD = re.compile(
    r"要注意|注意什么|注意事项|哪些因素|需要考虑|如何做|怎么做|如何考虑|"
    r"区别|差异|对比|为什么需要|如何保证|怎么看|怎么理解")

# 文档类请求（模板/规范/格式/小结/一览表等）→ 不预判任何工具。
# 2026-08-15 修复：裸词"临床试验/注册"命中《临床试验项目分中心小结》模板类问题，
# 被误判为 ct-registry 检索（输出 "撰写一份完整的药物" 污染）。文档类请求本就不该触发
# 数据检索/计算类工具，统一拦截；真实检索意图（在研/三期/招募等）仍正常预判。
DOC = re.compile(
    r"模板|撰写规范|撰写|格式|小结|总结报告|填写|一览表|doc\s*文件|提取的文本|审批表|签章|存档")


# 英文抽取停用词（避免把「registered trials for…」这类结构词当实体）
_EN_STOP = {
    "the", "a", "an", "our", "one", "registered", "trials", "trial",
    "case", "reports", "report", "published", "literature", "safety",
    "signal", "signals", "full", "picture", "help", "introduction",
}


def _extract_english_entity(q: str) -> str:
    """尽力抽取英文药名/靶点实体（route_tool 预取参数兜底）。

    2026-08-21：README 示例 2/3/7/8 实测——英文提示词在中文 SUFFIX 逻辑下抽不到
    cond/topic/drug，预取退化 need_params（只给检索指引、不出格局）。此处补英文
    抽取：已知靶点 > 「for X」> 「X in/of/with Y」。仅英文问题生效（CJK 占比守卫），
    中文问题不受影响。抽不到返回空串（由 handle_need_tool 追问）。
    """
    q = q or ""
    if len(re.findall(r"[\u4e00-\u9fff]", q)) >= max(1, len(q) * 0.15):
        return ""  # 中文主导，跳过英文抽取
    # 1) 已知靶点/药物形态（PD-1、GLP-1 RA 等）
    KNOWN = re.compile(
        r"\b(PD-1|PD-L1|CTLA-4|GLP-1(?:\s*RA)?|HER2|EGFR|ALK|ROS1|BRCA1|BRCA2|VEGF|CD20)\b",
        re.I)
    m = KNOWN.search(q)
    if m:
        return m.group(1).upper()
    # 2) 「for X」捕获（Pull the registered trials for semaglutide → semaglutide；
    #    介词/逗号/结尾处截断，避免吞入后续词）
    m = re.search(
        r"\bfor\s+((?:[A-Za-z][A-Za-z0-9\-]*\s+){0,2}[A-Za-z][A-Za-z0-9\-]*)"
        r"(?=\s+(?:in|among|of|with)\b|\s*[,.;]|$)", q)
    if m:
        cand = re.sub(r"^(?:the|a|an)\s+", "", m.group(1).strip(), flags=re.I)
        if cand and cand.lower() not in _EN_STOP:
            return cand
    # 3) 「X in/among/of/with Y」捕获（semaglutide in T2D → semaglutide）
    m = re.search(
        r"\b([A-Za-z][A-Za-z0-9\-]*(?:\s+[A-Za-z][A-Za-z0-9\-]+){0,2})\s+(?:in|among|of|with)\s+",
        q)
    if m:
        cand = re.sub(r"^(?:the|a|an)\s+", "", m.group(1).strip(), flags=re.I)
        if cand and cand.lower() not in _EN_STOP:
            return cand
    return ""


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
        SUFFIX = r"(?:抑制剂|单抗|药物|药|化合物|制剂|类|肽|抗体)"
        m = re.search(SUFFIX, q)
        if m:
            pre = q[: m.start()].strip()
            # 2026-08-20：剥离前导口语动词/请求短语（拉一下/帮我查…），
            # 避免连续中文合成一个 run 时把"拉一下"当 cond 的一部分。
            LEAD = re.compile(
                r"^(?:请|麻烦)?(?:(?:帮我|给我|帮|拉一下|查一下|搜一下|找一下|看一下|"
                r"检索|查询|查|看|拉|搜|找|了解|关于|针对|整理|列一下|列出|给我列)\s*)+")
            pre = LEAD.sub("", pre)
            runs = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+(?:[-][\u4e00-\u9fa5A-Za-z0-9]+)*", pre)
            BLACK = {"检索", "查询", "查", "看", "关于", "针对", "治疗", "了解",
                     "找", "这个", "该", "那", "适应症", "在研", "试验", "有", "哪些",
                     "撰写", "完整", "一份", "请", "根据", "以下", "模板",
                     "提取", "文本", "内容", "doc", "文件"}
            ent = ""
            for r in reversed(runs):
                if r not in BLACK:
                    ent = r
                    break
            if ent:
                params["cond"] = ent + m.group(0)
        if not params.get("cond"):
            # 2026-08-21：英文药名/靶点兜底（README 示例 2/3 实测根因：
            # 英文问题无中文 SUFFIX → m=None 整块跳过；此处独立于 if m 块执行）
            en = _extract_english_entity(q)
            if en:
                params["cond"] = en
    elif tool == "ct-literature":
        # 2026-08-21：英文 topic 尽力抽取（示例 3/8）；中文仍留空由 need_params 追问
        en = _extract_english_entity(q)
        if en:
            params["topic"] = en
    elif tool == "ct-safety":
        # 2026-08-21：英文 drug 尽力抽取（示例 7）；中文仍留空由 need_params 追问
        en = _extract_english_entity(q)
        if en:
            params["drug"] = en
    return params


def predict(q: str) -> dict:
    """返回 {'need_tool': str|None, 'need_tools': list, 'params': dict, 'confidence': 'high'|None}。

    高置信约束：命中工具触发词 AND 非「纯代词无工具意图」AND 非纯定义 AND 非方法论询问。
    工具触发词是强信号，命中时盖过代词歧义（如"这个适应症在研药物"仍预判 registry）。
    多工具场景取首个命中（need_tool）为**主判**；其余命中保留在 need_tools，供编排器
    缝合主源后**提示用户分别调用其余工具**（2026-08-21：README 示例 3/7/8 多源场景）。
    """
    q = (q or "").strip()
    if not q:
        return {"need_tool": None, "need_tools": [], "params": {}, "confidence": None}
    # 工具触发词是强信号：命中时不因代词歧义排除（意图明确）
    has_tool = any(rx.search(q.lower()) for rx in TOOL_TRIGGERS.values())
    # 纯代词短句且无工具意图 → 不预判（交给 vague 流程或 Coze）
    if is_vague(q) and not has_tool:
        return {"need_tool": None, "need_tools": [], "params": {}, "confidence": None}
    # 纯定义 → 不预判（避免"什么是样本量"误触发 samplesize）
    if DEF.search(q):
        return {"need_tool": None, "need_tools": [], "params": {}, "confidence": None}
    # 方法论询问（无明确数值/动作）→ 不预判（避免对"注意事项"题突兀追问参数）
    if METHOD.search(q):
        return {"need_tool": None, "need_tools": [], "params": {}, "confidence": None}
    # 文档类请求（模板/规范/格式/小结等）→ 不预判（2026-08-15：防"临床试验"裸词误伤
    # 分中心小结模板类问题；文档类问题本就不需要数据检索/计算工具）
    if DOC.search(q):
        return {"need_tool": None, "need_tools": [], "params": {}, "confidence": None}

    hits = [t for t, rx in TOOL_TRIGGERS.items() if rx.search(q.lower())]
    if not hits:
        return {"need_tool": None, "need_tools": [], "params": {}, "confidence": None}

    # 2026-08-21：need_tools 保留**全部**命中（LIT_FIRST 只调整主判顺序、不删候选，
    # 使 Ex7 缝合 ct-literature 后仍能提示 ct-safety 源）
    raw_hits = list(hits)

    # 2026-08-20：文献检索意图优先于 FAERS 信号统计（README 示例 7 修复）；
    # 2026-08-21：加 REG_INTENT 排除——同时含明确试验格局意图（trials/landscape/在研…）
    # 时维持字典序（registry 在前），避免英文示例 3 的竞品情报题被文献意图抢走 registry 主判。
    if ("ct-literature" in hits and "ct-safety" in hits
            and LIT_FIRST.search(q) and not REG_INTENT.search(q)):
        hits = [t for t in hits if t != "ct-safety"]
        hits.insert(0, "ct-literature")

    tool = hits[0]
    return {"need_tool": tool, "need_tools": raw_hits,
            "params": _extract_params(tool, q), "confidence": "high"}


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
    ("拉一下司美格鲁肽在 2 型糖尿病的注册试验", "ct-registry"),   # 2026-08-20：README 示例 2 ZH
    ("Pull the registered trials for semaglutide in T2D", "ct-registry"),  # 2026-08-20：README 示例 2 EN
    ("computing sample size with power 80%", "ct-samplesize"),
    ("Give me the full competitive-intel picture for GLP-1 RA in obesity — trials, safety signals, and literature", "ct-registry"),  # 2026-08-21：README 示例 3 EN（REG_INTENT 让 registry 主判）
    ("I'm planning a Phase II oncology trial and also need the sample size — help me decide the design", "ct-samplesize"),  # 2026-08-21：README 示例 4 EN
    ("One of our PD-1 products has case reports of interstitial lung disease; QA suspects a new safety signal. Search the published literature (case reports, pharmacovigilance studies, reviews) for how much support this signal has, and give me a citable evidence summary for the signal-evaluation meeting", "ct-literature"),  # 2026-08-21：README 示例 7 EN（LIT_FIRST 文献优先）
    ("We're drafting a phase-3 protocol in this indication. Give me the published RCT + systematic-review evidence from the last 5 years for the introduction, then compute the sample size for a superiority design using the key assumptions I'll provide", "ct-samplesize"),  # 2026-08-21：README 示例 8 EN
    ("FAERS 里 XX 药心血管信号", "ct-safety"),
    ("查 XX 药的文献", "ct-literature"),
    ("我们一款 PD-1 产品有间质性肺炎个案报告，请检索已发表文献（病例报告、药物警戒研究、综述）评估信号支持度", "ct-literature"),  # 2026-08-20：README 示例 7（文献意图优先于 safety）
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
    # 2026-08-21：英文药名/靶点抽取断言（README 示例 2/3/7 修复回归）
    ("Pull the registered trials for semaglutide in type-2 diabetes", {"cond": "semaglutide"}),
    ("Give me the full competitive-intel picture for GLP-1 RA in obesity — trials, safety signals, and literature", {"cond": "GLP-1 RA"}),
    ("One of our PD-1 products has case reports of interstitial lung disease; QA suspects a new safety signal. Search the published literature for how much support this signal has", {"topic": "PD-1"}),
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
