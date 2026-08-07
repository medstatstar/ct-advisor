#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate ct-advisor/knowledge/term_aliases.json for bilingual search expansion.

Strategy:
  - CORE = hand-curated high-frequency retrieval terms (zh/en/abbrev) typical
    for clinical-trial Q&A, ensuring zh<->en swapping coverage.
  - AUTO = strict-filtered auto-extraction from knowledge/ref-*.md bracket pairs
    (zh (English)), dropping sentence-residue noise (long phrases, workflow/指南/
    现行/GCP... leftovers).
  - Merge into groups (each group = co-occurring synonyms); a CORE sublist forms
    ONE group (or merges into an existing group sharing any member), so a synonym
    list is never split into isolated singletons. Write JSON.

Run:  python3 scripts/generate_term_aliases.py
"""
import re, json, glob, os
from collections import defaultdict

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOW = os.path.join(SKILL, "knowledge")
OUT = os.path.join(SKILL, "knowledge", "term_aliases.json")

# ---- CORE: hand-curated retrieval-term groups (zh/en/abbrev) ----
CORE = [
    ["源数据","source data","SDV","原始数据","source document","eSource","电子源数据"],
    ["源数据核查","SDV","source data verification","source data review"],
    ["监查","monitoring","CRA"],
    ["监查访视报告","MVR","Monitoring Visit Report"],
    ["核查","verification","SDV"],
    ["稽查","audit"],
    ["检查","inspection","监管检查"],
    ["核查准备","inspection readiness"],
    ["数据完整性","data integrity","ALCOA","ALCOA+"],
    ["数据治理","data governance"],
    ["数据库锁定","DBL","database lock","锁库"],
    ["盲态数据审查","BDR"],
    ["统计分析报告","SAR"],
    ["统计分析计划","SAP","statistical analysis plan"],
    ["病例报告表","CRF","eCRF"],
    ["电子数据采集","EDC"],
    ["临床数据管理系统","CDMS"],
    ["标准数据格式","CDISC","SDTM","ADaM"],
    ["分析数据集","ADaM"],
    ["数据呈现","SDTM"],
    ["必备文件","essential documents","ISF","TMF"],
    ["研究者文件夹","ISF"],
    ["试验主文件","TMF","eTMF"],
    ["计算机化系统验证","CSV"],
    ["申办方","sponsor"],
    ["研究者","investigator","PI","主要研究者"],
    ["中心","site"],
    ["机构","institution"],
    ["伦理委员会","IRB","IEC"],
    ["受试者","subject","participant","患者"],
    ["知情同意","informed consent","ICF","eConsent"],
    ["研究者手册","IB"],
    ["授权","authorization","delegation"],
    ["授权表","delegation log"],
    ["利益冲突","COI"],
    ["方案","protocol"],
    ["方案偏离","protocol deviation","PD","偏离"],
    ["方案违背","protocol violation"],
    ["修正案","amendment"],
    ["样本量","sample size"],
    ["把握度","power"],
    ["估计目标","estimand","E9 R1"],
    ["伴发事件","intercurrent event"],
    ["缺失","missingness","missing data"],
    ["多重性","multiplicity"],
    ["非劣效","non-inferiority"],
    ["优效","superiority"],
    ["等效","equivalence"],
    ["期中分析","interim analysis","期中"],
    ["假设检验","hypothesis testing"],
    ["一类错误","type I error","alpha"],
    ["置信区间","confidence interval","CI"],
    ["终点","endpoint"],
    ["主要终点","primary endpoint"],
    ["次要终点","secondary endpoint"],
    ["替代终点","surrogate endpoint"],
    ["生物标志物","biomarker"],
    ["伴随诊断","companion diagnostic","CDx"],
    ["富集","enrichment"],
    ["桥接","bridging","可比性"],
    ["合成对照","synthetic control"],
    ["历史对照","historical control"],
    ["外部对照","external control"],
    ["单臂","single-arm","单臂试验"],
    ["孤儿药","orphan drug"],
    ["儿科","pediatric","儿科研究计划","PIP"],
    ["老年","geriatric"],
    ["药物滥用","abuse potential","滥用潜力"],
    ["光安全","phototoxicity","photoallergy"],
    ["QTc"],
    ["群体药代","PopPK"],
    ["药代药效","PK-PD"],
    ["药物相互作用","DDI"],
    ["贝叶斯","Bayesian"],
    ["适应性","adaptive","适应性设计"],
    ["随机化","randomization","随机"],
    ["中央随机","IWRS","IRT"],
    ["破盲","unblind","unblinding","揭盲"],
    ["分配","allocation","分配隐藏","allocation concealment"],
    ["分层","stratification"],
    ["最小化","minimization"],
    ["响应自适应随机化","RAR"],
    ["生物样本","biospecimen","样本"],
    ["样本链","chain of custody"],
    ["试验用药品","investigational product","IP"],
    ["药品账目","drug accountability"],
    ["回收","recall"],
    ["应急信封","emergency envelope","应急分配"],
    ["安全性","safety"],
    ["不良事件","AE","adverse event"],
    ["严重不良事件","SAE","serious adverse event"],
    ["特别关注不良事件","AESI"],
    ["个例安全报告","ICSR"],
    ["研发期间安全性更新报告","DSUR"],
    ["研究者手册安全性参考信息","RSI"],
    ["安全性信号","safety signal","信号"],
    ["信号检测","signal detection","PRR","ROR"],
    ["药物警戒","pharmacovigilance","PV"],
    ["风险管理计划","RMP"],
    ["上市后安全性研究","PASS"],
    ["妊娠","pregnancy","育龄女性","WOCBP"],
    ["避孕","contraception"],
    ["死亡","death"],
    ["过量","overdose"],
    ["SAE 时钟","SAE clock","快速报告"],
    ["基于风险监查","RBM"],
    ["关键风险指标","KRI"],
    ["中心化监查","centralized monitoring"],
    ["质量容忍限","QTL"],
    ["纠正预防措施","CAPA"],
    ["质量","quality","QM"],
    ["有效性检查","effectiveness check"],
    ["独立影像","BICR","IRC"],
    ["中心影像","central imaging"],
    ["临床终点裁定","CEC","EAC"],
    ["患者报告结局","PRO","ePRO"],
    ["临床结局评估","COA"],
    ["Kappa"],
    ["数据监查委员会","DSMB","iDMC"],
    ["章程","charter"],
    ["无效性","futility"],
    ["贝叶斯自适应","Bayesian adaptive"],
    ["样本量重估","SSR"],
    ["预测性","predictive","预测"],
    ["诊断","diagnostic"],
    ["预后","prognostic"],
    ["药物临床试验","IND","CTA"],
    ["新药申请","NDA"],
    ["生物制品许可申请","BLA"],
    ["上市许可申请","MAA"],
    ["沟通交流","Pre-IND","Type A","Type B","Type C"],
    ["加快上市","fast track","breakthrough therapy","priority review","accelerated approval"],
    ["附条件批准","conditional approval"],
    ["真实世界证据","RWE"],
    ["真实世界研究","RWS"],
    ["数据保护","data protection"],
    ["数据跨境","cross-border","数据出境"],
    ["人遗资源","human genetic resources"],
    ["种族桥接","ethnic bridging","RFE"],
    ["国际多中心","MRCT"],
    ["主方案","master protocol"],
    ["平台试验","platform trial"],
    ["篮式","basket"],
    ["伞式","umbrella"],
    ["多臂多阶段","MAMS"],
    ["生物类似药","biosimilar"],
    ["生物等效性","BE"],
    ["同情用药","expanded access","compassionate use"],
    ["遗传毒性","genotoxicity"],
    ["药物经济学","HEOR"],
    ["个体水平数据","IPD"],
    ["数据共享","data sharing"],
    ["结果登记","trial registration","ClinicalTrials.gov"],
    ["eCTD"],
    ["CTD"],
    ["去中心化试验","DCT"],
    ["远程","remote"],
    ["招募","recruitment"],
    ["留存","retention"],
    ["脱落","dropout"],
    ["中心关闭","site closeout"],
    ["启动访视","SIV"],
    ["培训","training"],
    ["合同","contract"],
    ["保险","insurance"],
    ["补偿","compensation","诱导"],
    ["可行性","feasibility"],
    ["研究用检测方法","investigational assay","assay"],
    ["验证","validation","分析验证","analytical validation","临床验证","clinical validation"],
    ["一致性","concordance","agreement"],
    ["可比性","comparability","bridging"],
    ["漂移","drift"],
    ["锁定","locked","locked assay"],
    ["cutoff","临界值","截断值","cut-off"],
]

# ---- AUTO: strict-filtered extraction from knowledge bracket pairs ----
NOISE = ("workflow","为准","现行","指南","gcp","sop","审查","规范","cde","fda","ema",
         "nmpa","ich","pipl","gdpr","irb","官网","原文","必须","经","仍","可","与","及",
         "等","请","须","预","在","和","或","的","中","用","对","并","各","其","该","须做")
re1 = re.compile(r'([一-鿿]{2,8})\s*[（(]\s*([A-Za-z0-9][\w][\w\s/.,+\-]*?)\s*[）)]')
re2 = re.compile(r'([A-Za-z0-9][\w][\w\s/.,+\-]*?)\s*[（(]\s*([一-鿿]{2,8})\s*[）)]')
auto_pairs = []
for fp in glob.glob(os.path.join(KNOW, "ref-*.md")):
    txt = open(fp, encoding="utf-8").read()
    for m in re1.finditer(txt):
        auto_pairs.append((m.group(1).strip(), m.group(2).strip()))
    for m in re2.finditer(txt):
        auto_pairs.append((m.group(2).strip(), m.group(1).strip()))

def clean_en(v):
    if not re.match(r'^[A-Za-z0-9][A-Za-z0-9/.\-+ ]{0,17}$', v):
        return None
    if any(n in v.lower() for n in NOISE):
        return None
    return v

# ---- merge ----
groups = []          # list of sets
index = {}           # term(lower) -> group set

def get_or_create(sub):
    """Create one group for `sub`, or merge into an existing group that already
    contains any member of `sub` (keeps CORE synonym-lists and auto pairs fused
    instead of splitting a synonym list into isolated singletons)."""
    g = None
    for t in sub:
        if t.lower() in index:
            g = index[t.lower()]
            break
    if g is None:
        g = set()
        groups.append(g)
    g.update(sub)
    for t in sub:
        index[t.lower()] = g
    return g

for sub in CORE:
    get_or_create(sub)

for zh, en in auto_pairs:
    ce = clean_en(en)
    if ce is None:
        continue
    get_or_create([zh, ce])

# finalize: drop empty, sort terms (zh first then others), drop dup groups
seen = set()
aliases = []
for g in groups:
    g = {x for x in g if x}
    if not g:
        continue
    sig = frozenset(x.lower() for x in g)
    if sig in seen:
        continue
    seen.add(sig)
    lst = sorted(g, key=lambda s: (0 if re.match(r'[一-鿿]', s) else 1, -len(s), s))
    aliases.append(lst)

aliases.sort(key=lambda l: (0 if re.match(r'[一-鿿]', l[0]) else 1, l[0].lower()))

doc = {
    "version": "2026-08-06",
    "purpose": "ct-advisor 中英术语别名表：search_refs.py 检索前据此将用户关键字自动扩展为同义中英文词组，确保中文/英文提问均能命中知识库。",
    "usage": "检索时若 user pattern 含表中任一 term（不区分大小写子串），则把该 term 所在 group 全部并入正则。扩展词表可在此增删。重新生成：python3 scripts/generate_term_aliases.py",
    "aliases": aliases,
}

try:
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"WROTE {len(aliases)} groups -> {OUT}")
except Exception as e:
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_term_aliases_tmp.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"WRITE-FAILED ({e}); fallback -> {tmp}")
print(f"total groups={len(aliases)} total terms={sum(len(a) for a in aliases)}")
