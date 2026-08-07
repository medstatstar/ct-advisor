---
file: ref-ops-contract.md
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
serves_workflows: [B, D, E, F, G, H]
source_file: ref-ops-design.md (lines 23-34, merged 2026-08-05)
topics: This series' contract: what it can/cannot do; dynamic items must be officially verified; source hierarchy; series file-list entry
note: Dynamic items (current regulations / deadlines / thresholds / China pathways) must be officially verified; this series' contract & source hierarchy are in ref-ops-contract.md
---
# Clinical Operations Series — Use Contract & Source Hierarchy

> This file is the Clinical Operations series contract entry (the original ref-clinical-operations.md was merged into ref-ops-design / ref-ops-gcp-site / ref-ops-execution / ref-ops-data / ref-ops-safety on 2026-08-05); use `scripts/search_refs.py` for full-text location.

## 0. Use contract

### 0.1 What this file can do
- Explain the common execution logic of trial design, execution, data, safety, quality, operations, reporting;
- Turn vague problems into decision questions, information gaps, action steps, risk controls and quality gates;
- Review whether protocol, CRF, monitoring plan, data flow, supply chain, CSR etc. form an upstream–downstream closed loop;
- Provide review dimensions for training, SOP/plan frameworks, project retrospectives and methodology QC.

### 0.2 What this file cannot replace (dynamic items must be officially verified) Do not use alone to confirm: currently effective laws / regulations / guidance and their implementation status; statutory reporting deadlines, fixed thresholds, form & database versions; current China / US / EU / Japan filing pathways; a specific trial's protocol / IB / ICF / SAP; product-specific dose, washout, sample size, non-inferiority margin or safety conclusion. For these, open the official source per the source hierarchy in `ref-reg-contract.md`.

### 0.3 Source hierarchy (consistent with reg-statistical)
1. Applicable jurisdiction's current laws / regulations and binding regulatory documents; 2. Implemented ICH / official guidance; 3. Study-specific documents (protocol / IB / ICF / SAP); 4. Organizational control documents (SOP / protocol); 5. This consolidated reference (explanation, chaining, risk framework). This file does not rewrite "industry practice" as "regulatory mandate".
