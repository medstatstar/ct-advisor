#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""query_entity — 自然语言问句的实体抽取 / 前导噪声清洗（ct- 系列共用基座件）。

单一真源：``ct-base/scripts/query_entity.py``，经 ``publish_inject.py`` 分发到各
技能 ``scripts/``。提供"从用户自然语言问句抽药物 / 疾病 / 靶点实体 + 剥离噪声"
的确定性能力：

  - ``strip_generated_tail(text)`` : 剥离「初步说明 / 取数结果 / MISSING_REQUIRED」
                                     等生成物尾段，只留用户问题本体（防上下文污染）
  - ``has_cjk(text)``             : 是否含中日韩文字（**复用 kw_localize.detect_lang**，
                                    不再自建同义实现）
  - ``extract_english_entity(q)`` : 英文药名 / 靶点从句抽取（已知靶点 > for X > X in/of/with Y）
  - ``extract_mixed_entities(q)`` : 中英混合问句抽 {condition, disease, target,
                                    drug_cjk, topic}
  - ``extract_registry_params(q)``: ct-registry 的 ``{cond, intr}`` 唯一入口。
                                    调用方直接 return 其结果，禁止再补正则分叉。

设计纪律（继承 ct-base §5 / §16.8 单一真源不变量）：
  - 纯 stdlib / 确定性 / 无 LLM / 无网络，F33 边界安全。
  - 语言检测**只**复用 ``kw_localize.detect_lang``；禁止再写第二份 ``_has_cjk``。
    历史教训：ct-advisor 曾自建 ``_has_cjk``（码点范围更窄），与基座分叉。
  - 技能参数映射（如 ct-registry 的 ``cond``/``intr``）**在本模块给出唯一实现**，
    调用方不得再写第二份。历史教训：cond/intr 曾在 route_tool._extract_params、
    extract_params_for_tools、ct-base 三处各补一层，新增入口就复发一次（2026-11-20 根治）。
  - 药物后缀集合服务于"问句实体抽取"，与 ``keyword_breadth._DRUG_ZH``（服务于
    "关键词宽泛度判定"）用途不同，两者集合可不同、互不替代；此处不重复实现判定逻辑。
  - ``ct-safety`` 的 ``drug`` 绝不填中文：openFDA 只认英文通用名，中文会零命中。
    本模块的 ``drug_cjk`` 仅供"接受中文检索词"的技能（ct-registry 的 intr）使用。

用法：
    from query_entity import (strip_generated_tail, has_cjk, extract_english_entity,
                              extract_mixed_entities, extract_registry_params)
    python query_entity.py --self-test   # 离线自测
"""
from __future__ import annotations

import re

# 语言检测复用 ct-base 共用件（本地优先：分发后各技能 scripts/ 均携带 kw_localize.py；
# 开发态在 ct-base 内直接 import 同目录真源）。禁止在此重建同义实现。
try:
    from kw_localize import detect_lang as _detect_lang
except ImportError:  # pragma: no cover - 仅当脱离 ct-base 且未 vendor 时兜底
    def _detect_lang(text):
        if not text:
            return "en"
        for ch in text:
            o = ord(ch)
            if (0x4E00 <= o <= 0x9FFF) or (0x3400 <= o <= 0x4DBF) or \
               (0x3000 <= o <= 0x303F) or (0xFF00 <= o <= 0xFFEF):
                return "zh"
        return "en"


# ── 生成物尾段剥离（2026-11-20 根治：长上下文污染）────────────────────────────
# 用户把上一轮完整输出连同问题本体一起粘贴回来是高频场景。尾段里的法条名
# （《抗肿瘤药物临床试验技术指导原则》）、「按限定PD-1单抗」等会被实体正则
# 吞进 cond/intr，抽成 cond=抗肿瘤。此处在**所有抽取函数入口**先裁到问题本体，
# 单一实现、所有调用方受益（literature 的 topic 同样因此不再被污染）。
_GENERATED_TAIL = re.compile(
    r"初步说明\s*[（(]\s*首趟生成\s*[，,]?\s*仅供参考\s*[）)]"
    r"|取数结果\s*[（(]\s*按执行顺序陈列\s*[）)]"
    r"|本轮共执行\s*\d*\s*项?\s*取数"
    r"|MISSING_REQUIRED\s*:"
    r"|方法学解释\s*[，,]?\s*非取数结果"
    r"|以下按执行顺序陈列"
    r"|如需\s*[，,]?\s*我可以进一步展开"
)


def strip_generated_tail(text: str) -> str:
    """裁掉生成物尾段，只保留用户问题本体（幂等；无标记时原样 strip）。"""
    if not text:
        return ""
    s = str(text)
    m = _GENERATED_TAIL.search(s)
    return (s[:m.start()] if m else s).strip()


def has_cjk(text: str) -> bool:
    """是否含中日韩文字。复用 kw_localize.detect_lang 作为单一真源。"""
    return _detect_lang(text) == "zh"


# ── 英文实体抽取 ────────────────────────────────────────────────────────────
_EN_STOP = {
    "the", "a", "an", "our", "one", "registered", "trials", "trial",
    "case", "reports", "report", "published", "literature", "safety",
    "signal", "signals", "full", "picture", "help", "introduction",
}
_KNOWN_TARGET = re.compile(
    r"\b(PD-1|PD-L1|CTLA-4|GLP-1(?:\s*RA)?|HER2|EGFR|ALK|ROS1|BRCA1|BRCA2|VEGF|CD20)\b",
    re.I)


def extract_english_entity(q: str) -> str:
    """尽力抽取英文药名 / 靶点实体。仅英文问句生效（CJK 占比守卫）。

    优先级：已知靶点（PD-1 / GLP-1 RA 等） > 「for X」> 「X in/among/of/with Y」。
    抽不到返回空串（由调用方的 need_params 追问流程补全）。
    """
    q = strip_generated_tail(q)
    if len(re.findall(r"[\u4e00-\u9fff]", q)) >= max(1, len(q) * 0.15):
        return ""
    m = _KNOWN_TARGET.search(q)
    if m:
        return m.group(1).upper()
    m = re.search(
        r"\bfor\s+((?:[A-Za-z][A-Za-z0-9\-]*\s+){0,2}[A-Za-z][A-Za-z0-9\-]*)"
        r"(?=\s+(?:in|among|of|with)\b|\s*[,.;]|$)", q)
    if m:
        cand = re.sub(r"^(?:the|a|an)\s+", "", m.group(1).strip(), flags=re.I)
        if cand and cand.lower() not in _EN_STOP:
            return cand
    m = re.search(
        r"\b([A-Za-z][A-Za-z0-9\-]*(?:\s+[A-Za-z][A-Za-z0-9\-]+){0,2})\s+(?:in|among|of|with)\s+",
        q)
    if m:
        cand = re.sub(r"^(?:the|a|an)\s+", "", m.group(1).strip(), flags=re.I)
        if cand and cand.lower() not in _EN_STOP:
            return cand
    return ""


# ── 中英混合实体抽取 ────────────────────────────────────────────────────────
_CJK_DISEASE = re.compile(
    r"[\u4e00-\u9fa5A-Za-z0-9\-]{1,14}(?:癌|瘤|症|病|综合征|适应症)")
# 以「治疗/针对…」为界切出疾病核心词，避免药名残片被吞进 condition
# （如「帕博利珠单抗治疗晚期非小细胞肺癌」旧抽成 cond=帕博利珠单抗治疗晚期非小细胞肺癌）。
_TREAT_SPLIT = re.compile(r"(?:治疗|用于|针对|干预|应用于|配合|联合)")
_CJK_DISEASE_CORE = re.compile(
    r"(?:晚期|早期|转移性|复发性|难治性|初治|复发)?([\u4e00-\u9fa5A-Za-z0-9]{1,12}?(?:癌|瘤|症|病|综合征))")
# 问句实体抽取用药物后缀（服务于"从句子里抓药名"），与 keyword_breadth._DRUG_ZH
# （服务于"判断关键词是否过宽"）用途不同，集合可不同、互不替代。
# 允许「PD-1 抑制剂」中间空格（归一化时去掉），否则会丢掉整味药。
_CJK_DRUG = re.compile(
    r"[\u4e00-\u9fa5A-Za-z0-9\-]{1,14}\s*(?:抑制剂|单抗|抗体|肽|类药物|类似物)")
_LATIN = re.compile(r"\b[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*\b")
_LATIN_DISEASE = {"NSCLC", "SCLC", "HCC", "CRC", "T2DM", "COPD", "AML", "CLL"}
_ENTITY_BLACK = {
    "FAERS", "PRR", "ROR", "EBGM", "PubMed", "ORR", "PFS", "OS", "NCT", "CDE",
    "GCP", "ICH", "AE", "SAE", "IB", "CSR", "SAP", "ITT", "CI", "HR", "FDA",
    "EMA", "NMPA", "WHO", "CT", "RA", "MedDRA", "PT", "XX", "III", "II", "I",
    "Pull", "Give", "Find", "Search", "Compute", "Check", "How", "What",
}
# 疾病泛词（法条名/药类名里的高频残片）：不是适应症实体，禁止当 condition。
# 历史事故：长上下文《抗肿瘤药物临床试验技术指导原则》被抽成 cond=抗肿瘤。
_DISEASE_BLACK = {
    "抗肿瘤", "抗肿瘤药物", "肿瘤药物", "药物临床", "药物临床试验",
    "临床试验", "适应症", "在研药物", "研究方法", "治疗药物",
}
# 前导时间残片 / 请求动词：正则 [..]{1,14} 贪心会吞进这些噪声，统一在此剥离。
_LEAD_TIME = re.compile(r"^[\d四一二三零〇两十百千\-年月份以来近过]+\s*")
_LEAD_VERB = re.compile(
    r"^(?:请|帮我|给我|帮|查找|检索|查询|查一下|搜一下|找一下|"
    r"分析|检测|看一下|拉一下|查|搜|找|看|拉|"
    r"按限定|限定|需明确|需限定|干预为|适应症为)+\s*")


def extract_mixed_entities(q: str) -> dict:
    """从中文 / 中英混合问句抽适应症、靶点与文献主题（尽力而为，不编造）。

    返回 ``{condition, disease, target, drug_cjk, topic}``：
      - ``disease``    : **确证的疾病实体**（中文核心词 / 拉丁缩写），可能为空。
                         ct-registry 的 cond 必须用本字段，不能用 condition 兜底。
      - ``condition``  : 旧语义 ``disease or target``，保留给只认 condition 的历史调用方。
      - ``target``     : 拉丁靶点 / 药名缩写（已排除统计量与疾病缩写）
      - ``drug_cjk``   : 中文药名实体（已剥时间残片、请求动词与内部空格）
      - ``topic``      : 文献检索主题（target/drug_cjk + disease）

    仅用于给接受中文检索词的技能兜底（ct-registry 的 cond/intr、ct-literature
    的 topic）。ct-safety 的 drug 绝不取本模块的 drug_cjk（openFDA 只认英文名）。
    """
    q = strip_generated_tail(q)
    disease = ""
    parts = _TREAT_SPLIT.split(q)
    if len(parts) > 1:
        mc = _CJK_DISEASE_CORE.search(parts[-1])
        if mc:
            disease = mc.group(1)
    if not disease:
        m = _CJK_DISEASE.search(q)
        if m:
            disease = m.group(0)
    # 泛词残片（法条名 / 药类名）不是适应症，丢弃后走拉丁缩写兜底
    if disease in _DISEASE_BLACK:
        disease = ""
    if not disease:
        for tok in _LATIN.findall(q):
            if tok.upper() in _LATIN_DISEASE:
                disease = tok
                break
    m2 = _CJK_DRUG.search(q)
    drug_cjk = m2.group(0) if m2 else ""
    if drug_cjk:
        drug_cjk = _LEAD_TIME.sub("", drug_cjk)
        drug_cjk = _LEAD_VERB.sub("", drug_cjk)
        # 「PD-1 抑制剂」→「PD-1抑制剂」：检索词不要内部空格
        drug_cjk = re.sub(r"\s+", "", drug_cjk)
    targets = [t for t in _LATIN.findall(q)
               if t.upper() not in _ENTITY_BLACK
               and t.upper() not in _LATIN_DISEASE
               and len(t) >= 2]
    target = targets[0] if targets else ""
    topic = " ".join(x for x in (target or drug_cjk, disease) if x).strip()
    return {"condition": disease or target, "disease": disease, "target": target,
            "drug_cjk": drug_cjk, "topic": topic}


# ── ct-registry 参数唯一入口（2026-11-20 根治）────────────────────────────────
# 历史复发链：route_tool._extract_params 内 SUFFIX 正则 → 英文兜底 →
# has_cjk+mixed 三层覆盖；extract_params_for_tools 又补一层 setdefault；
# ct-base 再补一层。每新增入口（Web / predict / 底层）就漏一层 → 反复出现
# MISSING_REQUIRED:cond 或 cond=抗肿瘤。现收敛为本函数：任何调用方直接
# 「return extract_registry_params(q)」，不再有第二份 cond/intr 逻辑。
def extract_registry_params(q: str) -> dict:
    """ct-registry 的 ``{cond, intr}`` 唯一实现（纯确定性、无 LLM）。

    cond 优先级：确证疾病（中文核心词 / 拉丁缩写，如 NSCLC）
                 → 中文药名（如「PD-1抑制剂」「帕博利珠单抗」）
                 → 英文靶点 / 药名（如 PD-1 / semaglutide / GLP-1 RA）。
    不再要求「疾病 AND 中文药名」同时存在——纯英文靶点 + 疾病缩写（无单抗后缀）
    也要能填 cond。intr 优先中文药名，疾病主词时用靶点 / 药名补足。
    """
    text = strip_generated_tail(q)
    if not text:
        return {}
    # 纯英文问句：沿用英文实体抽取（_KNOWN_TARGET 保证 GLP-1 RA 等带空格靶点完整）
    if not has_cjk(text):
        en = extract_english_entity(text)
        return {"cond": en} if en else {}

    ent = extract_mixed_entities(text)
    disease = ent.get("disease") or ""
    drug = ent.get("drug_cjk") or ""
    target = ent.get("target") or ""

    params: dict = {}
    if disease:
        params["cond"] = disease
        if drug:
            params["intr"] = drug
        elif target and target != disease:
            params["intr"] = target
    elif drug:
        params["cond"] = drug
    elif target:
        params["cond"] = target
    return params


def extract_topic(q: str) -> str:
    """ct-literature 的 ``topic`` 唯一实现（中英统一，含尾段清洗）。

    英文走 ``extract_english_entity``（已知靶点优先）；中文走
    ``extract_mixed_entities()['topic']``。调用方直接取本函数结果，
    不得在叶子侧再拼 topic（那是历史补丁层，换个入口就漏）。
    """
    text = strip_generated_tail(q)
    if not text:
        return ""
    en = extract_english_entity(text)
    if en:
        return en
    if has_cjk(text):
        return extract_mixed_entities(text).get("topic") or ""
    return ""


# ── 离线自测 ────────────────────────────────────────────────────────────────
def _self_test() -> int:
    cases = [
        ("请帮我查询 2020 年以来帕博利珠单抗（Keytruda）治疗晚期非小细胞肺癌的临床试验注册情况",
         {"condition": "非小细胞肺癌", "drug_cjk": "帕博利珠单抗"}),
        ("查找信迪利单抗治疗肝癌的在研临床试验",
         {"condition": "肝癌", "drug_cjk": "信迪利单抗"}),
        ("拉一下 PD-1 在 NSCLC 的注册试验", {"condition": "NSCLC"}),
        # 2026-11-20 根治回归：生成物尾段不得污染实体抽取
        ("检索 PD-1 三线 NSCLC 的注册 III 期试验。\n"
         "初步说明（首趟生成，仅供参考）\n"
         "可通过 CDE、ClinicalTrials.gov 检索，按限定PD-1单抗、三线NSCLC检索。\n"
         "依据：CDE《抗肿瘤药物临床试验技术指导原则（2020年版）》\n"
         "原因码：MISSING_REQUIRED:cond",
         {"condition": "NSCLC", "disease": "NSCLC", "target": "PD-1"}),
    ]
    ok = 0
    for q, expect in cases:
        got = extract_mixed_entities(q)
        good = all(got.get(k) == v for k, v in expect.items())
        ok += good
        print("  [%s] %s -> %s" % ("PASS" if good else "FAIL", q[:32], got))

    # ct-registry 参数唯一入口回归（cond/intr 不得再依赖调用方补丁）
    reg_cases = [
        ("检索 PD-1 抑制剂三期试验有哪些", {"cond": "PD-1抑制剂"}),
        ("2020 年以来帕博利珠单抗（Keytruda）治疗晚期非小细胞肺癌的临床试验注册情况，列出主要的在研试验。",
         {"cond": "非小细胞肺癌", "intr": "帕博利珠单抗"}),
        ("查找信迪利单抗治疗肝癌的在研临床试验", {"cond": "肝癌", "intr": "信迪利单抗"}),
        ("检索 PD-1 三线 NSCLC 的注册 III 期试验。", {"cond": "NSCLC", "intr": "PD-1"}),
        ("检索 PD-1 三线 NSCLC 的注册 III 期试验。\n"
         "初步说明（首趟生成，仅供参考）\n"
         "可通过 CDE 按限定PD-1单抗检索。\n"
         "依据：CDE《抗肿瘤药物临床试验技术指导原则（2020年版）》\n"
         "原因码：MISSING_REQUIRED:cond", {"cond": "NSCLC", "intr": "PD-1"}),
        ("Pull the registered trials for semaglutide in type-2 diabetes",
         {"cond": "semaglutide"}),
        ("Give me the full competitive-intel picture for GLP-1 RA in obesity",
         {"cond": "GLP-1 RA"}),
    ]
    for q, expect in reg_cases:
        got = extract_registry_params(q)
        good = all(got.get(k) == v for k, v in expect.items())
        ok += good
        print("  [%s] registry %s -> %s" % ("PASS" if good else "FAIL", q[:32], got))

    # 英文抽取 / 语言检测复用
    en = extract_english_entity("Pull the registered trials for semaglutide in type-2 diabetes")
    h1 = has_cjk("帕博利珠单抗")
    h2 = has_cjk("pembrolizumab")
    good = (en == "semaglutide" and h1 is True and h2 is False)
    ok += good
    print("  [%s] english=%s has_cjk(zh/en)=%s/%s" %
          ("PASS" if good else "FAIL", en, h1, h2))
    # literature topic 唯一入口回归（中英 + 尾段清洗）
    topic_cases = [
        ("One of our PD-1 products has case reports of interstitial lung disease; "
         "Search the published literature for support", "PD-1"),
        ("检索 PD-1 三线 NSCLC 的注册试验。\n初步说明（首趟生成，仅供参考）\n"
         "依据：CDE《抗肿瘤药物临床试验技术指导原则》", "PD-1 NSCLC"),
    ]
    for q, expect in topic_cases:
        got = extract_topic(q)
        good = (got == expect)
        ok += good
        print("  [%s] topic %s -> %s" % ("PASS" if good else "FAIL", q[:32], got))

    total = len(cases) + len(reg_cases) + len(topic_cases) + 1
    print("query_entity 自测: %d/%d" % (ok, total))
    return 0 if ok == total else 1


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="ct-base 问句实体抽取共用件")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    raise SystemExit(_self_test() if args.self_test else 2)
