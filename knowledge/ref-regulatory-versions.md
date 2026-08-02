---
file: ref-regulatory-versions.md
version: 2026-08-02
tier: B
source_urls:
- https://www.ich.org
- https://www.nmpa.gov.cn
- https://www.cde.org.cn
last_verified: 2026-08-02
next_refresh: 2027-02-02
maintained_by: ct-advisor (self-maintained, not third-party ported)
note: 动态版本/状态/截止日/程序项必须实时官方核实（见 ref-regulatory-statistical.md 官方核验段）
---

# Regulatory Version Snapshot (controlled quick-reference · C-layer)

> **Nature**: This table is **maintained by ct-advisor itself** (not ported from a third party); it is the C-layer "China regulatory depth" controlled quick-reference. It is **not full-text regulation** and **does not confirm current validity** — any conclusion involving version, status, deadline, procedure or mandatory obligation must be verified in real time against the official original per the "fields to check" (see the official-verification section of `ref-regulatory-statistical.md`).

> **Relation to the other three references**: `ref-regulatory-statistical.md` explains "on what basis, how documents relate, how normative requirements land"; `ref-regulatory-versions.md` only does the quick-check of "current approximate version + verification entry", without re-expanding methodology.

## Use contract

- This table only answers "does the document exist, its rough topic, suggested verification entry"; it does not replace regulation, official guidance or project source documents.
- Entries marked `⚠️` mean version / status is volatile, or Step not implemented / consultation draft coexists — **must verify**.
- China implementation status ≠ ICH Step 4; translation ≠ official original.

## 1. ICH core guidance (extract, by topic)

| Topic | Document | Current main version (reference) | Focus | Fields to check |
|---|---|---|---|---|
| Individual safety report | E2A | Clinical safety data management | Serious AE expedited-report principle | Official original / implementation status |
| ICSR transmission | E2B(R3) | R3 | Individual safety report e-transmission | Implementation status / regional annex |
| Periodic benefit–risk | E2C(R2) | R2 | Periodic safety update | Version |
| Post-marketing safety data mgmt | E2D | — | Post-marketing HCP / consumer reports | Version |
| Development-period safety update | E2F | current | DSUR scope / period / structure | China submission period & entry |
| Clinical study report | E3 | current | CSR structure / data presentation / appendices | ICH official original |
| Dose response | E4 | current | Dose–effect study | Version |
| Ethnic factors | E5 | current | Ethnic data extrapolation | Implementation status |
| GCP | E6(R3) | **R3 (current)** | GCP principles & annex; R1 is historical | ICH Step / China GCP implementation date |
| Geriatric / pediatric / pregnancy-lactation | E7 / E11(R1) / E21 | — / R1 / — | Special populations | Version |
| Statistical principles | E9 | current | Randomization / bias / sample size / analysis set | Use with E9(R1) |
| Estimand | E9(R1) | R1 | Estimand / intercurrent event / sensitivity | Do not equate estimand with endpoint |
| Comparator selection | E10 | current | Comparator / active / placebo selection | Version |
| QT / genomic | E14 / E15 / E16 | — | QT study / biomarker / adaptive | Version |
| MRCT | E17 | current | Multi-regional trial | Implementation status |
| Adaptive / patient preference / RWE | E20 / E22 / E23 | — | Adaptive design / patient preference / real world | Version |
| CTD | M4(R4) / M4E(R2) / M4Q(R1) / M4S(R2) | each series | Five-module organization | Module 1 / e-submission region-specific |
| MedDRA (regulatory terminology) | — (MSSO-maintained; **not** an ICH M-series guideline — ICH M1 is *Medicinal Product Definition & Nomenclature*) | current MedDRA | Coding dictionary | MedDRA version |
| Bioanalysis / protocol / DDI / BE / RWD / MIDD | M10 / M11 / M12 / M13 / M14 / M15 | — | Various methodology | Version |

## 2. China NMPA / CDE basic framework

| Document / system | Type | Focus | Fields to check |
|---|---|---|---|
| 《药品管理法》 | Law | Umbrella law: registration / manufacturing / post-marketing overall | Current version / supporting rules |
| 《药品注册管理办法》 | Dept. rule | Registration classification / procedure / deadline | Release date / implementation date |
| 《药物临床试验质量管理规范》 | GCP | China GCP requirement & transition | Release date / implementation date / transition |
| 药物临床试验期间安全性数据快速报告 | Procedure | SAE / SUSAR expedited-report responsibility / deadline / route | Formal status / attachment / entry |
| 药物临床试验期间安全信息评估与管理 | Specification | Safety-information management overall | Version / implementation |
| 研发期间安全性更新报告（DSUR）管理 | Specification | DSUR compilation & submission | CDE submission entry / regional addendum |
| 临床试验登记与信息公示 | System | Registration platform / publication requirement | Platform & fields |
| 药物临床试验机构备案 | System | Institution filing requirement | Filing system |
| 核查/检查与数据递交 | System | Inspection key points / data standard | Current requirement |

## 3. CDE product / therapeutic-area guidance (extract)

| Document | Therapeutic area / topic | Focus | Fields to check |
|---|---|---|---|
| 抗肿瘤药物临床试验中 SUSAR 分析与处理 | Oncology | Cumulative analysis / signal / 2–3 cases high attention (hint, not statutory threshold) | Formal status / version |
| 研究者手册中安全性参考信息（RSI）撰写 | General | RSI inclusion / presentation / version / change | CDE official site |
| 药物临床试验不良事件相关性评价 | General | Individual causal evaluation | With E2A |
| 新药临床安全性评价 | General | Safety overall evaluation | Version |
| 新药获益-风险评估 | General | Whether risk changes development decision | Product / therapeutic-area doc |
| 药物临床试验期间安全性信息汇总分析和报告 | General | SAE / SUSAR / AESI aggregation & signal | Version |
| 沟通交流会议 | General | Type A / B / C meeting procedure / deadline | Official site / current procedure |
| 临床试验申请（CTA/IND）与默示许可 | General | **60-day tacit approval** (deemed approved if no negative opinion by deadline) | Current procedure / deadline |

> The titles, formal status, release date, implementation date and attachments of the above CDE documents **must** be re-confirmed on the CDE / NMPA official site. See the China clinical-trial safety document chain and official-verification section of `ref-regulatory-statistical.md`.

## 4. Official verification entry (quick)

- ICH: `https://www.ich.org/` ; guideline index `https://www.ich.org/page/search-index-ich-guidelines`
- NMPA: `https://www.nmpa.gov.cn/`
- CDE: `https://www.cde.org.cn/` (search "临床试验期间安全信息报告与管理", "SUSAR/RSI/DSUR", "沟通交流会议", etc.)
- Recommended search terms see the official-verification section of `ref-regulatory-statistical.md`.

## 5. Snapshot maintenance rules

- Maintained by ct-advisor; on update change only the "current main version (reference)" column and add entries — **do not change conclusive statements**.
- Any "currency" judgment defers to the official original; where this table conflicts with the official, follow the official and mark `⚠️`.
- Recommended refresh every 6–12 months or when the user triggers "re-verify"; record the update date at the end.

_Snapshot maintenance date: 2026-08-01 (maintained by ct-advisor; version info is reference value, not officially verified)._
