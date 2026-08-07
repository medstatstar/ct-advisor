---
file: ref-reg-cn.md
version: 2026-08-05
topics: China regulatory routing basics; safety document chain; CTA/IND & communication meetings; human genetic resources, data cross-border/GDPR/DPO, publication transparency, MSL compliance, multi-region ethics, DPIA, AI ethics, communication meeting preparation, suspension/clinical hold, data export, results registration; results registration transparency, accelerated approval programs, IPD sharing, data protection period
serves_workflows: [A, D, G]
---

<!-- === merged: ref-reg-cn-routing.md === -->
# China NMPA/CDE Document Routing (workflow A · 8.1-8.3)


## 8. China NMPA / CDE document routing (workflow A · C-layer)

### 8.1 Basic routing At minimum check per question: 《药品管理法》 and supporting rules; 《药品注册管理办法》 and implementation; current 《药物临床试验质量管理规范》 and transition; interim safety-information evaluation management / expedited reporting / DSUR management / electronic transmission; registration & publication, institution filing, inspection & data submission; CDE product & therapeutic-area guidance by chemical drug / biologic / TCM / vaccine / cell & gene / pediatric / rare disease / oncology; statistics / clinical pharmacology / BE / exposure–response / RWE / electronic data / subject-protection topics. Devices & IVD route to NMPA device regulations & registration-review guidance, do not default to drug ICH.

### 8.2 China clinical-trial safety document chain
| Task | Priority China document topic |
|---|---|
| Expedited-report responsibility / object / deadline / route | 药物临床试验期间安全性数据快速报告标准和程序, 药物临床试验期间安全信息评估与管理规范 |
| Aggregate SAE / SUSAR / AESI & identify signal | 药物临床试验期间安全性信息汇总分析和报告, 新药临床安全性评价 |
| Individual causal evaluation | 药物临床试验不良事件相关性评价 (with E2A) |
| Compile / change RSI | 研究者手册中安全性参考信息（RSI）撰写 (with E2A / E2F) |
| Compile & submit DSUR | 研发期间安全性更新报告（DSUR）管理规范 (with E2F and CDE entry) |
| Whether risk changes development decision | 新药获益-风险评估, product / therapeutic-area guidance |
| Oncology SUSAR signal | 抗肿瘤药物临床试验中 SUSAR 分析与处理 (with general docs) |

Document title / status / release date / implementation date / attachments must be re-confirmed on CDE / NMPA official site; where documents are stricter, explain scope, do not mechanically let product-specific override general obligation.

### 8.3 CTA / IND & communication meeting (C-layer core)
- **60-day tacit approval**: a clinical trial application (CTA / IND) is deemed approved if no negative opinion is received within 60 days of acceptance (specific procedure / deadline per current CDE / NMPA).
- **Communication meeting**: Type A / B / C meetings each have their own procedure & deadline, used to communicate before key development decisions; see `ref-regulatory-versions.md` and CDE official site.
- **Registration ≠ tacit approval**: trial registration & publication and tacit approval are two independent matters.
- May combine a competitor-landscape brief stitched in-house from `ct-registry` + `ct-safety` + `ct-literature` to support registration strategy & differentiation argument.

<!-- === merged: ref-reg-cn-data-ethics.md === -->
# China Data, Ethics & Cross-border Compliance (workflow A · 8.4-8.13)


### 8.4 Human genetic resources compliance & data cross-border (workflow A / registration) — HGR collection, export approval & cross-border data provision
- **Scenario / Role**: Human Genetic Resources Office / Regulatory Affairs — for multi-center trials collecting blood/tissue intended for export to a central lab for testing or foreign-party analysis, HGR approval/filing and cross-border data compliance are required.
- **Correct handling path**: ① **HGR scope**: Human genetic resource materials (blood/tissue/cells etc. containing human genome/genes) and information (genetic data) are regulated by 《人类遗传资源管理条例》; ② **Approval/filing**: Where important pedigrees, specific regions, foreign-party participation, or resource export are involved, HGR collection/preservation/international collaboration/material export approval or filing (per circumstance) is generally required, running in parallel with ethics review and CTA; ③ **Data cross-border**: Provision of genetic data/subject personal health information abroad must satisfy both HGR provisions and data security/cross-border transfer requirements (echoing §8.5), specifying recipient, purpose, de-identification and re-transfer restrictions; ④ **International collaboration**: Foreign-party participation requires international collaborative scientific research approval/filing, with rights and IP ownership clearly stated; ⑤ **Documentation**: Approval documents, informed consent (including sample/data export notification), ethics approval, and data-export security assessment archived.
- **Key points**: HGR compliance is a precondition independent of ethics/CTA; sample/genetic data export requires dedicated approval and must not be "send first, supplement later"; it stacks with cross-border data privacy requirements.
- ⚠️ HGR approval/filing scope, export conditions, and data-provision/security-assessment requirements are dynamic items — follow 《人类遗传资源管理条例》 and current MOST/NHC regulations (officially verify).

### 8.5 Cross-border data privacy & transfer compliance (GDPR / DPO) (workflow A / registration) — landing EU subject data to offshore cloud EDC
- **Scenario / Role**: Data Protection Officer (DPO) / Sponsor — trials including EU subjects transferring personal health data to offshore cloud EDC/analysis must satisfy GDPR cross-border transfer and data-subject rights.
- **Correct handling path**: ① **Transfer mechanism**: EU data export generally relies on **Standard Contractual Clauses (SCC) / Binding Corporate Rules (BCR)** or adequacy decisions, plus a Transfer Impact Assessment (TIA); ② **Data-subject rights**: Subjects have rights to access, rectify, erase (right to be forgotten), restrict processing, and portability, which must be operationalized in process and systems (data deletion upon withdrawal of consent see `ref-ops-data.md` §4.1.4); ③ **Data minimization & de-identification**: Collect only necessary data, pseudonymize/de-identify before transfer, separate keys domestic/foreign; ④ **Breach notification**: Personal data breaches must be notified to the regulator and (when material) to data subjects within prescribed time limits; ⑤ **DPO & contracts**: Establish data-protection responsibilities (DPO), sign Data Processing Agreements (DPA) with cloud/EDC/CRO, clarifying sub-processors and re-transfer; ⑥ **Link to GCP**: Tension exists between ALCOA+ traceability (§4.1) and the privacy deletion right — predefine data retention and deletion boundaries via contract/protocol.
- **Key points**: GDPR cross-border transfer requires SCC/BCR + TIA; the data-subject erasure right and the GCP data-retention obligation must be pre-coordinated; DPA and sub-processor management are indispensable.
- ⚠️ SCC/BCR versions, notification time limits, scope of data-subject rights, and localization requirements are dynamic items — follow the EU GDPR and current national data-protection laws verbatim (officially verify).

### 8.6 Publication transparency & selective-reporting control (workflow A / G) — avoid cherry-picking & post-hoc subgroups
- **Scenario / Role**: Medical Affairs / Investigator — an investigator-initiated post-hoc subgroup analysis is intended for submission; how to avoid selective reporting and satisfy pre-registration and transparency requirements.
- **Correct handling path**: ① **Pre-registration/registration**: Pivotal trials must be registered on a public registry (target/primary endpoint transparent); post-hoc subgroups must not be disguised as pre-specified; ② **Selective-reporting control**: Primary/secondary/exploratory/post-hoc analyses must be clearly labeled (echoing `ref-ops-safety.md` §5.2 results presentation); do not report only significant results and hide non-significant ones; ③ **Transparency**: CSR consistent with registry information (§5.3); publications must be coordinated with regulatory-submission conclusions and not contradict them; ④ **Data integrity**: Submitted data must originate from a traceable database, avoid "embellishment"; ⑤ Conflict of interest and funding disclosure per journal/standards.
- **Key points**: Transparency is not "publish more" but "full picture checkable" — pre-specified analyses and post-hoc explorations must be clearly distinguished and labeled.
- ⚠️ Trial registry platforms, selective-reporting and disclosure requirements are dynamic items — follow ICMJE/registry platforms and current standards (officially verify).

### 8.7 Medical affairs (MSL) communication compliance & transparency (workflow A) — boundaries of interaction with investigators
- **Scenario / Role**: Medical Affairs / MSL — Medical Science Liaisons (MSL) interacting with investigators must avoid unduly influencing investigator judgment/data and must satisfy transparency and anti-bribery requirements.
- **Correct handling path**: ① **Boundaries**: MSL provide scientific information (approved label/public data), must not induce prescribing, must not influence investigator protocol conduct or data interpretation; ② **Transparency**: Interaction records checkable; consulting/speaker fees paid to HCPs comply with anti-bribery (e.g., Sunshine Act/anti-commercial-bribery) and disclosure requirements; ③ **Separation from research**: MSL do not participate in investigator-initiated study protocol design to avoid conflicts of interest; investigator independence must be preserved; ④ **Information accuracy**: Scientific information provided must be based on authoritative sources, not exceed label or evidence; ⑤ PV interface: Medical information (including safety signals) obtained by MSL must be forwarded to PV per process.
- **Key points**: MSL value lies in scientifically neutral communication — any overreach that "influences data/prescribing" constitutes a compliance risk.
- ⚠️ Anti-bribery/Sunshine Act disclosure thresholds and MSL compliance requirements are dynamic items — follow local anti-commercial-bribery laws and industry standards (officially verify).

### 8.8 Multi-region / multinational trial ethics coordination (workflow A / D) — managing multiple IRBs and ethics differences
- **Scenario / Role**: Institution office / Ethics coordination — international multicenter trials (MRCT) involve multiple national/center IRBs with differing ethics-review requirements and standards, which must be coordinated without lowering standards.
- **Correct handling path**: ① **Central vs local IRB**: Some jurisdictions accept a central/unified IRB; some require independent local IRB review — follow each jurisdiction's rules; ② **Coordination principle**: A unified ethics submission package (common protocol/ICF/informed-consent elements) adapted locally, ensuring subject-protection standards are not lowered; ③ **Difference management**: Countries differ on risk–benefit, vulnerable populations, informed consent, compensation, and data privacy — identify differences and apply the strictest applicable or local-specific approach; ④ **Continuing review**: Multicenter continuing review (§3.7 continuing review) must meet each jurisdiction's frequency and reporting; ⑤ **Documentation**: Ethics approvals, versions, coordination records archived to support GCP inspection (§6.4).
- **Key points**: MRCT ethics coordination core is "unified baseline + local adaptation + no lowering of standards"; central IRB acceptability varies by jurisdiction.
- ⚠️ Multi-region IRB acceptability, ethics coordination and localization requirements are dynamic items — follow each jurisdiction's current GCP/ethics-review standards (officially verify).

### 8.9 Data Protection Impact Assessment (DPIA) & high-risk processing (workflow A) — GDPR Art.35 and similar assessments
- **Scenario / Role**: DPO / Sponsor — trials involving large-scale/high-risk personal health data processing (e.g., whole-genome, cross-border, wearable continuous monitoring) must conduct a DPIA and manage high risk.
- **Correct handling path**: ① **DPIA trigger**: Per GDPR Art.35 etc., high-risk processing of large-scale sensitive data, profiling, cross-border, new-technology collection etc. requires prior DPIA; ② **Content**: Describe processing purpose/necessity, risk identification (re-identification, misuse, cross-border), mitigation measures (pseudonymization, minimization, access control), residual risk and DPO/regulator consultation; ③ **Link to §8.5**: DPIA is the upstream assessment of cross-border transfer (SCC/BCR + TIA), reinforcing data-subject rights; ④ **Ongoing**: Processing changes (new endpoint, new third party) require DPIA update; ⑤ **Documentation**: DPIA report archived to support inspection and data-subject inquiries.
- **Key points**: DPIA is "pre-risk-control" for high-risk data processing — identify re-identification/cross-border/misuse risks and retain mitigation evidence, stacking with cross-border transfer assessment.
- ⚠️ DPIA trigger thresholds, assessment content and regulatory requirements are dynamic items — follow EU GDPR Art.35 and current national data-protection laws verbatim (officially verify).

### 8.10 AI / algorithm-tool ethics & regulatory review (workflow A / D) — compliance boundaries of AI-assisted decision-making
- **Scenario / Role**: Sponsor / Ethics — trials using AI tools (e.g., AI imaging §5.6, AI enrollment screening, AI safety signals, wearable algorithms) require ethics and regulatory review.
- **Correct handling path**: ① **Purpose definition**: Distinguish "assistive" (decision still made by human) vs "replacement" (requires rigorous validation §5.6); ② **Validation & transparency**: Algorithm performance, explainability, version lock, bias assessment (echoing §5.6); ③ **Ethics**: AI impact on subject rights/privacy (data, automated decisions) requires ethics review; ④ **Responsibility**: Clear attribution when algorithm errs; human review indispensable; ⑤ **Data**: AI training/inference data compliance (§8.5 DPIA §8.9).
- **Key points**: AI tools require "purpose tiering + validation + human fallback + clear responsibility" — do not use black boxes to replace clinical/ethics judgment.
- ⚠️ AI/algorithm-tool regulatory review, validation and transparency requirements are dynamic items — follow current FDA/EMA/NMPA AI/ML software clinical-validation guidelines (officially verify).

### 8.11 Communication meeting (Type A / B / C) preparation & minutes (workflow A / registration) — regulatory communication before key decisions
- **Scenario / Role**: Regulatory Affairs — before key development decisions, apply for regulatory communication meetings; preparation must be thorough and minutes closed out.
- **Correct handling path**: ① **Meeting type**: Type A (blocking procedure) / B (key decisions such as EOP2, Pre-IND, Pre-NDA) / C (general), each with its own procedure and time limit (echoing §8.3); ② **Preparation**: Background package (question list, data, protocol, proposed path), preset agenda and expected outputs; ③ **Minutes**: Consensus/divergence/action items reached at the meeting confirmed in writing, serving as the basis for subsequent submissions; ④ **Multi-region**: US-China/EU meeting procedures differ and must be arranged separately (§5.5, §5.19); ⑤ **Linkage**: Connect with §3.9/§3.5 adaptive/Bayesian, §3.8 single-arm pre-acceptance.
- **Key points**: The value of communication lies in "prior consensus" — thorough preparation + closed-loop minutes reduce later submission uncertainty.
- ⚠️ Meeting types, procedures, time limits and minutes requirements are dynamic items — follow current CDE/FDA/EMA communication guidelines (officially verify).

### 8.12 Clinical trial suspension / clinical hold & resumption (workflow A / registration) — regulatory halt and restart
- **Scenario / Role**: Regulatory Affairs / Sponsor — trial placed under regulatory clinical hold (suspended) or voluntarily suspended for safety/quality reasons; must handle and resume.
- **Correct handling path**: ① **Trigger**: Regulatory clinical hold (e.g., major safety risk, GCP issues, data integrity) or sponsor voluntary suspension (DSMB §3.10 recommendation, safety signal §4.8); ② **Response**: Assess cause, suspend enrollment/dosing, notify sites/ethics/subjects, protect already-enrolled subjects; ③ **Reply**: Submit corrective actions and evidence to the regulator, apply for hold lift; ④ **Resumption**: After conditions met, restart — protocol/process updates and retraining required; ⑤ **Linkage**: Linked with §4.2.6 recall, §6.4 inspection.
- **Key points**: Clinical hold is a regulator's mandatory suspension for subject protection — require rapid response, root-cause correction, and sufficient evidence before resumption.
- ⚠️ Clinical hold triggers, reply procedures and resumption conditions are dynamic items — follow current NMPA/FDA/EMA regulations (officially verify).

### 8.13 China data-export security assessment (PIPL / Data Security Law) & personal information protection (workflow A / registration) — compliance for exporting China subject data
- **Scenario / Role**: Human Genetic Resources Office / DPO — personal health data/HGR information of China subjects exported abroad must satisfy PIPL 《个人信息保护法》 and 《数据安全法》 export security assessment (echoing §8.4 HGR, §8.5 GDPR).
- **Correct handling path**: ① **Export path**: Per PIPL, personal-information export may proceed via security assessment/standard contract/certification; important data requires a declared security assessment; ② **Stack with HGR**: HGR material/information export also requires §8.4 approval/filing — the two run in parallel and do not substitute; ③ **De-identification**: Pseudonymize/de-identify before export, separate keys (echoing §8.5); ④ **Notification & consent**: Subject separate consent and export notification (consistent with §2.2 continuing consent); ⑤ **With regulator**: Cross-border data-transfer compliance affects multicenter and submission.
- **Key points**: China data export is multi-layered compliance of PIPL/Data Security Law + HGR regulation — security assessment and separate consent are indispensable, stacking with HGR approval.
- ⚠️ PIPL/Data Security Law export paths, security-assessment thresholds and separate-consent requirements are dynamic items — follow China 《个人信息保护法》《数据安全法》 and current CAC regulations (officially verify).

<!-- === merged: ref-reg-cn-transparency.md === -->
# Transparency, Accelerated Programs & IP (workflow A/registration · 8.14-8.17)


### 8.14 Clinical trial results registration & transparency (ClinicalTrials.gov / EU CTIS) (workflow A / G) — results-publication obligation
- **Scenario / Role**: Regulatory Affairs / Medical Affairs — trials must be registered on a public registry and results published, satisfying transparency and regulatory obligations (echoing §8.6 publication transparency).
- **Correct handling path**: ① **Registration**: Pivotal trials registered on ClinicalTrials.gov / Chinese Clinical Trial Registry / EU CTIS etc. (protocol/primary endpoint transparent); ② **Results publication**: Submit results summary (efficacy/safety) per platform time limits, consistent with CSR/registration (§5.3); ③ **With publication**: Registration consistent with publication, no selective reporting (§8.6); ④ **Jurisdictional differences**: Countries differ on registration and results-publication requirements; ⑤ **Linkage**: Connect with §7.1 submission — registration information supports regulatory credibility.
- **Key points**: Results registration is a "transparency obligation" not optional — registration + results publication + consistency with submission/publication forms public credibility.
- ⚠️ Registry platforms, results-publication time limits and content requirements are dynamic items — follow ClinicalTrials.gov, NMPA registry platform and EU CTIS current regulations (officially verify).

### 8.15 Accelerated approval programs (fast track / breakthrough therapy / priority review) (workflow registration) — regulatory pathways to accelerate development
- **Scenario / Role**: Regulatory Affairs — an investigational drug applying for FDA/EMA/NMPA accelerated approval programs (fast track, breakthrough therapy, priority review, conditional approval §5.4) must understand the pathways and commitments.
- **Correct handling path**: ① **Program types**: fast track (serious disease + unmet need), breakthrough therapy (preliminary clinical evidence substantially superior), priority review (shortened review timeline), rolling review; ② **Jurisdiction equivalents**: NMPA has breakthrough therapy, priority review, conditional approval (§5.4), special approval; ③ **Commitments**: Accelerated programs often accompany post-marketing commitments (§4.10 PASS) and risk plans (§4.9 RMP); ④ **Communication**: Pre-IND/Type B (§8.11) must pre-confirm eligibility and pathway; ⑤ **Linkage**: Links with §3.8 single-arm/conditional, §5.16 RWE label.
- **Key points**: Accelerated programs are "pathway acceleration" not "standard lowering" — must trade time for stricter post-marketing commitments and communication.
- ⚠️ Accelerated-approval-program eligibility, procedures and commitment requirements are dynamic items — follow current FDA/EMA/NMPA accelerated-program guidelines (officially verify).

### 8.16 Data sharing & individual-level data (IPD) sharing (workflow G / transparency) — compliance & governance for externally sharing research data
- **Scenario / Role**: Medical Affairs / Data governance — sponsors sharing clinical trial data (including individual-level data, IPD) externally per regulatory or journal policy must balance transparency, subject privacy and IP.
- **Correct handling path**: ① **Sharing tiers**: From summary level (CSR synopsis/results registration §8.14) → table level (TFL) → individual-level data (IPD/dataset), progressively opened, requiring advance planning; ② **IPD mechanism**: Build a data-request portal, publish data dictionary/analysis specification, set use agreements (DUA) and an independent review committee; ③ **Privacy & de-identification**: IPD must be pseudonymized/de-identified, minimal necessary fields, consistent with §8.5 GDPR/§8.13 PIPL export (export requires separate assessment); ④ **Consent basis**: Sharing scope must be pre-disclosed in ICF (§2.1)/continuing consent (§2.2); beyond-scope requires re-consent; ⑤ **IP & competition**: Set embargo period/publication policy (§8.6) to prevent selective disclosure; ⑥ **With registration**: Registry-platform metadata (§8.14) points to the sharing portal, forming a transparency closed loop.
- **Key points**: Data sharing is "limited openness, traceable, controlled reuse" — IPD requires de-identification + use agreement + consent basis, consistent with privacy/registration/transparency.
- ⚠️ IPD-sharing policy, de-identification standards, export and consent requirements are dynamic items — follow current ICMJE/EMA/FDA/NMPA data-sharing and PIPL regulations (officially verify).

### 8.17 Data protection period & patent-term restoration (workflow A / registration) — combined layout for market exclusivity
- **Scenario / Role**: Regulatory Affairs / Legal — innovative drugs post-launch enjoy data exclusivity and patent-term restoration (Patent Term Restoration / Supplementary Protection Certificate) as important market-exclusivity mechanisms.
- **Correct handling path**: ① **Data protection**: Originator new drugs/orphan drugs/pediatric drugs etc. enjoy different years of data exclusivity per jurisdiction, blocking generics from relying on originator data for filing; ② **Patent restoration**: Patent term lost to review occupation may be extended (SPC/PTE), rules differ by jurisdiction; ③ **Stacking strategy**: Data protection + patent + market exclusivity (orphan drug §5.11/pediatric exclusivity) combined layout; ④ **With generic/BE (§5.20)**: Generic filing restricted during data-protection period; ⑤ **With accelerated programs (§8.15)**: Priority review shortens review occupation, affecting restoration calculation.
- **Key points**: Market exclusivity is a "data protection + patent restoration + special exclusivity" combination — must be calculated and laid out per jurisdiction.
- ⚠️ Data-protection years, patent-term-restoration rules and pediatric/orphan exclusivity are dynamic items — follow each country's current drug-data and patent laws (officially verify).
