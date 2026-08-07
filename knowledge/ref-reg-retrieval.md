---
file: ref-reg-retrieval.md
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
serves_workflows: [A]
source_file: ref-reg-retrieval.md (originally ref-regulatory-statistical.md §400-§413, merged 2026-08-05)
topics: Official entry points, retrieval process, search terms, conflict handling / citation / stop rules, minimal regulatory answer template
note: Dynamic items (current regulations / deadlines / thresholds / China pathways) must be officially verified; this series' contract & source hierarchy are in ref-reg-contract.md
---
# Official Retrieval, Conflict Handling & Stop Rules (workflow A)

> This file is the Regulatory & Statistical series retrieval file (the original ref-regulatory-statistical.md §400-§413 region, merged and retained on 2026-08-05); cross-series basis is in ref-reg-contract.md; use `scripts/search_refs.py` for full-text location.

## 9. Official online retrieval & currency verification (workflow A)

### 9.1 Official entries ICH `https://www.ich.org/` (guideline index `https://www.ich.org/page/search-index-ich-guidelines`); NMPA `https://www.nmpa.gov.cn/`; CDE `https://www.cde.org.cn/`.

### 9.2 Retrieval process First turn the question into `jurisdiction + product + phase + topic + document type + activity date`; for each candidate document verify: official full title & issuing body; document number / version / Step / revision; official / draft / pending / superseded / withdrawn / historical status; release & implementation date; applicable product / population / phase / role / activity; section / clause / table / footnote / appendix supporting the conclusion; official page & attachment link; retrieval date. Search snippets only locate, do not replace the original; when PDF tables / footnotes / flowcharts / attachments affect meaning, check the corresponding page image; never judge currency by file-name version number alone.

### 9.3 Recommended search terms `full document name + release / implementation / attachment`; `site:ich.org topic + guideline + Step`; `site:cde.org.cn product / indication + 临床试验技术指导原则`; `site:cde.org.cn SUSAR / RSI / DSUR + 安全性`; `site:nmpa.gov.cn 药物临床试验质量管理规范 + 实施`; `site:nmpa.gov.cn 药品注册管理办法 + 临床试验`.

## 10. Conflict handling, citation & stop rules (workflow A)

Conflicts compared in order: jurisdiction & activity date → law / regulatory tier → official / pending / draft / historical → general vs product/therapeutic-area → problem scope & role → whether project approval / protocol / SOP is stricter. Unresolvable → state the conflict & impact, do not declare a document invalid on your own. Citation format: `document name (version / date), section or clause + official link + retrieval date`; explicitly mark `regulatory / mandatory requirement`, `formal technical guidance suggestion`, `draft / Q&A / example`, `methodology judgment`, `project practice suggestion`. Stop rule: when official site inaccessible / only secondary source / version-status conflict / missing body location / jurisdiction-date unknown and changes the conclusion → stop definitive judgment, output what is unconfirmed, why it cannot be confirmed, which conclusions are affected, conservative measures before verification, official site / search terms / fields to check, pages the user can return.

## 11. Minimal regulatory answer template (workflow A)
1. **Conclusion**: how far confirmation reaches now; 2. **Applicable boundary**: jurisdiction / product / phase / role / activity date; 3. **Document role**: what each applicable regulation / guidance resolves; 4. **Official basis**: document status / body location / link / retrieval date; 5. **Project impact**: on subjects / protocol / IB-RSI / data / statistics / operations / DSUR-CSR / filing; 6. **Immediate action**: owner / time point / record / escalation / closure evidence; 7. **Unverified items**: what is missing / impact / how to verify.
