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
from route import is_vague, DEF as DEF_ZH  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _load_mapping() -> dict:
    try:
        return json.loads((ROOT / "scripts" / "tool_mapping.json").read_text(encoding="utf-8"))
    except Exception:
        return {"skills": {}}


# ---------------------------------------------------------------------------
# 工具触发词（从 route.py CPLX + tool_mapping.json 提取，确定性、可单测）
#
# 🔴 2026-09-10（第十四轮，用户要求）：由「宽词表」收紧为「强触发词」——
#   起因：关键词误报导致把方法学 / 定义 / 法规判断题误判为「需取数」并弹参追问。
#   用户口径：**只有需求关联非常明确时才调用**兄弟技能；其余一律「先自身作答 + 末尾建议」。
#
#   分层：
#     TOOL_TRIGGERS（强）：唯一指向 → 命中即高置信自动调用。
#       满足其一即可：① 具名数据源（FAERS / ClinicalTrials.gov / NCT 号 / PubMed…）；
#                     ② 具名统计量或高特异性方法（PRR / ROR / EBGM / 去激发 / 病例报告…）；
#                     ③「检索动词 + 注册试验/文献」完整句式（中英各一条）。
#     WEAK_TRIGGERS（弱）：歧义大（信号 / 文献 / 试验 / 安全性 / 设计…）→ **不再自动调用**，
#       仅在答案末尾追加一行软建议（见 suggest_footer），由用户决定是否真要取数。
#
#   一律受「咨询意图护栏」约束（DEF / METHOD / DOC，见下方）：问「是什么 / 怎么做 / 要模板」
#   且无明确取数动作（RETRIEVAL）时，不作取数请求。
# ---------------------------------------------------------------------------

# 强触发词：具名数据源 / 具名统计量 / 高特异性方法 /「检索动词 + 明确对象」句式
TOOL_TRIGGERS = {
    "ct-samplesize": re.compile(
        r"样本量|检验效能|把握度|样本数|估算样本|需要多少例|需要多少受试者|需要多少患者|"
        r"sample size|sample-size|how many (?:subjects|patients|participants)|\bpower\b"),
    "ct-registry": re.compile(
        # ① 具名注册库 / 登记号（词边界由正则自带，避免 nct 命中 distinct 之类）
        r"\bnct\s*\d|clinicaltrials\.gov|\bchictr\b|chinadrugtrials|药物临床试验登记|"
        # ② 高特异性检索对象（2026-09-10：裸「在研」改「在研(?!究)」防命中「在研|究者手册」）
        r"在研(?!究)(?:药物|试验|项目|管线|产品)|试验数量|pipeline|competitive[- ]intel|landscape|"
        r"registered trials?|"
        # ③ 「检索动词 + 注册/临床试验」完整句式（中文）
        r"(?:检索|查询|查找|搜索|列出|统计|整理|拉一下|查一下|搜一下|找一下|帮我查|帮我找|给我查|"
        r"看看|查|拉|搜|找)[^。；;，,]{0,18}?"
        r"(?:注册试验|登记试验|临床试验|试验注册|试验登记|注册临床试验|注册库|登记库|三期|二期)|"
        # ③′ 英文同型句式
        r"(?:find|search|list|retrieve|pull|fetch|give me|show me|how many|get)\b[^.;]{0,40}?"
        r"(?:registered trials?|clinical trials?|trials?\b|landscape|pipeline|competitive[- ]intel)"),
    "ct-safety": re.compile(
        # 具名数据源 / 统计量 / 高特异性方法（因果判定、去激发再激发、具体 irAE）
        r"faers|disproportionality|\bprr\b|\bror\b|\bebgm\b|"
        r"去激发|再激发|dechallenge|rechallenge|因果关系判定|相关性评价|"
        r"不良反应因果关系|ae因果关系|免疫相关不良事件|\birae\b|"
        r"带状疱疹|vzv|水痘-带状疱疹|herpes zoster|"
        r"间质性肺炎|免疫性肺炎|心肌炎|免疫性肝炎|甲状腺炎|垂体炎|免疫性肾炎|"
        r"pneumonitis|myocarditis|nephritis|thyroiditis|hypophysitis|causality assessment"),
    "ct-literature": re.compile(
        # 具名文献源 / 高特异性研究类型 / 「检索动词 + 文献」句式
        r"pubmed|openalex|\bmeta\s*[- ]?分析|meta[- ]analysis|系统综述|系统评价|"
        r"systematic[- ]reviews?|病例报告|个案报告|case reports?|evidence summary|证据摘要|"
        r"已发表文献|published literature|"
        r"(?:检索|查询|查找|搜索|列出|查|搜|找)[^。；;]{0,12}?(?:文献|论文|综述|证据)|"
        r"(?:find|search|list|retrieve|pull|fetch)\b[^.;]{0,24}?"
        r"(?:literature|papers?|publications?|reviews?)"),
}

# 弱触发词（2026-09-10 新增）：歧义大，**不自动调用**，仅作答案末尾的软建议。
# 出现「信号 / 文献 / 试验 / 安全性 / 设计」这类泛词时，先由本技能自身作答，
# 再提示「如需真实数据可安装 / 调用 ct-XXX」——把「要不要取数」的决定权交还用户。
WEAK_TRIGGERS = {
    "ct-registry": re.compile(
        r"临床试验|注册试验|登记试验|注册库|登记库|在研(?!究)|适应症|招募|试验数量|竞品|管线|"
        r"三期|二期|\btrials?\b|\bregistry\b|landscape|pipeline"),
    "ct-safety": re.compile(
        r"不良事件|信号|安全性|药物警戒|pharmacovigilance|safety signal|adverse events?|\bsafety\b"),
    "ct-literature": re.compile(
        r"文献|论文|综述|发表|\bliterature\b|published|systematic review|evidence"),
    "ct-samplesize": re.compile(
        r"样本|效能|把握度|\bpower\b|sample|effect size"),
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
    r"\btrials?\b|landscape|competitive.?intel|在研(?!究)|注册|登记|试验数量|pipeline")

# 方法论询问（仅问注意事项/因素/步骤，无明确数值或计算动作）→ 不预判，
# 避免对"样本量计算要注意什么"这类题突兀地追问效应量参数。明确查询（含动作/数值）
# 即使带"这个/文献/vs"也预判——工具触发词盖过代词歧义。
#
# 🔴 2026-09-10（第十四轮）：补齐**英文**等价词（此前只有中文 → 英文方法学问句直接穿透，
#   实测「…how do I keep the overall type I error rate at 0.05?」被裸词 "trial" 判成检索注册试验）。
#   与云端 `tool_router_node._consultation_intent` 保持同义（两处需同步改）。
METHOD = re.compile(
    r"要注意|注意什么|注意事项|哪些因素|需要考虑|如何做|怎么做|如何考虑|如何评估|如何判断|"
    r"如何保证|怎么看|怎么理解|有什么区别|有何区别|区别是什么|"
    r"\bhow (?:do|does|should|can|to|would)\b|\bwhat should i\b|\bwhich factors\b|"
    r"\bconsiderations?\b|\bdifference between\b|\bwhat(?:'s| is) the difference\b|\bbest practice\b")

# 定义意图（中文复用语 route.DEF；英文补等价词）→ 纯「是什么」不取数。
DEF = re.compile(
    DEF_ZH.pattern + r"|"
    r"\bwhat(?:'s| is| are)\b|\bdefine\b|\bdefinition\b|\bmeaning\b|\bstands? for\b|\babbreviation\b")

# 文档类请求（模板/规范/格式/小结/一览表等）→ 不预判任何工具。
# 2026-08-15 修复：裸词"临床试验/注册"命中《临床试验项目分中心小结》模板类问题，
# 被误判为 ct-registry 检索（输出 "撰写一份完整的药物" 污染）。文档类请求本就不该触发
# 数据检索/计算类工具，统一拦截；真实检索意图（在研/三期/招募等）仍正常预判。
DOC = re.compile(
    r"模板|撰写规范|格式|小结|总结报告|填写|一览表|doc\s*文件|提取的文本|审批表|签章|存档|"
    r"\btemplate\b|\bformat\b|\bchecklist\b|\bwrite (?:a|the|up)\b|\bdraft (?:a|the)\b|\bfill (?:in|out)\b")

# 明确取数动作（2026-09-10）：命中 → 咨询意图护栏让位（用户是在「要数据」而非「问怎么做」）。
# 与云端 `_RETRIEVAL_INTENT` 同义。
RETRIEVAL = re.compile(
    r"检索|搜索|查找|查询|列出|统计|拉一下|查一下|搜一下|找一下|列一下|帮我查|帮我找|给我查|"
    r"有哪些|哪几个|数量|多少家|"
    r"\bfind\b|\bsearch\b|\blist\b|\bretrieve\b|\bpull\b|\bfetch\b|\bgive me\b|\bshow me\b|"
    r"\bhow many\b|\bget (?:the|me)\b")


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


def _none(suggest=None) -> dict:
    """统一的「不调用」返回（可携带软建议）。"""
    return {"need_tool": None, "need_tools": [], "suggest_tools": list(suggest or []),
            "params": {}, "confidence": None}


def predict(q: str) -> dict:
    """返回 {'need_tool', 'need_tools', 'suggest_tools', 'params', 'confidence'}。

    🔴 2026-09-10（第十四轮，用户要求）三层语义：
      - need_tool 非空   → **强命中**（唯一指向）→ 自动调用该技能取真实数据；
      - need_tool 空 + suggest_tools 非空 → **弱命中 / 咨询意图** → 不调用，先自身作答，
        答案末尾追加一行软建议（suggest_footer），把「要不要取数 / 安装」交回用户；
      - 两者皆空         → 与兄弟技能无关，直接自身作答。

    高置信约束（保留）：强命中 AND 非纯代词短句 AND 非纯定义 / 方法论 / 文档类询问
    （咨询意图护栏，且无明确取数动作）。
    """
    q = (q or "").strip()
    if not q:
        return _none()
    ql = q.lower()
    strong = [t for t, rx in TOOL_TRIGGERS.items() if rx.search(ql)]
    weak = [t for t, rx in WEAK_TRIGGERS.items() if rx.search(ql)]

    # 咨询意图护栏：问「是什么 / 怎么做 / 要模板」且**无明确取数动作** → 不作取数请求。
    # 明确取数动作（RETRIEVAL，如「检索…」「帮我查…」「how many …」）时护栏让位。
    # ⚠️ 必须用**小写** ql 判定：英文护栏词区分大小写，句首 "How do I…" 否则不命中。
    if (DEF.search(ql) or METHOD.search(ql) or DOC.search(ql)) and not RETRIEVAL.search(ql):
        # 🔴 2026-09-10（第十四轮·补丁，用户要求）：护栏命中时**只保留强命中**作为建议，
        #   不再回落弱词表。否则裸弱词（ct-registry 的 `\btrials?\b`）会给纯定义 / 方法论题
        #   附一条题不对路的「可调用 ct-registry」提示——即已消灭的误报换了位置继续出现。
        #   实测回归：「A confirmatory Phase III trial plans one interim analysis — how do I
        #   keep the overall type I error rate at 0.05?」「…ITT and mITT…trial?」此前均建议
        #   ct-registry，现应为 []。与云端 `_suggest_tools(..., strong_only=True)` 同义。
        return _none(strong)

    # 纯代词短句且无强命中 → 不预判（交给 vague 流程或 Coze）；弱命中保留为软建议
    if is_vague(q) and not strong:
        return _none(weak)

    if strong:
        # 2026-08-21：need_tools 保留**全部**强命中（LIT_FIRST 只调整主判顺序、不删候选）
        raw_hits = list(strong)
        hits = list(strong)
        # 2026-08-20：文献检索意图优先于 FAERS 信号统计（README 示例 7 修复）；
        # 2026-08-21：加 REG_INTENT 排除——同时含明确试验格局意图时维持字典序（registry 在前）。
        if ("ct-literature" in hits and "ct-safety" in hits
                and LIT_FIRST.search(q) and not REG_INTENT.search(q)):
            hits = [t for t in hits if t != "ct-safety"]
            hits.insert(0, "ct-literature")
        tool = hits[0]
        return {"need_tool": tool, "need_tools": raw_hits, "suggest_tools": [],
                "params": _extract_params(tool, q), "confidence": "high"}

    # 弱命中 → 不调用；答案末尾软建议
    return _none(weak)


def predict_tool(q: str):
    """兼容接口：仅返回 need_tool 字符串或 None（供编排器快速判定）。"""
    return predict(q).get("need_tool")


# ---------------------------------------------------------------------------
# 软建议页脚（2026-09-10 第十四轮，用户要求）
#
# 姿态：**先自身作答，末尾再建议**。当问题与兄弟技能沾边、但「需求关联不够明确」
# （弱命中）或属咨询意图（定义 / 方法论 / 文档）时，不再阻断答案去要参数或要安装，
# 而是在答案**最后**追加一行建议，把「是否安装 / 是否调用」交给用户决定。
#
# 文案随提问语言切换；工具名保持 id 原文。供 orchestrate.build_output /
# refine_answer --ship 复用（单一数据源，避免两处文案漂移）。
# ---------------------------------------------------------------------------
_TOOL_DESC = {
    "ct-registry": {"zh": "试验注册库检索（试验格局 / 分期 / 申办方 / 时间线）",
                    "en": "trial-registry search (landscape / phase / sponsor / timeline)"},
    "ct-safety": {"zh": "FAERS 药物警戒信号（PRR / ROR / EBGM + 95%CI）",
                  "en": "FAERS pharmacovigilance signals (PRR / ROR / EBGM + 95% CI)"},
    "ct-literature": {"zh": "学术文献检索（含临床指南 / 病例报告 / 综述 / 证据摘要）",
                      "en": "literature search (guidelines / case reports / reviews / evidence)"},
    "ct-samplesize": {"zh": "样本量 / 检验效能计算",
                      "en": "sample size / power calculation"},
}


def suggest_footer(tools, lang: str = "zh-CN") -> str:
    """构造答案末尾的兄弟技能软建议（无匹配则返回空串）。

    🔴 只建议、不阻断：本函数产出的文本追加在**答案之后**，不改变答案本身，
    也不要求用户先补参数 / 先安装。用户想取数时再显式发起。
    """
    tools = [t for t in (tools or []) if t in _TOOL_DESC]
    if not tools:
        return ""
    if lang == "zh-CN":
        items = "\n".join(f"- `{t}`：{_TOOL_DESC[t]['zh']}" for t in tools)
        return ("\n\n---\n\n💡 *补充：本问题还涉及以下兄弟技能。以上已按本技能自身能力作答；"
                "如需**真实数据或更深入的分析**，可安装 / 调用后再补充：*\n" + items)
    items = "\n".join(f"- `{t}`: {_TOOL_DESC[t]['en']}" for t in tools)
    return ("\n\n---\n\n💡 *Note: this question also touches the following sibling skills. "
            "The answer above is from this skill's own capability; install / invoke them "
            "if you'd like **real data or a deeper analysis**:*\n" + items)


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
    # 2026-09-10：英文方法学问句含 "trial" 不得误判为 registry（README 示例 1 EN 实测回归）
    ("A confirmatory Phase III trial plans one interim analysis — how do I keep the overall type I error rate at 0.05?", "none"),
    ("How do I design a Phase III clinical trial?", "none"),
    # 2026-09-10（第十二轮续）：中文短词「在研」不得命中「在研|究者」——
    # README 新增实操例（GCP 受试者补偿 / PV 预期性判断）实测误判回归。
    ("方案规定完成全部访视的受试者可获得 5000 元交通补贴。某受试者因 SAE 提前退出，研究者是否应支付全额补偿？GCP 对此有何要求？", "none"),
    ("某不良反应在研究者手册（IB）中列为“少见”，但实际发生率在试验中达到 15%。PV 应如何评估是否需要更新 IB 和标签？", "none"),
    ("研究者发起的临床试验（IIT）与药企申办试验在监管上有何区别？", "none"),
    # 隐晦需求 → none（漏判由 Coze need_tool 兜底，不强行放宽）
    ("XX 药在肺癌的疗效如何", "none"),
    ("鼻咽癌目前的治疗手段", "none"),
    ("评估下这个方案的可行性", "none"),
    # 🔴 2026-09-10（第十四轮·关键词收紧）：以下为「泛词不再自动触发」回归——
    #   这些问句含「信号 / 文献 / 试验 / 设计 / 安全性」等弱词，但需求关联不明确，
    #   一律不自动调用（need_tool=None），仅由 suggest_footer 在答案末尾软建议。
    ("查 XX 药的安全性信号有哪些", "none"),                       # 弱词「安全性信号」→ 不触发
    ("帮我设计一个三期临床试验方案，要注意什么", "none"),             # 弱词「三期/临床试验」+ 方法论
    ("纸质 CRF 迁移到 EDC 要注意什么数据完整性？", "none"),          # 方法论（F1 流程）
    ("帮我找 XX 药治疗肺癌的最新文献", "ct-literature"),             # 「找…文献」句式 → 仍强命中
    ("How should I handle missing data when the endpoint cannot be interpreted?", "none"),
    ("What is the difference between a screening failure and a withdrawal?", "none"),
    ("我们的药物管线里有哪些在研项目", "ct-registry"),               # 高特异性「在研项目」
]

# 软建议断言（2026-09-10 第十四轮）：need_tool 必须为 None，且 suggest_tools 应包含预期技能
# （或 None 表示「不应给出建议」）。用于锁住「先自身作答 + 末尾建议」的新姿态。
SUGGEST_TEST = [
    # (问题, 期望 suggest_tools 至少包含 [tool...]，None/[] = 不应建议)
    ("样本量计算要注意什么", ["ct-samplesize"]),        # 咨询意图 + 强词 → 不调用，但建议
    ("什么是 FAERS 信号", ["ct-safety"]),              # 定义题 + 具名数据源 → 不调用，但建议
    ("查 XX 药的安全性信号有哪些", ["ct-safety"]),      # 弱命中 → 仅建议
    ("纸质 CRF 迁移到 EDC 要注意什么数据完整性？", []),  # 与兄弟技能无关 → 不建议
    ("某不良反应在研究者手册（IB）中列为“少见”，但实际发生率在试验中达到 15%。"
     "PV 应如何评估是否需要更新 IB 和标签？", []),        # PV 实操题 → 不建议（回归）
    ("为什么 AE 需要分级", []),                        # 与兄弟技能无关 → 不调用也不建议
    # —— 2026-09-10 修补（用户要求）：咨询护栏命中时**只建议强命中**，裸弱词不再溢出建议 ——
    #   回归来源：以下英文方法学 / 定义题此前均建议 ct-registry（裸词 `trials?`），题不对路。
    ("A confirmatory Phase III trial plans one interim analysis — "
     "how do I keep the overall type I error rate at 0.05?", []),
    ("What is the difference between ITT and mITT in a confirmatory trial?", []),
    ("How do I design a Phase III clinical trial?", []),
    ("样本量的定义", ["ct-samplesize"]),                # 护栏 + 强词 → 建议保留
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

    # 软建议断言（2026-09-10 第十四轮）：不调用时是否给出恰当建议
    print("软建议断言（先自身作答 + 末尾建议）")
    print("-" * 56)
    sok = 0
    for q, expect in SUGGEST_TEST:
        res = predict(q)
        got = res.get("suggest_tools") or []
        # 期望非空 ⇒ 需包含；期望为空 ⇒ 结果必须为空（否则「不建议」断言形同虚设）
        ok_s = ((res.get("need_tool") is None)
                and all(e in got for e in expect)
                and (bool(expect) or not got))
        if ok_s:
            sok += 1
            sm = "✓"
        else:
            sm = "✗"
        print(f"  {sm} need={res.get('need_tool')} suggest={got} 期望含 {expect} | {q[:40]}")
    stotal = len(SUGGEST_TEST)
    print("-" * 56)
    print(f"  软建议准确率: {sok}/{stotal} = {sok / stotal * 100:.1f}%")

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
    return 0 if (ok == total and sok == stotal and pok == ptotal) else 1


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
