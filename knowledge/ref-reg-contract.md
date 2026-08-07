---
file: ref-reg-contract.md
version: 2026-08-02
tier: A
source_urls:
- https://www.ich.org
- https://www.nmpa.gov.cn
- https://www.cde.gov.cn
- https://www.fda.gov
last_verified: 2026-08-02
next_refresh: 2027-02-02
adapted_from: github.com/A-xin946/clinical-trial-advisor (not verbatim)
serves_workflows: [A, C, F, G]
source_file: ref-reg-stats.md (lines 23-51, merged 2026-08-05)
topics: This series' contract: what it can/cannot do; regulatory-version verification hierarchy; document applicability routing table
note: Dynamic items (current regulations / deadlines / thresholds / China pathways) must be officially verified; this series' contract & source hierarchy are in ref-reg-contract.md
---
# Regulatory Series — Use Contract, Source Hierarchy & Applicability Routing

> This file is the Regulatory & Statistical series contract entry (the original ref-regulatory-statistical.md was merged into ref-reg-stats / ref-reg-submission / ref-reg-cn / ref-reg-safety / ref-reg-gcp-version / ref-reg-retrieval on 2026-08-05); use `scripts/search_refs.py` for full-text location.

## 1. Use contract & source hierarchy

### 1.1 What this file can do
- Locate the regulation / guidance / section to read or search per the question;
- Explain each document's role across safety / design / statistics / GCP / reporting / filing;
- Extract core methodology principles that do not depend on timeliness;
- Build the evidence chain `conclusion — basis — body location — applicable condition — action`;
- Identify differences between a local file's historical version, example, translation and the current official document.

### 1.2 What this file cannot replace (must verify online) Current effective version, ICH Step status, China implementation status & transition; statutory reporting deadlines, submission entry, forms, systems, data standards; whether a document is officially released / pending / in consultation / superseded / repealed / withdrawn; product / indication / population / jurisdiction / date-specific requirements; externally-facing, ethics, regulatory-communication, inspection or submission-level conclusions.

### 1.3 Source hierarchy (by applicability, not fame)
1. Applicable jurisdiction's current laws / regulations and binding regulatory documents; 2. ICH guidance implemented in that jurisdiction; 3. Regulatory-body formally released general / product / therapeutic-area technical guidance; 4. Project-approved documents, protocol, IB, ICF, SAP, safety plan, formal regulatory communication; 5. Consultation drafts / Q&A / training / examples (auxiliary only, mark status); 6. Methodology literature & verified practice knowledge. ICH reaching Step 4 does not automatically mean implemented; translations aid reading but key wording must be checked against both ICH original and China implementation document. On source conflict, do not mechanically pick "highest tier" — first check scope / version / jurisdiction / phase / project constraints and record the adoption basis.

## 2. Applicability routing table

| Document | Main requirement / use | Limitation |
|---|---|---|
| CDE《抗肿瘤药物临床试验中 SUSAR 分析与处理》 | Oncology SUSAR cumulative analysis, signal, regulatory communication | Therapeutic-area guidance; do not write its suggested thresholds as universal statutory standard |
| CDE《研究者手册中安全性参考信息（RSI）撰写》 | RSI inclusion / presentation / version / change / quality | Current version & implementation: check CDE official site |
| ICH E2F / DSUR | DSUR scope / period / structure / overall safety assessment | China submission period / entry / regional addendum: check NMPA / CDE |
| ICH E3 | Single CSR structure / data presentation / appendices | Key interpretation per current official ICH original |
| ICH E6(R1) | Understand classic GCP responsibility & essential-documents framework | Historical version; not the sole current-GCP basis |
| ICH E9 | Randomization / bias / sample size / analysis set / missing / multiplicity | Use with E9(R1) and current topic guidance |
| ICH E9(R1) | Estimand / intercurrent event / estimation / sensitivity | Do not equate estimand with endpoint / analysis set / imputation |
| ICH M4(R4) | CTD five modules, granularity, lifecycle | Module 1 and e-submission are region-specific |
| ICH M4E(R2) | Clinical overview / clinical summary / Module 5 CSR | Not a single-CSR template; pair with E3 |
| ICH M4Q(R1) / M4S(R2) | Quality / non-clinical data organization | Pair with current Q-series / S-series and regional requirements |

