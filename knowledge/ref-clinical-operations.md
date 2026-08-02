---
file: ref-clinical-operations.md
version: 2026-08-02
tier: A
source_urls:
- https://www.ich.org
- https://www.nmpa.gov.cn
- https://www.cde.org.cn
- https://www.fda.gov
last_verified: 2026-08-02
next_refresh: 2027-02-02
serves_workflows: [B, D, E, F, G, H]
adapted_from: github.com/A-xin946/clinical-trial-advisor (not verbatim)
note: 动态项（现行法规/截止日/阈值/中国路径）须官方核实
---

# Clinical Operations & Execution Reference

> **Source & refactor note**: Content adapted from the third-party skill `github.com/A-xin946/clinical-trial-advisor` (adapted_from) and reorganized to fit ct-advisor's own architecture — **not a verbatim copy**. This file focuses on **"how to do it"** — the execution layer of trial design, GCP & quality, clinical operations, documents & data, and methodology QC. The "**on what basis**" content (regulatory versions, statistical principles, safety regulatory chain, CSR regulatory structure) lives in `ref-regulatory-statistical.md`; the two cross-link by topic and do not duplicate. Methodology facts defer to the official / project source documents.

> **Duty domain**: serves workflows `B` (trial design), `D` (GCP & quality), `E` (clinical operations), `F` (safety & DSUR — individual-case execution layer), `G` (documents & reports — execution layer), `H` (methodology QC). (Workflow `F`/`G` regulatory chain & CSR structure live in `ref-regulatory-statistical.md`; the two cross-link by topic.) **ct-series integration anchor**: sample-size / power handoff to `ct-samplesize` (workflow `C`, no in-house n computation); when advice needs real-data support, perform B-layer data grounding by reading sibling-skill outputs (see §1.4).

## 0. Use contract

### 0.1 What this file can do
- Explain the common execution logic of trial design, execution, data, safety, quality, operations, reporting;
- Turn vague problems into decision questions, information gaps, action steps, risk controls and quality gates;
- Review whether protocol, CRF, monitoring plan, data flow, supply chain, CSR etc. form an upstream–downstream closed loop;
- Provide review dimensions for training, SOP/plan frameworks, project retrospectives and methodology QC.

### 0.2 What this file cannot replace (dynamic items must be officially verified) Do not use alone to confirm: currently effective laws / regulations / guidance and their implementation status; statutory reporting deadlines, fixed thresholds, form & database versions; current China / US / EU / Japan filing pathways; a specific trial's protocol / IB / ICF / SAP; product-specific dose, washout, sample size, non-inferiority margin or safety conclusion. For these, open the official source per the source hierarchy in `ref-regulatory-statistical.md`.

### 0.3 Source hierarchy (consistent with reg-statistical)
1. Applicable jurisdiction's current laws / regulations and binding regulatory documents; 2. Implemented ICH / official guidance; 3. Study-specific documents (protocol / IB / ICF / SAP); 4. Organizational control documents (SOP / protocol); 5. This consolidated reference (explanation, chaining, risk framework). This file does not rewrite "industry practice" as "regulatory mandate".

## 1. Trial design chain (workflow B)

Evidence-production chain: `development objective → clinical question → protocol design → subject protection → executable process → data generation → statistical analysis → medical interpretation → study report → registration decision`. Track upstream–downstream impact for any local decision (an endpoint change ripples to timeline, CRF, randomization, SAP, sample size, TFL, CSR, subject burden).

### 1.1 Shared decision loop
1. Define the decision (interpret / choose / execute / correct / review / write); 2. Build the problem profile (product, indication, phase, design, jurisdiction, role, document & data status); 3. Identify the key objective or risk (subject protection / result reliability / registration use / operational feasibility); 4. Determine the evidence needed (what is confirmed, what must be officially or project-supplemented); 5. Design controls (prevent / detect / escalate / record); 6. Specify decision rules (who, under what condition, continue / suspend / modify / close); 7. Close the loop (owner, time point, evidence, approval, verification, cross-file update). When a key fact changes the conclusion, clarify first, then judge.

### 1.2 Design choices (compare by fit, not template) Parallel / crossover / single-arm / randomized / open / blinded / superiority / non-inferiority — compare on: fit to the clinical question, bias control, ethical acceptability, subject burden, sample size & time, operational feasibility, interpretability & registration use. Randomization balances known & unknown prognostic factors but cannot eliminate selection / implementation / measurement / loss-to-follow-up / reporting bias; when blinding is impossible, strengthen independent assessment, objective endpoints, standardized procedures and blinded data review.

### 1.3 Inclusion / exclusion, endpoints, comparators
- Each inclusion / exclusion criterion serves at least one purpose (protect subjects / reduce confounding / ensure endpoint assessment / implement risk control / define population); prefer enhanced monitoring, stabilization periods, stratification, rescue over direct exclusion; criteria must be objective & executable (history / time window / exam / threshold).
- Endpoints must satisfy clinical relevance, measurement reliability, reasonable timing, executability, statistical tractability. Primary / secondary / exploratory hierarchy must align with study objective, multiplicity, and reporting claims; composite / surrogate / PRO / biomarker endpoints need explicit composition, determination, missing-data handling and clinical interpretation.
- Comparator chosen by clinical question, ethics, assay sensitivity, interpretability: placebo / standard-of-care / active / dose / external control; historical or external controls must control for time trends, selection and measurement differences.

### 1.4 ct-series integration anchor (layer B)
- **Sample-size handoff**: this skill gives the parameter framework in workflow `C` (assumptions / effect size / variability / alpha / power / allocation ratio / dropout); once complete, hand off to `ct-samplesize` for actual computation — **do not compute n in-house** (see `scripts/workflows.json` `integration.sample_size_handoff`).
- **Data grounding**: when advice needs real-data support, read sibling-skill outputs per `scripts/workflows.json` `integration.data_grounding` — `ct-registry` (peer-trial count / phase / region to argue feasibility), `ct-safety` (FAERS signals to support AE monitoring), `ct-literature` (published evidence for endpoint precedent); a competitive-landscape view is stitched in-house from the three data skills — and explicitly label "Data source: ct-xxx on <date>". Pure methodology questions with no data need may skip this and state "no data grounding performed".

### 1.5 Early-phase & clinical pharmacology (B)
- BA / BE: choose crossover or parallel by half-life / carryover / within-subject variability / safety; washout controls parent drug, metabolite, pharmacodynamic residual; sampling covers absorption peak and elimination phase; predefine pre-dose concentration, vomiting, missed sampling, aberrant dosing, concomitant meds, analyte, PK parameters, determination and unevaluable rules. Food-effect studies standardize meal type / timing / dosing time / water / meal completion.
- FIH / dose escalation: starting dose grounded in toxicology / pharmacology / target / exposure prediction / uncertainty; risk control includes sentinel dosing, cohort staggered enrollment, observation intervals, cumulative review; predefine individual / cohort / study-level hold, de-escalation, escalation and termination criteria。**联合用药 IND 的剂量探索策略**：全新靶点药物 A 与已上市药 B 联合，提交联合 IND 时：① **起始剂量依据**：A 的单药 PK/PD（暴露-效应）、机制协同证据（如 A 增敏 B）、单药 MTD / RP2D（若有）；B 的已上市剂量与暴露；联合起始通常取「A 单药 RP2D 的一部分或更低 + B 标准剂量」，避免叠加未知毒性；② **DDI 预期**：评估 A 对 B 的代谢 / 转运体影响（方法见 §1.6）、B 对 A 的影响，预设剂量调整规则；③ **早期终止标准（Stopping Rules）**：基于剂量限制性毒性（DLT）、叠加毒性、药效过早饱和，预设队列暂停 / 降剂量 / 终止规则；④ 联合 vs 序贯、是否设单药对照臂须在方案中论证。联合起始剂量、DDI 与终止标准的监管期望为动态项，以 NMPA / FDA 现行 IND 与联合用药指导原则为准（官方核实）。
- PopPK: define the model-supported decision first, then design sampling; evaluate stability, predictive performance, mechanistic plausibility, covariate clinical impact and interpretability of dose recommendation.
- DDI: from metabolic enzymes / transporters / in-vitro / clinical PK / target-population concomitant meds, decide clinical study, opportunistic assessment or model prediction; translate results into contraindications / restrictions, dose adjustment, monitoring and labeling.

### 1.6 临床药理学 DDI 决策：R 值、阳性判据与说明书不确定性（workflow C / B） DDI 决策须量化：可逆抑制用 **R = 1 + [I]/Ki**（[I] 取最保守的稳态峰浓度，游离或总浓度视机制），FDA 体外 DDI 指南对可逆抑制的阳性判据通常 **R ≥ 1.1**；R=1.2 已超过阈值，按静态 [I]/Ki 法一般应开展正式临床 DDI 研究。注意：① 用最保守 [I]（总 Cmax 或游离 Cmax，视抑制机制）；② **转运体维度不计入 CYP R 值**——若药物同时是 OATP1B1 等转运体底物且治疗窗窄，即使 CYP R 值临界，仍存在转运体介导的相互作用顾虑（如升高他汀类水平），须单独评估；③ **跳过 DDI 研究的条件**：R 值低于阈值**且**无窄治疗窗 / 无敏感转运体底物 / 无机制担忧，方可在说明书中诚实描述不确定性而跳过。④ **说明书不确定性措辞**：若跳过，须声明「提示 CYP3A4 抑制（预测 R=1.2）」「为 OATP1B1 底物，避免合具该转运体底物性质的药物或加强监测」「未完成临床 DDI 研究，相互作用潜力未充分表征」，不夸大安全性。FDA《In Vitro / Clinical Drug Interaction Studies》现行阈值、R 值惯例、OATP 判据为动态项，以官方原文为准（官方核实）。

### 1.7 儿科人群剂量调整与 Assent 年龄分层（workflow B / D）— 体重/BSA 个体化给药与分龄赞同
- **场景 / 角色**：儿科专家 / 临床药理 — 儿科试验需按体重 / BSA 调整剂量，且对具备成熟度的儿童分年龄层取得 Assent，监护人签知情同意。
- **正确处理路径**：① **剂量调整**：儿科剂量常按体重（mg/kg）或体表面积（BSA）个体化，预设剂量计算规则、取整 / 上限、超重 / 肾损调整与重新计算触发；② **Assent 年龄分层**：依成熟度将儿童分龄（如 ≤6 岁仅监护人同意、7–11 岁简易 Assent、≥12 岁书面 Assent），各层语言与形式不同；③ **儿童拒绝优先**：儿童明确拒绝有创 / 继续参与时优先于监护人要求（呼应 §3.5.1）；④ **监护人同意**：法定监护人签署知情同意，与 Assent 为独立文件；⑤ **伦理与安全**：儿科试验须额外伦理审查（最小风险、直接受益、风险收益），不良事件更敏感监测。
- **关键要点**：儿科给药须个体化且剂量计算可核查；Assent 是年龄分层的持续过程，非一次性。
- ⚠️ 儿科剂量公式、Assent 年龄阈值、儿科伦理审查要求为动态项，以《儿科人群药物临床试验技术指导原则》与现行 GCP 为准（官方核实）。

### 1.8 模型引导剂量探索（CRM / BOIN）（workflow B）— 替代 3+3 的模型化升剂量
- **场景 / 角色**：临床药理学家 — FIH 剂量探索采用 CRM（连续重新评估法）或 BOIN（Bayesian optimal interval），设定目标毒性概率与剂量递增 / 暂停 / 降级决策。
- **正确处理路径**：① **目标毒性概率**：预设可接受 DLT 率（如 25%–30%），CRM / BOIN 据此动态分配受试者至接近 MTD 的剂量；② **BOIN**：基于区间的简易贝叶斯，每剂量 cohort 按预设升降边界决策，操作透明、易向 IRB 解释；③ **CRM**：基于模型更新剂量-毒性曲线，需稳健先验与频发模型检查；④ 与 §1.5 传统 cohort 升剂量比较：模型法更高效但须更严格模拟与监查；⑤ 预设暂停 / 终止规则与 DSMB/iDMC oversight（§3.7）。
- **关键要点**：模型引导法提升 MTD 估计效率，但须预设目标毒性率、先验与停止规则并经模拟验证。
- ⚠️ 目标毒性率、CRM / BOIN 实施与监管接受为动态项，以 FDA / EMA / NMPA FIH 与剂量探索现行指南为准（官方核实）。

### 1.9 肝 / 肾损害人群剂量调整（workflow B / C）— 器官功能损害下的起始剂量与调整
- **场景 / 角色**：临床药理学家 / 生物统计 — 肝功能不全 / 肾功能不全受试者如何确定起始剂量与剂量调整。
- **正确处理路径**：① **清除途径先行**：先看药物主要清除途径（肝代谢 / 肾排泄），肝损影响代谢酶与转运体、肾损影响原形排泄；② **起始剂量调整**：基于 popPK / 群体药代与内在因子（器官功能）建模，预设肝损（如 Child-Pugh 分级）/ 肾损（eGFR / CrCl 分级）各层的剂量系数或禁用层；③ **试验设计**：方案预设器官功能分层入排与剂量调整表，重度损害常排除或设专门低剂量队列；④ **动态监测**：肝 / 肾功能动态变化者须再评估剂量；⑤ **标签衔接**：肝 / 肾损剂量须在 IB / 标签明确（与 §1.5 起始剂量衔接）。
- **关键要点**：器官损害剂量须基于清除机制与暴露-效应建模，而非经验折减；分层与调整表须预先写入方案。
- ⚠️ 肝 / 肾损害分级标准、剂量调整系数与排除标准为动态项，以 FDA / EMA / NMPA 器官功能损害人群临床研究与 PopPK 现行指南为准（官方核实）。

### 1.10 定量药理学与暴露-效应建模（workflow B / C）— PopPK / PK-PD 指导剂量与给药方案
- **场景 / 角色**：临床药理学家 — 用群体药代（PopPK）与 PK-PD 模型量化暴露-效应关系，指导剂量选择、给药间隔与特殊人群调整。
- **正确处理路径**：① **模型引导**：基于稀疏采样（§1.5）构建 PopPK / PK-PD，量化协变量（体重、肾损、合并用药如 §1.6）对暴露的影响；② **暴露-效应**：链接暴露与疗效 / 安全终点，确定目标暴露范围与最优剂量；③ **剂量决策**：为起始剂量（§1.5）、器官功能调整（§1.9）、给药间隔提供依据；④ **模拟**：用模型模拟不同方案把握度与安全性，支持方案设计与监管沟通；⑤ **验证**：模型经内部 / 外部验证，不确定性透明。
- **关键要点**：定量药理学把"剂量"从经验变为暴露-效应驱动；模型须验证且不确定性须透明。
- ⚠️ 定量药理学模型、暴露-效应关系与剂量优化方法为动态项，以 FDA / EMA / NMPA 群体药代与模型引导药物开发现行指南为准（官方核实）。

### 1.11 老年人群试验特殊考量（workflow B / D）— 多病共存、多重用药与认知同意
- **场景 / 角色**：临床药理 / 研究者 — 老年患者（常多病共存、多重用药、肾损高发）入组，须特殊设计与保护。
- **正确处理路径**：① **入排**：避免过严排除导致外部有效性差，预设老年亚组与合并症分层；② **多重用药**：老年多重用药普遍，伴随用药（§4.8）与 DDI（§1.6）风险更高，须强化监测；③ **肾损高发**：老年肾损比例高，剂量须按 §1.9 调整；④ **认知与同意**：认知下降者须法定代理人 + 本人意愿（呼应 §2.2 / §3.5.1），Assent 类比；⑤ **终点**：老年适用终点（功能、跌倒、认知）与耐受性考量。
- **关键要点**：老年试验须平衡"代表性"与"脆弱保护"——分层设计 + 多重用药 / 肾损管理 + 同意能力评估。
- ⚠️ 老年人群入排、剂量与同意能力评估要求为动态项，以现行 GCP 与老年药学 / 老年医学指南为准（官方核实）。

### 1.12 药物基因组学（PGx）与剂量指导（workflow B / C）— 基因多态性影响暴露与反应
- **场景 / 角色**：临床药理 — 药物代谢酶 / 转运体基因多态性（如 CYP2C19、DPYD、HLA）影响暴露或严重不良反应，须纳入剂量与监测策略。
- **正确处理路径**：① **基因型-表型**：明确多态性对代谢（快 / 慢代谢）、转运、免疫（如 HLA-B*1502 与 SJS）的影响；② **剂量 / 选择**：依基因型调整起始剂量、选择替代药或禁忌（如 DPYD 缺陷者降氟尿嘧啶剂量）；③ **检测时机**：用药前基因检测须预先规定并写入方案 / IB，避免事后分层；④ **联合考量**：与 §1.6 DDI、§1.9 器官损害联合评估；⑤ **与伴随诊断区分**：PGx 用于剂量 / 安全，伴随诊断（§3.7）用于富集 / 获批。
- **关键要点**：PGx 把"个体差异"从经验预警转为基因可循证据——须预先规定、写入方案、与安全性监测联动。
- ⚠️ PGx 检测指征、剂量调整与禁忌要求为动态项，以 FDA / EMA / NMPA 药物基因组学与标签现行指南为准（官方核实）。

### 1.13 药物滥用潜力与依赖性评估（workflow B / C）— CNS 活性药的前置安全证据
- **场景 / 角色**：临床药理 / 安全 — 中枢神经系统（CNS）活性药物须在研发早期评估滥用潜力与躯体 / 精神依赖性，指导标签与管控。
- **正确处理路径**：① **风险预判**：按药理类别（兴奋 / 抑制 / 阿片 / 大麻素等）预判滥用相关风险；② **非临床**：体外受体 / 转运体结合、动物药物辨别 / 自身给药 / 躯体依赖（戒断）研究；③ **人体**：人体滥用潜能研究（与已知滥用药、安慰剂对照）；④ **缓解**：防滥用剂型（abuse-deterrent）、配药限制、REMS / 风险计划（§4.9 RMP）；⑤ **与标签 / 管制**：影响说明书"药理依赖性"项与受控物质列管。
- **关键要点**：滥用潜力评估是 CNS 药的"前置安全证据"——体外 / 动物 / 人体三层证据 + 防滥用剂型兜底。
- ⚠️ 滥用潜能研究设计、防滥用剂型标准与受控物质列管为动态项，以 FDA / EMA / NMPA 依赖性评估与受控物质现行法规为准（官方核实）。

### 1.14 光安全性（phototoxicity / photoallergy）评估（workflow B / C）— 光照毒性的非临床到临床链条
- **场景 / 角色**：临床药理 / 非临床 — 具光吸收特性（全身 / 局部暴露、皮肤外用、部分抗菌 / 精神 / 利尿 / NSAID）药物须评估光照毒性与光过敏性。
- **正确处理路径**：① **非临床**：3T3 NRU 光毒性试验、光致突变 / 光致癌评估（结构警示）；② **临床**：早期光毒性临床试验（给药 + 照射）、症状监测（红斑 / 水肿 / 色素沉着）；③ **风险分层**：依据暴露部位、光吸收波长、半衰期决定临床与标签警示；④ **告知**：防晒 / 避光指导写入 ICF（§2.1）/ IB；⑤ **联动**：光致癌信号与 §5.25 致癌性评估衔接。
- **关键要点**：光安全是"非临床筛查 → 临床验证 → 标签警示"链条——结构警示 + 波长 / 暴露驱动决策。
- ⚠️ 光安全性试验方法、判定标准与标签警示要求为动态项，以 ICH S10 与监管光安全现行指南为准（官方核实）。

### 1.15 儿科剂型与适口性 / 给药装置（workflow B / D）— 可接受 + 可精确分剂量
- **场景 / 角色**：临床药理 / 儿科 — 儿科试验须考虑剂型适口性、吞咽能力、给药装置与可按体重精确分剂量的规格。
- **正确处理路径**：① **剂型选择**：液体制剂 / 颗粒 / 口服混悬 / 可分割片剂，避免成人剂型直接拆分；② **适口性**：掩味 / 矫味、颜色气味接受度，避免喂药困难致依从差；③ **装置**：量杯 / 滴管 / 口服注射器精确给药，培训照护者；④ **与剂量**：按体重 / BSA 个体化（§1.7 分龄）；⑤ **与 Assent（§1.7）/ 儿童伦理**衔接。
- **关键要点**：儿科剂型是"可接受 + 可精确分剂量"——适口性与装置直接影响依从与准确给药。
- ⚠️ 儿科剂型、适口性与给药装置要求为动态项，以儿科制剂与 GCP 现行指南为准（官方核实）。

### 1.16 心血管安全性与 QTc / thorough QT 评估（workflow B / C）— 非临床 hERG → 临床 TQT → 标签
- **场景 / 角色**：临床药理 / 安全 — 具延迟心室复极化风险（尤其 hERG 抑制、精神 / 抗菌 / 抗心律失常类）药物须评估 QT 延长与心律失常风险。
- **正确处理路径**：① **非临床**：hERG 通道试验、动物遥测 QT；② **临床**：全面 QT（cQT）/ thorough QT（TQT）研究、浓度 - QT（cQT）分析；③ **监测**：心电图（ECG）QTc 定期监测、电解质校正；④ **风险分层**：依据 TQT 结果与暴露量定标签警示（§2.1）；⑤ **与剂量**：影响推荐剂量与安全窗（§1.5）。
- **关键要点**：QTc 安全是"非临床 hERG → 临床 TQT → 标签警示"链条——浓度 - QT 分析支撑风险分层。
- ⚠️ QTc / TQT 研究设计、判定与心电图监测要求为动态项，以 ICH E14 / S7B 与监管心脏安全现行指南为准（官方核实）。

### 1.17 生物分析与样本分析（PK / BA）方法验证（workflow B / C）— PK / BE 的数据底座
- **场景 / 角色**：临床药理 / 生物分析 — 支持 PK / 暴露 - 效应（§1.10）与 BE（§5.20）的样本分析须经验证生物分析方法（LC-MS/MS 等）。
- **正确处理路径**：① **方法验证**：特异性 / 选择性、准确度 / 精密度、回收率、基质效应、稳定性、定量下限 LLOQ；② **样本管理**：采集 / 处理 / 储存 / 运输温度与时效（§4.1.3 样品链）；③ **批次质控**：随行 QC 样品、校准曲线、复测规则；④ **与 PK / BA**：数据支撑暴露 - 效应与 BE 判定；⑤ **GLP**：生物分析常须 GLP 合规。
- **关键要点**：生物分析是"PK / BE 的数据底座"——方法验证 + 样本链 + 批次 QC 三支柱。
- ⚠️ 生物分析方法验证、样本处理与 GLP 要求为动态项，以 FDA 生物分析方法验证与监管现行指南为准（官方核实）。

## 2. GCP & role responsibilities (workflow D · execution layer)

> The **current GCP version & implementation status** follow the GCP version discipline section of `ref-regulatory-statistical.md`; this section covers execution principles only.

### 2.1 Ethical judgment order Scientific necessity → risk reasonable & minimized → benefit–risk acceptable → fair subject selection → genuine informed consent → adequate privacy & data protection → ongoing oversight. Scientific validity is itself an ethical requirement: a study that cannot answer its question forces subjects to bear burden with no benefit.

### 2.2 Informed consent is a continuous process Includes appropriate information, understandable expression, sufficient time, autonomous decision, opportunity to ask, no undue influence, correct version, process record, ongoing update. When new risks / procedure changes / information that may affect willingness to continue arise, assess whether to update consent and re-consent; special populations need extra assessment of consent capacity, legal representative, the subject's own wishes, minimal risk and direct benefit.

### 2.3 Responsibilities may be delegated, accountability does not disappear Investigator / institution (on-site medical decisions, eligibility, consent, protocol execution, source data, investigational product, reporting, safety); sponsor (design, resources, quality system, safety oversight, vendor supervision, cross-site risk, regulatory communication, evidence integrity); CRO / vendor (leave verifiable evidence per contract & quality agreement); monitor (verify protection, protocol, key data, issue closure); IRB / IEC (independently review benefit–risk, consent, recruitment, changes, safety); QA (independent of evaluated activity, identify systemic risk and escalate).

#### 2.4 PI 对分中心研究者（sub-I）的授权与监督（workflow D）— 委托不转移 oversight 责任
- **场景 / 角色**：研究者(PI) — 多中心试验中 PI 授权 sub-I 执行部分职责，sub-I 超授权（如独立判定合格性 / 开试验药）如何处理。
- **正确处理路径**：① PI 是 GCP 责任主体，所有 delegated 职责须写入**授权表（delegation log）**并明确生效日期与范围（呼应 §3.1.2）；② sub-I 仅在授权范围内行动，超授权操作（如未授权即筛选 / 给药）须记录为**方案偏离 / 资质问题**，溯源根因（授权不清 / 培训不足）；③ PI 对 sub-I 的监督责任不转移——须定期审查 sub-I 操作、再培训、必要时撤回授权；④ 重大超授权（影响受试者安全 / 数据可靠性）升级 QA / 伦理。
- **关键要点**：授权表是责任边界的可核查证据；PI 的 oversight 责任不因委托而消失（呼应 §2.3）。
- ⚠️ 授权范围、sub-I 资质与监督要求为动态项，以 IRB SOP 与现行 GCP 为准（官方核实）。

#### 2.5 受试者投诉与权益申诉渠道（workflow D）— 可触及、独立、留痕（含受试者申诉）
- **场景 / 角色**：受试者权益 — 受试者认为被不当纳入 / 受到不当处理，如何投诉、独立申诉与获得赔偿。
- **正确处理路径**：① 中心须公示**投诉渠道**（联系人 / 伦理 / 独立申诉途径），ICF 中告知受试者权利与申诉方式；② 投诉须记录、调查、反馈时限与责任人，重大投诉（伤害 / 权益受损）升级伦理与申办方；③ 赔偿：依合同 / 保险 / 当地法规处理受试者损害补偿（与 §3.10 参与补偿区分——赔偿是因损害而非参与）；④ 申诉独立性：可设独立于研究者 / 申办方的申诉受理（伦理或第三方）；⑤ 整改：投诉揭示的系统问题走 CAPA（§6）。
- **关键要点**：投诉权是受试者权益核心，须有可触及、独立、留痕的渠道；赔偿与参与补偿性质不同。
- ⚠️ 投诉处理时限、赔偿标准与保险要求为动态项，以当地法规、IRB SOP 与 GCP 为准（官方核实）。

#### 2.6 研究者经济利益冲突（COI）披露与管理（workflow D）— 股权 / 咨询费须透明
- **场景 / 角色**：研究者(PI) — PI 持有试验药物公司股权或收咨询费，如何披露、管理、决定是否可参与。
- **正确处理路径**：① 研究者须在**试验开始前披露**所有相关经济利益（股权、顾问、专利、演讲费），写入 IRB 申报与机构 COI 政策；② 机构 / 伦理评估冲突程度：重大冲突须**管理、减少、或排除**参与（如不由该研究者入组 / 判读）；③ 参与决策须独立于经济利益，受试者知情同意不须披露细节但机构须留痕；④ 与 §3.1.2 PI 变更衔接：新 PI 亦须 COI 声明；⑤ 持续披露：试验期间新增利益须补充申报。
- **关键要点**：COI 核心是"披露 + 管理"，而非一律排除；未披露的重大经济利益属合规缺陷。
- ⚠️ COI 披露阈值、管理机构政策要求为动态项，以机构 SOP、IRB 与现行 GCP 为准（官方核实）。

#### 2.7 电子知情同意（eConsent）与远程获取合规（workflow D）— 电子签名与过程留痕
- **场景 / 角色**：研究者 / CRC — 采用电子知情同意（eConsent，含远程视频讲解 / 电子签名）获取同意，须满足等效于纸质的法律与伦理要求。
- **正确处理路径**：① **等效原则**：eConsent 须承载纸质 ICF 全部要素（信息、理解、自愿、充分时间、提问、撤回权），且具可核查的获取过程；② **电子签名**：符合可靠电子记录 / 电子签名要求（如 21 CFR Part 11 精神或当地等效），身份核验、时间戳、不可篡改、审计轨迹；③ **远程讲解**：视频 / 远程会议讲解须留痕，确保研究者（或授权人）在场、受试者充分理解；④ **版本控制**：eICF 版本切换 / 重签同纸质（呼应 §3.5.1 / §3.17）；⑤ **撤回**：电子撤回须可记录并归档（呼应 §4.1.4）。
- **关键要点**：eConsent 的核心是"过程可核查 + 签名可靠"，不是简单把 PDF 放上网；远程获取不得弱化自愿与理解。
- ⚠️ 电子签名 / 电子记录法规、远程知情同意与身份核验要求为动态项，以 FDA 21 CFR Part 11、NMPA 电子病历 / GCP 与当地数据法现行规定为准（官方核实）。

#### 2.8 豁免与紧急情境知情同意（workflow D）— waiver / emergency consent 边界
- **场景 / 角色**：伦理 / 研究者 — 紧急救治（如卒中 / 创伤）或极小风险研究拟申请豁免 / 延迟知情同意，边界如何。
- **正确处理路径**：① **豁免前提**：仅当风险不超过最小风险、且无法在事前取得同意（如回顾性病历研究、匿名样本）时，IRB 可批准豁免或简化同意；② **紧急情境**：受试者无法表达意愿且无法定代理人及时到场（如昏迷急救），依当地法 / IRB 批准可延迟或代行同意，须事后尽快补知与征得同意（如可行）；③ **不得泛化**：治疗性干预不得借"紧急"规避同意；④ **文件**：豁免 / 紧急同意须 IRB 书面批准并记录理由，ICF 仍须覆盖可接触信息；⑤ **衔接**：与 §2.2 持续同意、§2.7 eConsent 衔接。
- **关键要点**：豁免 / 紧急同意是严格受限的例外——须 IRB 批准、最小风险、事后补知，不得泛化为常态。
- ⚠️ 豁免 / 紧急同意的适用条件、批准程序与事后补知要求为动态项，以 IRB SOP 与现行 GCP / 伦理规范为准（官方核实）。

#### 2.10 受试者隐私与数据保护落地（privacy by design）（workflow D / G）— 试验中隐私的工程化嵌入
- **场景 / 角色**：研究者 / DPO — 试验中受试者个人健康数据须从设计阶段嵌入隐私保护，而非事后补丁。
- **正确处理路径**：① **数据最小化**：仅采集必要数据，去标识 / 假名化优先（呼应 §8.5）；② **访问控制**：基于角色的最小权限、审计轨迹（呼应 §4.6 CSV / §4.10 网络安全）；③ **知情同意衔接**：隐私用途与出境告知写入 ICF（§2.2 / §8.13）；④ **留存与删除**：保存期与删除权预先规定（§4.1.4）；⑤ **跨境**：出境须合规评估（§8.5 / §8.13）。
- **关键要点**：隐私保护须"设计即嵌入"——最小化 + 假名化 + 访问控制 + 删除权构成可核查的隐私闭环。
- ⚠️ 隐私保护要求、去标识与删除权为动态项，以 GDPR / PIPL 与现行数据保护法为准（官方核实）。

#### 2.11 研究者发起研究（IIT）治理（workflow D / 注册）— 非申办方主导试验的责任边界
- **场景 / 角色**：研究者 / 机构办 — 研究者（医院 / 学术）发起的 IIT，申办方角色与责任、资助与利益冲突如何治理。
- **正确处理路径**：① **责任主体**：IIT 中研究者 / 机构常自任申办方，须承担 GCP 申办方责任（§2.3）——设计、质量、安全、上报；② **资助 / 合作**：企业资助 IIT 须透明、不干预科学独立性与数据判读（呼应 §8.7 MSL 边界）；③ **伦理与监管**：IIT 同样须伦理审查、CTA / 备案、SAE / SUSAR 报告；④ **与药企申办研究的区分**：责任、保险（§3.16）、TMF 要求一致但主体不同；⑤ **质量**：IIT 亦须风险计划（§3.14）与监查 / 稽查（§3.4 / §6.4）。
- **关键要点**：IIT 不改变 GCP 责任本质——研究者 / 机构自任申办方时须完整承接申办方义务，资助方不得侵蚀科学独立。
- ⚠️ IIT 申办方责任、资助披露与监管要求为动态项，以 IRB SOP 与现行 GCP 为准（官方核实）。

### 2.12 育龄女性（WOCBP）妊娠筛查与避孕管理（workflow D / F）— 防妊娠暴露三联
- **场景 / 角色**：研究者 / 医学 — 具生殖风险的药物试验须对育龄女性（WOCBP）实施妊娠筛查与有效避孕，防妊娠暴露。
- **正确处理路径**：① **定义与排除**：明确 WOCBP 定义与排除证据（绝经 / 绝育）；② **筛查**：入组前及定期（如每周期 / 每月）高灵敏度妊娠试验（血清 / 尿 hCG），阳性即排除 / 退出；③ **避孕**：试验期间及洗脱期有效避孕（依风险单 / 双重避孕），写入 ICF（§2.1）；④ **失败处置**：妊娠暴露按 SAE / 特别流程上报与随访（§5.4）、提供妊娠结局登记；⑤ **男性伴侣**：男性受试者致畸风险同样须避孕 / 屏障；⑥ **联动**：与 §5.6 生殖安全、§5.7 孕妇、§5.8 哺乳期衔接。
- **关键要点**：WOCBP 管理是"筛查 + 避孕 + 失败处置"三联——防暴露优先于事后补救。
- ⚠️ WOCBP 定义、妊娠试验时机 / 灵敏度与避孕要求为动态项，以 ICH M3(R2) / 现行生殖与 GCP 指南为准（官方核实）。

## 3. Clinical operations (workflow E)

### 3.1 Site activation quality gate Feasibility confirmed → responsibilities / contract / budget clear → ethics & regulatory conditions met → team delegation & training complete → systems / supplies / drug / lab ready → written release. A system flag "activated" ≠ the site is safe to screen & enroll.

### 3.1.1 机构备案前置（workflow E） 在中国开展药物临床试验，机构须已在 NMPA 药物临床试验机构备案系统完成备案（备案制，非认证制）；未备案机构不得启动筛选 / 入组。中心启动前置链：确认机构备案状态与备案专业 / 主要研究者资格 → 合同与经费 → 伦理与备案条件 → 团队授权与培训 → 系统 / 物资 / 药品 / 检验就绪 → 书面释放（见 §3.1）。备案状态以 NMPA 备案系统公示为准（具体专业 / PI 资格与试验匹配性为动态项须官方核实）；拟新增备案专业须走机构备案变更流程，不得"先启动后补备"。**机构备案与伦理审查批准是两项独立前置**：在中国，启动筛选 / 入组须同时满足①机构已在 NMPA 备案系统备案（且备案专业 / PI 与试验匹配）②伦理委员会审查同意③合同生效等。仅完成备案但未通过伦理审查的中心，**不得开始筛选或入组**——备案状态 ≠ 伦理批准，二者齐备方可启动（启动前置链见 §3.1）。

### 3.1.2 主要研究者（PI）变更的程序与文件更新（workflow E / D） PI 因退休 / 离职 / 资质变动退出时，**新 PI 接任须完成正式变更程序，不得「先接手后补手续」**：① 医院出具 PI 变更函，确认新 PI 专业资质、GCP 证书、与本试验匹配性（呼应 §3.1.1 备案专业 / PI 资格）；② 更新**授权表（delegation log）**——新 PI 列入、原 PI 移除，明确职责分工与生效日期；③ 新 PI 简历 / GCP 证书 / 利益冲突声明归档；④ 重新培训（方案 / SOP / 安全 / 数据系统）并留记录；⑤ **伦理委员会与机构备案同步更新**：PI 变更通常须报伦理审查（重大变更视机构要求），备案系统中 PI 信息须相应变更；⑥ 合同 / 经费 / 保险中 PI 责任主体更新；⑦ 受试者告知（如涉及持续治疗 / 随访的研究者变更）。仅研究者「相同资质」不等于可跳过程序——PI 是 GCP 责任主体，变更须透明、可核查、各方知悉。具体变更报备范围与伦理 / 备案要求为动态项，以机构 SOP 与现行 GCP 为准（官方核实）。

### 3.2 Site feasibility & CRO supervision Site feasibility verifies patient source, screening funnel, competing trials, key exams, rescue capability, team capacity, staff stability, prior quality, emergency care, data entry, drug / sample conditions, ethics & contract cycle, travel & follow-up burden; recruitment forecast states base / conversion / ramp / seasonality / site differences and calibrates against actual data. Vendor supervision chain: capability & compliance due diligence → scope & RACI → quality agreement → interface & escalation → deliverables & KPI → subcontractor change control → performance review. High-risk interfaces (safety database / central lab / imaging / IRT / ePRO / drug supply / external transfer) define data owner, frequency, format, version, verification, anomaly & escalation.

### 3.3 Risk-based monitoring & site closeout Identify key data & key processes first, then configure centralized / remote / on-site activities; fixed visits or 100% SDV cannot replace risk judgment. Before closeout confirm safety follow-up, data queries, drug reconciliation, samples, finance, reporting & archiving are all closed; open items keep owner, deadline and tracking.

### 3.4 SDV 与源数据核查（workflow E） SDV 校验 CRF 录入与源文件（病历 / 检验 / 处方 / 日志）一致性，是"监查"而非"抄数"；风险导向监查先定关键数据 / 关键流程，再定 SDV 范围（全部 / 抽样 / 靶向），固定 100% SDV 或固定访视不能替代风险判断（见 §3.3）。差异处理闭环：发现 → 分类（录入错误 / 方案偏离 / 数据完整性问题）→ 溯源到源文件与责任人 → 在源端更正（不覆盖原始值、保留稽查轨迹）→ 重新核查 → 关闭；录入错误走 query（见 §4.3），方案偏离走 §6 偏离流程，疑似数据完整性问题升级 QA。SDV 发现问题须留可核查证据（哪份源、哪条、谁、何时、如何改）。**接近排除/入选边界的基线值 + 后续安全事件**：数值未超阈值的，当前不属合格性偏离，但不得静默放过——须记录上下文并与医学监查员裁断其是否提示该受试者本属高风险；若研究者坚持原判定而 CRA 有合理质疑，应发起质疑 / 升级医学监查员或 QA，并在该中心对同类边界值设增强监查（呼应 §3.3 风险导向）。

### 3.4.1 监查访视报告（MVR / Monitoring Visit Report）时限与质量（workflow E） 监查访视（现场 / 中心化）结束后须及时完成书面监查报告，以固化发现、纠正措施与跟踪闭环。时限：**监查报告的具体完成与提交天数由申办方 SOP / 监查计划规定**（常见为访视结束后 10–15 个工作日内，具体为动态项须官方核实）；超期须记录原因并升级。报告须含：访视类型 / 日期 / 范围、源数据核查比例与发现、方案偏离、安全性报告核查、药品账目、受试者招募与保留、纠正措施（owner / 期限）、未关闭项跟踪、对中心质量的整体评估。MVR 是 GCP「监查」义务的可核查证据（呼应 §3.4 差异留痕），不得仅以系统内日志替代；报告时限与最低内容要求为动态项，以申办方 SOP 与现行 GCP 为准（官方核实）。

### 3.5 方案修正案分类与伦理审查（workflow D） 修正案分实质性（影响受试者安全 / 权益、科学性、终点、入排、剂量、设计）与行政性（联系信息、日期、排版、不影响风险收益）。实质性修正案（如入排标准年龄上限 65→75、主要终点变更）须伦理会议审查（convened review），行政性可快速审查（expedited）；审查前须：变更理由与批准、已入组 / 未入组受试者影响、版本切换、培训、ICF / CRF / EDC / IRT / SAP / 物资同步（亦见 §8.1 跨文件依赖）。修正案分类与审查程序为动态项，以 IRB SOP 与现行 GCP 为准（版本见 `ref-regulatory-statistical.md` §6）。
- **修正案实例（实验室变更）**：中心实验室改为本地实验室，即使检测方法学、参考范围不变，因样本流转 / 储存 / 检测主体变更可能影响数据可靠性与安全性监测一致性，一般判为**实质性修正案**，须伦理会议审查（convened review）；若质量评估有书面证据证明确实等同、不影响风险收益，可论证为行政性（快速审查）。无论何种分类，均须评估对已采数据的可比性影响，并同步更新相关 SOP / 手册 / 物资。

### 3.5.1 知情同意执行质量与获取资格（workflow D） 知情同意须由有资格人员获取：研究者，或经研究者正式授权、经培训并按 SOP 指定的人员（如 CRC / 研究护士）可在受试者有充分时间理解、提问后参与讲解并协助完成过程；但**研究者须对「自愿、充分知情」承担主体责任**，知情同意过程应在场完成、双方签字在同一过程节点落实，**不得事后补签**。CRC 讲解后研究者「回来补签」揭示知情同意时研究者缺位，属流程缺陷——应：① 暂停过程待研究者返回，或由另一位经授权人员按规定执行；② 若已发生补签，记录为流程偏离、溯源根因（SOP 授权边界不清）、培训纠正；③ SOP 须明确「谁有权获取同意、研究者何时须在场、授权边界」。知情同意的版本、语理解、撤回权告知为动态项，以现行 GCP 与伦理规范为准（官方核实）。

**ICF 版本更新与重新签署**：试验期间 ICF 版本因新增安全信息 / 程序变更更新时，已入组且在治受试者须重新获取知情同意——① 评估变更是否影响继续参与意愿（§2.2 持续同意原则）：新增非严重但常见不良反应等「影响风险认知」的信息，通常须**重新签署新版 ICF**；② 拒绝重新签署者：不得强制继续，按方案 / SOP 处理（可能退出或仅完成安全随访），并记录拒绝原因与沟通；③ 版本切换须同步更新授权、培训、物资，旧版 ICF 与签署记录归档可溯。重新签署范围与拒绝处理为动态项，以 IRB SOP 与现行 GCP 为准（官方核实）。

**儿科受试者 Assent 与监护人冲突**：对具备相应成熟度的儿童（如 8–12 岁），须取得其 **Assent（儿童版同意 / 赞同）**，由监护人签知情同意；Assent 与监护人同意是两个独立文件。当儿童明确拒绝继续（如不愿再抽血）而监护人坚持时，**儿童拒绝优先于监护人要求**——研究须以儿童最佳利益与最小伤害为原则，不得为「监护人认为为好」而强制儿童承受程序性痛苦；应：① 暂停该有创操作、评估儿童意愿与成熟度、与家属沟通；② 若涉及受试者安全 / 关键治疗，启动研究者与伦理评估；③ 必要时提交伦理委员会紧急审查，调整该受试者的参与范围或退出。儿科 Assent 年龄、拒绝处置与伦理审查要求为动态项，以《儿科人群药物临床试验技术指导原则》与现行 GCP 为准（官方核实）。

### 3.6 统一 KRI 体系与区域差异化监查计划（workflow E） E6(R3) 为现行 GCP，基于风险的监查（RBM）已内嵌为原则基线而非附加项；固定访视或 100% SDV 不能替代风险判断（见 §3.3）。国际多中心试验建议：先定 **关键质量因素（CtQ）→ 映射关键风险指标（KRI）**，常见 KRI 维度含入组节奏/符合率、数据质量（录入差异率、质疑率、超窗）、方案依从（偏离率/重要偏离）、安全性报告时效、盲态维护、试验用药品账目；以**中心化监查（centralized monitoring）为 backbone**（远程趋势分析与可视化，早于现场发现问题）。**统一框架、差异化阈值**：全球主监查计划定义统一的 KRI 分类法与风险分级逻辑，各区域附录差异化 SDV 抽样比例、容忍限值、数据跨境与监查报告要求——既满足 FDA 对 RBM 的期望，又能在 NMPA 关注 SDV 比例时以"风险论证后的靶向 SDV"替代全覆盖。E6(R2)→E6(R3) 过渡期，监查计划须体现 RBM 原则基线（GCP 版本判断见 `ref-regulatory-statistical.md` §6）。区域数据跨境、各国对 SDV 比例的现行期望、E6(R3) 实施过渡节点为动态项，以 FDA / EMA / NMPA·CDE 官网现行原文为准（官方核实）。

### 3.7 适应性 FIH 试验的伦理持续监督（workflow D / B） 适应性首次人体试验（FIH）由内部安全监查委员会（iDMC）根据 PK/PD 动态决策剂量/队列，其风险来自「决策过程」而非固定方案，故伦理委员会初始审查须审查**决策框架**而非仅固定方案：① iDMC **章程（charter）** 须提交 IRB——含成员独立性、运作规则、揭盲程序、向 IRB 的报告义务；② **预设的适应性决策规则**（剂量递增/扩展、暂停、终止标准）须透明，IRB 审查的是规则本身；③ **持续伦理监督机制**：预设 IRB 再审查触发点——当 iDMC 决策改变后续受试者风险/受益比（升剂量、扩队列、安全暂停）时自动触发 IRB 复查，iDMC 会议摘要（盲态或适当非盲）定期提交 IRB 作持续审查材料；④ **适应性修改预分类**：框架内修改（快速审查）vs 须 IRB 重新批准（实质性），初始即界定；⑤ **独立性防火墙**：iDMC 与申办方运营团队独立，IRB 须理解隔离结构以评估利益冲突控制（FIH 设计侧见 §1.5）。IRB 持续审查频率、iDMC charter 的 GCP 要求、适应性试验伦理审查细则为动态项，以现行 GCP 与伦理审查规范为准（官方核实）。

**跟踪审查（持续审查）频率**：伦理委员会对已批准试验须定期跟踪审查，最长间隔通常**不超过 12 个月**（具体以现行 GCP / 伦理审查规范要求为准，动态项须官方核实）；逾期未完成跟踪审查时，**已入组受试者通常可继续按方案用药 / 随访**（不应仅因 IRB 行政逾期中断受试者治疗），但申办方 / 研究者须主动催促 IRB 完成审查并留痕，重大安全信号仍须即时报伦理。跟踪审查最长间隔与逾期处理为动态项，以现行 GCP 与伦理审查规范为准（官方核实）。

### 3.8 单臂试验外部对照预设置与附条件批准路径（workflow B / C / 注册） 单臂设计的监管可接受性取决于适应症背景：**无标准治疗（如无 SOC 的罕见病）或 RCT 伦理/可行性不可行时，单臂（尤其作为附条件批准的关键试验）是 CDE 相对最能接受的场景**；反之，已有 SOC 的适应症（如多数实体瘤）单臂通常被视证据等级不足，须强理由。鉴于外部对照偏倚风险，须在方案中**预先（非事后）规定**（呼应本节省列 5 点预设要求）：① 可比人群定义（瘤种/线数/分子特征/基线）与单臂队列预先对齐；② 匹配/调整方法（PS、MAIC）与协变量写死；③ 时间趋势控制（历史队列同期性、治疗背景）；④ 测量一致性（RECIST 版本、是否 BICR）；⑤ 方案中预设「外部对照局限性说明」章节（CDE 审查必看）。**估计目标（E9 R1）**：ORR/DoR 的伴发事件（开始新治疗、进展前死亡、失访）策略预先定义；**敏感性分析**须主分析 + 至少 1–2 个（不同伴发事件策略、不同外部对照口径、应激检验），主/敏分明、多重性受控（多重性见 `ref-regulatory-statistical.md` §3.3）。**终点矩阵**：ORR + DoR + PFS + OS，避免单点 ORR 孤证。附条件批准逻辑：单臂关键试验 + 承诺上市后确证性试验（常需 RCT 或高质量外部/真实世界对照），单臂是阶段性证据非终局证据（证据标准、MCID、生物标志物亚组、说明书平衡见 `ref-regulatory-statistical.md` §5.4）。**Pre-IND（Type B）沟通交流强烈建议且宜早**：单臂 + 外部对照 + 附条件批准的接受度高度依赖 CDE 预先认可，议题含单臂可接受前提、外部对照构建法、ORR+支撑矩阵、确证性承诺结构、是否走突破性疗法。附条件批准适用标准、单臂关键试验接受边界、确证性试验时限、沟通交流会议程序为动态项，以 CDE 官网现行原文为准（官方核实）。

**RWE 外部对照的具体方法（呼应 §3.8）**：以 RWD 构建外部对照须满足 CDE《真实世界证据支持药物研发与审评的指导原则》核心要求——① **RWD 适用性**：数据来源（登记库 / 医保 / 电子病历）须与研究问题匹配，数据质量（完整性 / 准确性 / 时效性）经评估可接受；② **因果推断严谨性**：预先规定研究设计（回顾性队列 / 巢式 / 外部对照臂）、目标试验模拟（target trial emulation）、可比人群定义；③ **偏倚控制**：选择偏倚（用 PS / MAIC / 熵平衡匹配基线协变量）、混杂偏倚（敏感性分析 / 阴性对照 / 阳性对照检验）、时间趋势（同期对照）；④ **透明报告**：预设局限性章节与偏倚方向应激检验。RWE 接受度高度依赖预注册方案与监管事先认可（呼应 Pre-IND，§3.8）。具体 RWE 适用性标准与因果推断方法要求为动态项，以 CDE 官网现行原文为准（官方核实）。

**替代安慰剂对照的设计（罕见病 / 伦理高压场景）**：当安慰剂对照引发公众 / 患者组织强烈反对（如进展迅速致死性罕见病 ALS），可考虑替代设计——① **延迟启动设计（Delayed Start / 随机撤药）**：所有受试者先获活性治疗，随机子集延迟一段时间再启动，以「早期 vs 延迟启动的获益差」间接论证疗效，兼顾伦理；其统计假设（如早期启动组与延迟组在共同观察窗的可比性、洗脱效应）须预先定义并被监管接受；② **外部对照（见 §3.8）**：以历史 / RWE 对照替代同期安慰剂；③ **适应性 / 贝叶斯设计**降低安慰剂暴露。替代设计证据等级通常弱于 RCT 安慰剂对照，须在方案预设统计假设并尽早与监管沟通（Pre-IND / Type B）。延迟启动等设计的监管接受度与统计假设要求为动态项，以现行 GCP / 统计规范与 CDE 原文为准（官方核实）。

### 3.9 细胞 / 基因治疗长期随访（LTFU）依从性（workflow E / 注册） CAR-T 等基因 / 细胞治疗产品因迟发性不良反应（继发性恶性肿瘤、远期免疫 / 器官毒性）须长期随访（常见长达 15 年），法规义务（如基因治疗产品长期随访指导原则）与实操（搬迁 / 失访 / 主观拒绝）须平衡：① **独立 LTFU 计划与知情同意**：LTFU 可与原治疗试验知情同意分离，设专门的长期随访同意与补偿机制，降低受试者负担与脱落；② **可执行的随访路径**：结合 registry、转诊网络、受试者主动报告、医保 / 处方记录联动，对失访设分级追踪（电话 / 信函 / 第三方）；③ **法规义务不可因失访免除**：申办方须证明已尽合理努力并文档化失访原因，不能因无法联系而中止随访义务；④ **数据质量**：LTFU 数据（不良事件 / 继发癌）须 ALCOA+ 可追溯；⑤ 撤回知情同意者停止新数据采集但已采数据按约定保留。长期随访年限、最低随访内容与脱离处理为动态项，以基因治疗 / 细胞治疗长期随访现行指导原则为准（官方核实）。

### 3.10 受试者补偿与诱导偏倚防控（workflow E / D）— 交通费/营养补偿的审批、记录与伦理边界
- **场景 / 角色**：研究者 / CRC / 申办方 — 受试者因随访交通、误工申请补偿，需明确审批链、支付记录、是否构成不当诱导（inducement）。
- **正确处理路径**：① 补偿须**合理、按实际发生、不与完成研究挂钩**（避免"每次访视给固定金额"式按次付费诱发盲目留组）；② 标准写入方案 / IB / ICF 与受试者手册，ICF 中透明披露补偿项目与额度；③ 审批与支付：研究者 / CRC 核验实际发生（车票、误工证明）→ 申办方财务按 SOP 支付并留痕（避免现金无记录）；④ 受试者权益角度：补偿不得影响自愿退出权，不得因未获补偿而强迫继续；⑤ 伦理审查：补偿方案（额度、方式、对象）须报伦理审查，过高补偿可能被视为不当诱导；⑥ 记录：支付台账、税务处理按当地法规。
- **关键要点**：补偿"实报实销 + 合理误工"可接受，"按完成度递增付费"易构成诱导；ICF 透明披露 + 伦理审查 + 财务留痕是三道控制。
- ⚠️ 补偿额度上限、税务与现金支付限制、伦理审查要求为动态项，以当地法规、IRB SOP 与现行 GCP 为准（官方核实）。

### 3.11 中心库房 / 物流与运输温控失效处理（workflow E）— 申办方仓库发运途中温度记录仪失效
- **场景 / 角色**：中心库房 / 物流 / CRA — 试验用药品从申办方仓库发运至中心，途中温控记录仪（温度记录仪）故障无数据，到货后能否使用、如何处理。
- **正确处理路径**：① 到货即**隔离**该批药品、贴"待评估"标识，暂停发放；② 启动偏差调查：记录运输起止、时长、环境、记录仪故障证据、包装完整性、到货外观；③ 评估：以**留样稳定性数据 + 供应商质量意见 + 包装验证（如保温箱验证时长）**推断运输期内药品是否可能超条件；④ 由**申办方质量 / 药物供应责任人**（非物流或药房单方）裁定可用 / 限用 / 销毁；⑤ 若已发至中心使用该批，评估受试者安全、必要时医学监查与上报、告知伦理；⑥ 根因（记录仪校验 / 冗余、运输商 SOP）与 CAPA（双记录仪、实时温控报警、到货温度复核）。
- **关键要点**：温控记录仪失效 ≠ "无超温证据即可用"——缺失数据本身破坏可追溯；裁定权在质量责任人，库房 / 物流无权单方放行。
- ⚠️ 运输可接受标准、记录仪冗余要求、稳定性推断规则为动态项，以方案 / IB / GCP 与质量体系为准（官方核实）。

### 3.12 机构主体变更（合并 / 分立）的备案与文件平移（workflow E / D）— 在研试验的资质、合同与药品账目接续
- **场景 / 角色**：机构办 / 申办方 — 中心所属医院合并 / 分立致法人主体变更，在研试验的 NMPA 机构备案、合同、伦理、药品账目如何平移与报备。
- **正确处理路径**：① 新法人主体须确认仍具 NMPA 药物临床试验机构备案资格（备案专业 / PI 与试验匹配，呼应 §3.1.1），主体变更通常须走**备案变更 / 重新备案**流程，不得"先继续后补备"；② 合同与经费：原合同主体变更须签署**三方补充协议**或重签，保险被保险主体同步更新；③ 伦理：向伦理委员会报备机构主体变更，审查新主体资质与受试者保护连续性；④ 必备文件（ISF / eTMF）与试验用药品账目：依合同 / 质量协议**整体移交**新主体并留移交清单（呼应 §4.1.1）；⑤ 受试者告知与知情同意衔接（研究者 / 机构变更可能影响持续治疗）；⑥ PI 若随机构变动，按 §3.1.2 走 PI 变更。
- **关键要点**：机构合并 / 分立不直接"自动继承"在研资格——备案主体、合同、伦理须同步变更并留痕，药品账目与文件须可核查移交。
- ⚠️ 备案变更程序、主体资格承接要求为动态项，以 NMPA 备案系统与现行 GCP 为准（官方核实）。

### 3.13 CRO 质量审计与过渡管理（workflow E）— 申办方最终责任不转移
- **场景 / 角色**：申办方 / CRO — CRO 未按监查计划执行或质量不达标，如何触发审计、CAPA 与平稳过渡。
- **正确处理路径**：① 依 §3.2 供应商监督链：KPI / 交付物偏差触发**供应商审计（质量审计）**（范围、通知、现场、发现分级）；② 审计发现须有**纠正与预防措施（CAPA）**计划、责任人与时限，申办方跟踪闭环；③ 过渡：CRO 更换 / 终止须**过渡计划**（知识转移、在研数据 / 文件移交、受试者连续性、监管 / 伦理报备），避免"断档"；④ 合同与质量协议明确审计权、终止条件、数据归属与移交标准；⑤ 重大质量失败（如系统性 SDV 缺失）须评估对已产数据可靠性影响并上报。
- **关键要点**：CRO 失误由申办方承担最终责任（§2.3）——审计与过渡是申办方监督义务的延伸。
- ⚠️ CRO 审计频率、过渡报备要求为动态项，以合同 / 质量协议与现行 GCP 为准（官方核实）。

### 3.14 试验风险计划与质量容忍限（QTL）（workflow E / D）— CtQ→KRI→QTL→CAPA 闭环
- **场景 / 角色**：项目经理(PM) / QM — 基于 E6(R3) 质量风险管理制定试验风险计划，设定 CtQ 与质量容忍限（QTL）。
- **正确处理路径**：① 识别**关键质量因素（CtQ）**（影响受试者安全 / 结果可靠性的环节，呼应 §3.6）；② 每 CtQ 设**质量容忍限（QTL）**——可接受的偏离阈值，超限即触发行动；③ 风险计划含：风险描述、可能性 / 严重性、控制措施、监测指标（KRI）、QTL、升级路径；④ QTL 与 KRI 联动：中心化监查（§3.6）实时监测，超限触发 root-cause 与 CAPA；⑤ 风险计划随试验进展更新，纳入监查计划与 SAP 衔接。
- **关键要点**：QTL 把"风险导向"从原则落到可量化阈值；CtQ→KRI→QTL→CAPA 形成闭环。
- ⚠️ QTL 设定惯例、E6(R3) 质量风险管理要求为动态项，以 FDA / EMA / NMPA 现行 GCP 与风险管理指南为准（官方核实）。

### 3.15 GCP 培训体系与授权前培训（workflow E / D）— 培训是可核查的资质证据
- **场景 / 角色**：临床运营经理 / QM — 研究者 / CRC 授权前须完成 GCP 与方案培训，如何建立培训体系、记录与溯源。
- **正确处理路径**：① **授权前培训**：任何人在被写入授权表（§3.1.2 / §2.4）前须完成 GCP、方案、SOP、安全与系统培训并考核；② **持续培训**：方案修订、安全信息更新、稽查发现须触发再培训；③ **记录**：培训主题、日期、讲师、参与者、考核结果归档于 ISF / eTMF，作为资质可核查证据；④ 外包 / 第三方人员（如家庭护士，§4.1.2）须同等培训 + 资质认定；⑤ 培训缺失或造假须作为质量风险处理（CAPA，§6）。
- **关键要点**：培训不是"一次性签到"——授权前 + 持续 + 留痕构成资质闭环。
- ⚠️ GCP 培训内容与资质要求为动态项，以 IRB SOP 与现行 GCP 为准（官方核实）。

### 3.16 试验合同与受试者伤害保险（workflow E / D）— 合同主体、保险与赔偿
- **场景 / 角色**：机构办 / 申办方 — 试验合同须明确各方责任、保险 coverage 与受试者伤害赔偿流程。
- **正确处理路径**：① **合同主体**：申办方与机构（PI）签署，明确研究责任、数据权属、费用、知识产权与保险；② **受试者伤害保险**：依当地法规与 GCP 购买保险或设立补偿基金，覆盖与试验相关的伤害（与 §3.10 参与补偿区分——保险针对损害）；③ **赔偿流程**：伤害认定、申请、支付路径写入合同与 ICF，受试者知情；④ 保险须覆盖试验全程及合理随访期，机构变更（§3.12）时保险主体同步更新；⑤ 跨国多中心须满足各区域保险 / 赔偿法定要求。
- **关键要点**：合同与保险是受试者保护的 contractual 底线——伤害赔偿路径须在 ICF 与合同中透明。
- ⚠️ 保险强制要求、赔偿标准与时限为动态项，以当地法规、GCP 与合同为准（官方核实）。

### 3.17 重大修正案重新知情同意的时限衔接（workflow D）— 版本切换与受试者告知
- **场景 / 角色**：伦理委员会秘书(IRB) / 研究者 — 方案重大变更（如终点变更）获伦理批准后，已入组受试者重新签署 ICF 的时限与衔接。
- **正确处理路径**：① 重大修正案（§3.5）获伦理批准 + 版本切换后，须评估对在治受试者继续参与意愿的影响（§2.2 持续同意）；② **重新知情同意时限**：依 IRB SOP 与方案规定（常见为批准 / 新版 ICF 生效后一定窗口内完成在治者重签），具体为动态项；③ 拒绝重签者：不得强制继续，按方案处理（可能退出或仅安全随访），记录拒绝；④ 版本切换同步：授权、培训、ICF / CRF / EDC / IRT / SAP / 物资（§3.5 / §8.1）；⑤ 重签完成须跟踪闭环，未完成的受试者状态与理由留痕。
- **关键要点**：修正案批准 ≠ 自动生效——在治受试者的重签是版本控制的闭环环节，须按时限追踪。
- ⚠️ 重新知情同意时限、版本切换要求为动态项，以 IRB SOP 与现行 GCP 为准（官方核实）。

### 3.18 中心启动访视（SIV）与启动质量（workflow E）— 启动会前的最后一道 gate
- **场景 / 角色**：CRA / 临床运营经理 — 中心筛选 / 入组前须完成 Site Initiation Visit（SIV），明确启动条件与启动后责任。
- **正确处理路径**：① **启动前置**：须先满足 §3.1 启动质量门（可行性、合同、伦理、备案、授权培训、系统物资药品）；② **SIV 内容**：向中心团队讲解方案 / GCP / SOP / 安全性 / 数据系统 / 药品管理 / 监查计划，确认职责与流程；③ **启动确认**：所有关键角色（研究者、sub-I、CRC、药师、实验室）已培训并签字确认，系统已验证可用；④ **启动纪要**：记录启动日期、参与人、遗留项与关闭时限，作为已启动证据；⑤ **首例入组衔接**：遗留项未关闭前不应开始筛选 / 入组——SIV 完成 ≠ 中心 ready（呼应 §3.1）。
- **关键要点**：SIV 是"知识转移 + 责任确认"的节点，不是走形式；启动纪要 + 启动门齐备共同证明中心 ready。
- ⚠️ SIV 内容要求、启动确认清单与首例入组前置条件为动态项，以申办方 SOP 与现行 GCP 为准（官方核实）。

### 3.20 受试者招募与留存 / 脱落防控（workflow E）— recruitment funnel 与 retention plan
- **场景 / 角色**：临床运营经理 / CRA — 中心入组缓慢、脱落率高，须制定招募与留存策略并监控。
- **正确处理路径**：① **招募**：基于 §3.2 可行性设招募漏斗（base / 转化 / 爬坡 / 季节），与门诊流量、竞争试验、筛选失败率校准；多渠道（研究者转介、登记库、社区）；② **留存**：降低访视负担（居家访视 / DCT §4.1.2）、交通 / 时间补贴（§3.10 合规）、清晰沟通与关系维护、必要时召回受试者完成随访；③ **脱落监控**：用 KRI（§3.6）监测脱落率、超窗、撤回，按脱落机制（随机 / 非随机）预警；④ **脱落影响**：高脱落影响 ITT / FAS 与把握度（§4.2.2、§3.2），须敏感性分析与申办方升级；⑤ **中心差异**：低入组 / 高脱落中心走 §3.13 绩效 review。
- **关键要点**：招募与留存是可行性闭环的两端——漏斗管理 + 负担控制 + 脱落预警共同保障把握度。
- ⚠️ 招募合规边界、脱落率可接受阈值与留存措施要求为动态项，以 IRB SOP 与现行 GCP 为准（官方核实）。

### 3.21 中心关闭（site closeout）与数据 / 物资移交（workflow E）— 收尾的可核查闭环
- **场景 / 角色**：CRA / 临床运营经理 — 中心完成入组 / 随访或提前终止，须规范关闭、移交数据与物资。
- **正确处理路径**：① **关闭前确认**：安全性随访完成、数据质疑关闭、药品账目核对 / 回收、样本状态、经费结算、报告与归档（呼应 §3.3）；② **数据与文件**：ISF / eTMF 移交 / 归档（§4.1.1）、源数据可及性保留；③ **物资**：剩余试验药回收 / 销毁（§4.2.6）、设备归还；④ **受试者**：完成随访或转归交接，退出后安全随访（§4.1.4）；⑤ **文档**：关闭报告记录遗留项 owner / 期限 / 追踪。
- **关键要点**：中心关闭是"可核查收尾"而非简单停访——安全随访、数据 / 账目 / 物资闭环与归档缺一不可。
- ⚠️ 中心关闭条件、数据 / 物资移交与保留要求为动态项，以申办方 SOP 与现行 GCP 为准（官方核实）。

### 3.22 伦理委员会（IRB / IEC）组成与独立性运作（workflow D）— 审查主体的资格与防火墙
- **场景 / 角色**：机构办 / IRB — 伦理委员会的组成、独立性、运作频率与利益冲突管理，确保审查质量。
- **正确处理路径**：① **组成**：多专业 + 非科学 / 社区成员，具备审查能力与多样性；② **独立性**：委员与试验申办方 / 研究者无不当利益关联，审查不受行政 / 经济干预；③ **运作**：会议审查（convened）/ 快速审查（expedited）程序与记录、跟踪审查频率（§3.7）、文件归档；④ **COI**：委员利益冲突须声明并回避（呼应 §2.6）；⑤ **联动**：与 §3.5 修正案分类审查、§3.7 持续审查衔接。
- **关键要点**：IRB 有效性在"组成多元 + 独立 + 规范运作"——独立性防火墙是受试者保护的第一道门槛。
- ⚠️ IRB 组成、独立性要求与运作规范为动态项，以 IRB SOP 与现行 GCP / 伦理审查规范为准（官方核实）。

### 3.23 试验用药品回收、销毁与计数差异（workflow E）— 账目闭环最后一环
- **场景 / 角色**：研究药师 / CRC — 试验结束 / 受试者退出 / 召回时的剩余药品回收、销毁与账目计数须闭环可追溯。
- **正确处理路径**：① **回收**：按方案 / 合同回收未用药品、空包装、剩余液体制剂，记录批号 / 数量；② **销毁**：授权人员监督下销毁（或返还申办方集中销毁），留销毁记录与见证；③ **计数差异**：发药 - 回收 - 销毁差异须调查归因（漏记 / 丢失 / 依从）、记录并上报（§6.3）；④ **账册**：与 accountability 账册（§4.2.4）全程一致；⑤ **冷链**：温度偏离药品（§4.2.3）销毁须另行记录。
- **关键要点**：药品回收与药物销毁是"账册闭环最后一环"——回收有记录、销毁有见证、差异有归因。
- ⚠️ 药品回收销毁程序与记录要求为动态项，以 GCP 与申办方 SOP 现行规定为准（官方核实）。

### 3.24 医疗器械临床试验特殊考量（workflow E / B）— 不能照搬药物 RCT 模板
- **场景 / 角色**：临床运营 / 注册 — 医疗器械（含 IVD、植入、软件 SaMD）试验相较药物在设计、对照、终点与随访上有特殊点。
- **正确处理路径**：① **设计**：常以"金标准 / 已上市器械"对照，优效或非劣，考虑学习曲线；② **终点**：器械性能 / 可用性 / 影像 / 并发症，常需长期随访（如植入 / 起搏）；③ **盲法局限**：器械常难盲（手术 / 操作），须评估偏倚与独立终点判定（BICR / CEC）；④ **样本**：考虑操作者变异、中心效应与簇随机；⑤ **法规**：遵循器械 GCP / 注册路径（与 §8.3 申报衔接），IVD 依分析 + 临床有效性验证；⑥ **软件 / SaMD**：算法变更须版本控制与再验证（§4.6 CSV）。
- **关键要点**：器械试验是"对照 + 学习曲线 + 长期随访 + 偏倚控制"——不能照搬药物 RCT 模板。
- ⚠️ 医疗器械试验设计、对照与随访要求为动态项，以 NMPA / FDA / EMA 医疗器械 GCP 与注册现行规定为准（官方核实）。

### 3.25 受试者给药依从性与服药监测（workflow E）— 疗效数据可信度前提
- **场景 / 角色**：CRC / 研究者 — 受试者服药依从性影响疗效与暴露数据（§1.10）可靠性，须监测与记录。
- **正确处理路径**：① **监测**：计数剩余药片 / 包装、电子依从（MEMS 瓶）、血浆药物浓度佐证；② **记录**：实际服药时间 / 漏服 / 补服纳入源数据（§4.1）；③ **干预**：低依从者提醒 / 教育，严重者按方案处理；④ **与终点**：依从性影响 PP / 符合方案集与疗效解释（§5.23）；⑤ **盲态**：依从监测不影响盲态。
- **关键要点**：给药依从性是"疗效数据可信度前提"——客观监测 + 源记录 + 不破盲。
- ⚠️ 依从性监测方法与记录要求为动态项，以 GCP 与方案 / SOP 现行规定为准（官方核实）。

### 3.26 受试者招募广告与公开招募的伦理合规（workflow D / E）— 广告引流而非说服
- **场景 / 角色**：研究者 / CRC — 公开招募广告、社交媒体招募须符合伦理审查与避免诱导 / 误导。
- **正确处理路径**：① **审查**：招募材料须 IRB（§3.22）预先审查批准；② **内容**：客观、不夸大获益、不隐瞒风险、不诱导（避免过高补偿 §3.10）；③ **渠道**：社交媒体 / 平台须合规、隐私（§2.10）、可溯源；④ **公平**：保障弱势群体（§5 弱势）公平可及；⑤ **与知情同意**：广告不得替代 ICF（§2.1）。
- **关键要点**：招募广告是"伦理审查 + 客观 + 不诱导"——广告引流而非说服，ICF 才是同意。
- ⚠️ 招募广告审查与公开招募要求为动态项，以 IRB SOP 与 GCP / 招募现行规范为准（官方核实）。

### 3.27 受试者停药 / 退出与退出后随访安排（workflow E / F）— 退出不等于失联
- **场景 / 角色**：研究者 / 医学 — 受试者主动退出、因 AE / 妊娠（§2.12）/ 失访或申办方终止给药，须规范停药与安排随访（呼应 §3.20 留存）。
- **正确处理路径**：① **停药原因**：记录退出 / 停药原因（AE、撤回同意、失访、方案违背）；② **洗脱**：依半衰期确定洗脱 / 随访期（§1.5）；③ **受试者随访**：退出后安全性随访（尤其 AE / 妊娠 / 哺乳 §5.8）须按方案执行并尽量完成；④ **数据**：已采集数据保留可分析（§4.1），撤回同意者按 §2.2 处理删数据；⑤ **与终点**：影响分析集（§5.23）与脱落率（§3.20）。
- **关键要点**：停药 / 退出是"原因记录 + 洗脱 + 安全随访 + 数据归属"闭环——退出不等于失联。
- ⚠️ 停药 / 退出随访与数据保留要求为动态项，以 GCP 与方案 / SOP 现行规定为准（官方核实）。

## 4. Documents, data & e-systems (workflow G · execution layer)

> The CSR **regulatory structure** (E3 main chain, consistency chain, submission-level quality gate) is in `ref-regulatory-statistical.md` §5; this section covers execution.

### 4.1 Required records & data chain Records / data must reconstruct "what was done, why, by whom, when, with what result", with ALCOA+ attributes (attributable / legible / contemporaneous / original / accurate / complete / consistent / enduring / available). eTMF is the ongoing evidence system proving how the trial was designed, approved, executed, monitored and closed — not a repository uploaded only at the end. Data chain: `source record → CRF / external data → cleaning & coding → reconciliation → analysis dataset → TFL → CSR`; each transformation is traceable, explainable, reproducible; corrections do not overwrite original values or break the audit trail。

**受试者日记卡 / 量表等纸质源数据**：受试者自填的疼痛 NRS（0–10 分）日记卡属于**源数据（source data）**，须满足 ALCOA+；CRC 转录至 EDC 时**必须保留原始纸质件**（不得销毁或仅存转录值），原始件与转录记录共同构成可溯源证据链（转录差异按 §3.4 差异闭环处理）；ePRO 电子化采集可替代纸质但须经验证、带时间戳与签名。源数据范围与转录留存要求为动态项，以现行 GCP 与数据标准为准（官方核实）。

### 4.1.1 研究者文件夹（ISF）保存与保管（workflow D / QA） ISF 是中心层面必备文件，保存年限为动态项须以现行 GCP / 法规与合同为准（常见为试验结束后若干年，具体年限与起算点以官方要求核实）。机构无长期保存条件时，可在协议 / 质量协议下由申办方统一归档保管，但研究者对必备文件的可及性与真实性仍负主要责任，须明确移交清单、保管责任、取回与销毁流程。eTMF（申办方）与 ISF（中心）分工不同，二者均须 ALCOA+ 与可追溯（见 §4.1 数据链）。**受试者原始病历（源文件）与 ISF 区分**：原始病历是必备源文件，保存要求类似或更长，二者均须按试验文件保存义务留存。当医院常规病历销毁周期（如超 5 年）早于试验文件保存期时，研究者应对：① 试验相关病历 / ISF 受 GCP 与合同约束，保存期通常长于医院常规销毁周期，不得无条件服从医院销毁；② 销毁前将必备文件（含原始病历复印件 / ISF）依合同 / 质量协议**移交申办方统一归档**（机构无长期保存条件时允许，见上）；③ 明确移交清单、保管责任与取回 / 销毁流程，留痕。具体保存年限与起算点为动态项，以现行 GCP / 法规与合同为准（官方核实）。

**筛选失败（screen failure）受试者归档**：签署 ICF 后因实验室检查超标等未入组的受试者，仍须在 EDC / IXRS 中**分配筛选号（screening ID）**并标记为筛选失败——筛选号是追踪「曾接触本试验」受试者的关键标识，便于安全随访、撤回查询与监管核查；其已签 ICF（含版本、日期）、实验室报告等按**必备文件**归档于 ISF / eTMF 或专门筛选档案，保留年限同试验文件义务。筛选号分配范围与筛选档案保存为动态项，以方案 / SOP 与现行 GCP 为准（官方核实）。

### 4.1.2 去中心化试验（DCT）数据流的 ALCOA+ 合规（workflow E / D） DCT 引入非研究团队成员（如家庭护士上门访视）与可穿戴设备连续采集，源数据仍须 ALCOA+：① **非团队成员采集**：家庭护士经经验证 eSource/ePRO 设备 + 用户认证（attributable）、时间戳（contemporaneous）、电子签名/角色日志采集；申办方须培训 + 资质认定 + 质量协议 + 稽查外派机构，数据链可追溯（家庭护士采集 → 中心化 EDC/eSource → 清洗）（数据链见 §4.1）。② **可穿戴海量原始数据**：不必全量作传统源数据——区分连续原始流（存为机器可读原始数据集，带设备 ID/固件/算法版本元数据）与**分析相关源**（预设 SAP 衍生的终点，如访视窗内平均心率）；ALCOA+ 适用于衍生终点 + 原始溯源，建议原始全量导出至受控仓储（带保留策略），分析用预定义衍生值。③ **QC 体系**：设备校准、数据传输校验、缺失数据处理规则、可穿戴数据完整性的中心化监查 KRI、差异管理。监管对 DCT、可穿戴作源数据、保留期限的具体期望为动态项，以官方原文为准（官方核实）。

### 4.1.3 生物样本链完整性与运输温度偏离（workflow E / G） 生物样本（如 PK 血样）的**完整性（chain of custody）**须贯穿采集 → 处理 → 储存 → 运输 → 检测全流程：① 运输温度偏离（如途中 4 小时超 2–8°C）**不等于结果可直接使用**——温度超标可能降解分析物（尤其蛋白 / 核酸 / 不稳定代谢物），破坏样本代表性；② 正确流程：立即记录偏离（起止、峰值、时长、设备、发现人）、**隔离该批样本结果并标记「待评估」**、启动偏差调查（稳定性数据、中心实验室意见、样本是否可重采）；③ 由**申办方 / 中心实验室质量责任人（非研究者单方）**裁定结果是否可用、是否需重采 / 补采；④ 若研究者因「结果看起来正常」直接录入 EDC，CRA 须质疑并要求补全评估与留痕，不得静默接受；⑤ 样本链全程（采集时间、处理、温度日志、交接单）须 ALCOA+ 可追溯，作为源数据保存。样本运输可接受标准与处置权限为动态项，以方案 / IB / 中心实验室 SOP 与 GCP 为准（官方核实）。

#### 4.1.4 受试者退出 / 撤回的文档与 ICF 归档（workflow E / D）— 已入组受试者撤回同意后的文件与数据处置
- **场景 / 角色**：CRC / 研究者 — 已签署 ICF 并用药的受试者电话告知不再参与，需明确退出的文档、继续安全随访义务、原始 ICF 与撤回记录如何归档。
- **正确处理路径**：① 受试者有权随时无条件撤回知情同意（§2.2 持续同意）；撤回不溯及已采集数据的使用（按方案 / IB 约定）；② 填写**撤回知情同意书（Withdrawal of Consent）**或由研究者记录撤回声明（日期、方式、见证人、拒绝继续理由），与原始 ICF 一并归档；③ 评估是否仍需**退出后安全随访**（如药物半衰期长、已知迟发风险），该随访通常仍需完成并记录；④ 分析集归属：按 SAP 预定规则（如仍属 ITT / FAS、安全性按实际暴露），撤回 ≠ 自动移出（呼应 §4.2.2）；⑤ 电子数据：撤回者停止新数据采集，已锁数据保留；若要求删除个人数据须按数据隐私与合同评估（见 `ref-regulatory-statistical.md` §8.5）；⑥ 原始 ICF、撤回文件、筛选 / 入组记录按**必备文件**归档于 ISF / eTMF，保存年限同试验文件义务（呼应 §4.1.1）。
- **关键要点**：撤回是受试者权利，须留可核查书面证据；原始 ICF 不得销毁或仅以转录件替代；退出后安全随访与数据保留义务不因撤回免除。
- ⚠️ 撤回文件模板、退出后随访范围、数据删除权与保存年限为动态项，以现行 GCP、数据保护法规与方案 / 合同为准（官方核实）。

#### 4.1.5 生物样本销毁与二次使用授权（workflow E / G）— 剩余样本不等于可自由处置
- **场景 / 角色**：生物样本管理员 — 中心实验室返还剩余样本拟销毁，或拟用于方案外二次研究，受试者未授权。
- **正确处理路径**：① 样本销毁：依方案 / IB / 中心实验室 SOP 与合同，销毁须记录（样本 ID、数量、方式、执行人、日期），留存销毁证明；② 二次使用：方案外 / 新研究使用剩余样本须**重新获取知情同意或专门授权**（宽知情同意 / 动态同意），不得超原 ICF 范围使用；③ 若原 ICF 含"未来研究"宽授权且经伦理批准，可按约定使用并留痕；否则须新申请；④ 样本链（§4.1.3）与隐私（§8.5）须贯穿销毁 / 再利用全程；⑤ 销毁或再利用决定须可核查，纳入 ISF / eTMF。
- **关键要点**：剩余样本 ≠ "可自由处置"——销毁留证、再利用须授权，边界由原 ICF 与伦理界定。
- ⚠️ 样本保存 / 销毁年限、宽知情同意适用范围为动态项，以伦理规范、GCP 与数据保护法规为准（官方核实）。

#### 4.1.6 生物样本长期储存与稳定性（workflow E / G）— 留存样本的保存条件与效期
- **场景 / 角色**：生物样本管理员 / 中心实验室 — 剩余 / 留存样本需长期储存（如用于未来检测 / 生物标志物），须明确保存条件、稳定性与效期。
- **正确处理路径**：① **储存条件**：按样本类型（血清 / 血浆 / DNA / 组织）规定温度 / 冻存 / 防降解，设备校准与报警（呼应 §3.11 温控）；② **稳定性**：留样稳定性数据支持储存期内可用性，超期须评估；③ **效期与销毁**：保存年限依方案 / 法规（呼应 §4.1.5 销毁授权），到期销毁留证；④ **中心实验室校准**：检测设备须校准与 QC，结果可比；⑤ **链与隐私**：储存全程 ALCOA+（§4.1.3）与去标识（§8.5）。
- **关键要点**：长期储存须"条件明确 + 稳定性可证 + 效期可溯"，设备校准是保障可比的前提。
- ⚠️ 样本保存条件、稳定性验证与效期要求为动态项，以方案 / IB / 中心实验室 SOP 与 GCP 为准（官方核实）。

### 4.2 CRF, database lock & e-systems The CRF collects only data supporting endpoints / safety / protocol execution / interpretation, with explicit units / timing / options / missing-reason / logic, consistent with protocol, SoA, data standards, SAP. Before lock confirm key-data completeness, acceptable queries, external data readiness, coding & reconciliation done, important deviations classified, analysis-set decisions recorded; unlock records reason / impact / approval / correction / relock. EDC / ePRO / IRT are selected, validated, configured, tested, go-live, interfaced, run, changed, retired per intended use & risk; least-necessary permissions; key changes assess data-integrity / blinding / analysis impact. Randomization (stratification / block / allocation concealment / drug coding / permissions) and unblinding (only for genuine medical need, record reason / time / role / impact) jointly protect the allocation process.

### 4.2.1 随机化系统与应急分配（workflow E） 中央随机（IWRS / IRT）故障且受试者急需用药时，可经预设 SOP 启动应急手动分配：使用密封备用代码 / 药房备用药物，保持盲态（谁能揭盲、何时、为何留痕），分配后立即在系统内补录并核对。应急分配须事前在 SOP / 随机手册规定触发条件、授权、盲态保护、事后核对与稽查轨迹；事后评估对随机化与盲态的影响、是否需上报。IWRS 权限、配置、应急流程须经验证与培训（系统选择 / 验证见 §4.2）。

### 4.2.2 紧急破盲（为救治揭晓分组）（workflow E） 紧急破盲与 §4.2.1 的「应急分配」不同：系为受试者救治之需**揭晓其所属治疗组**。授权：由研究者依预设 SOP / 盲态保持计划申请，经中央随机（IRT）执行紧急揭盲，须记录理由、时间、执行人、对盲态的影响。破盲后数据处理：该受试者仍按**原随机分组纳入分析（ITT 原则，保持随机化完整性）**，破盲信息对疗效盲态评估人员设盲；安全性分析按实际接受的治疗。用药前撤回的受试者分析集归属：① **ITT / FAS 通常包含该受试者**——ITT 原则下所有完成随机化、分配药物编号者即便未用药 / 撤回，仍属 ITT / FAS（保留随机化完整性、避免选择性排除偏倚）；② 仅在**预设**排除规则下（如从未暴露且属重大方案违反）才可考虑移出 FAS，但须预先定义并在 SAP 写清；③ 安全性集按实际暴露计。撤回 ≠ 自动移出 ITT/FAS，归属须预先规定、透明、可溯源（分析集定义见 `ref-regulatory-statistical.md` §3.2）。破盲本身须留完整稽查轨迹，事后评估是否需上报 / 是否影响其他受试者盲态。何人有权破盲、破盲流程与数据处置为动态项，以方案 / SOP 与现行 GCP 为准（官方核实）。

### 4.2.3 试验用药品温度超标与冷链偏离处理（workflow E） 试验用药品须按方案 / IB / 标签要求储存（常见 2–8°C 冷藏），温度偏离（如冰箱故障致超范围）**不等于可正常发放**：即使外观无可见变化，化学性质 / 效价 / 稳定性可能已受影响，且偏离本身破坏「药品账目与质量可追溯」。正确流程：① **立即隔离**超标批号药品、暂停发放、贴「待评估」标识；② 记录偏离全程（起止时间、峰值温度、时长、设备、环境、发现人）；③ 启动**偏差调查（deviation investigation）**：评估对药品质量与受试者安全的影响（稳定性数据、留样、供应商意见）；④ 由**申办方 / 药剂与质量责任人（非药房管理员单方）**决定销毁或经稳定性论证后限用，结论须有质量依据并留痕；⑤ 若已有受试者使用偏离期内药品，评估安全性影响、必要时医学监查与上报、告知伦理；⑥ 根因（设备故障 / 报警失灵 / 人员疏忽）与 CAPA（报警、备用冰箱、温度连续监测、SOP 培训）。CRC / 药房管理员**无权单方决定正常发放**——「外观无变化 = 问题不大」是典型错误判断。具体储存条件、偏离可接受标准与处置权限为动态项，以方案 / IB / GCP 与质量体系为准（官方核实）。

### 4.2.4 试验用药品清点、回收与计数差异（workflow E） 试验用药品须建立**药品账目（drug accountability）**：发放、使用、回收、销毁、在库数量逐盒 / 逐瓶记录并可追溯至受试者。出现**计数差异**（如发放 120 片、回收 + 销毁 110 片、差 10 片）：① 不视为「可能受试者丢弃」而直接关闭——须发起**差异调查**：核对发放记录、受试者服药日记 / 剩余药返还、销毁记录、转运记录、盘点时点，定位差异来源（记录错误 / 未返还 / 遗失 / 被盗）；② CRA 须记录差异、发起 query / 偏离评估，由**药房管理员 + 申办方药物供应 / 质量责任人**裁断是否构成方案偏离或重大药品管理问题；③ 差异若无法合理解释或疑为药品流失，须升级报告、评估受试者安全（是否误服 / 过量）、必要时医学监查与上报、告知伦理；④ 根因与 CAPA（强化回收流程、服药日记核对、定期盘点、转运双签）；⑤ 账目与调查记录须 ALCOA+ 留痕，作为必备文件保存。CRC / 药房管理员**无权单方认定「问题不大」并跳过调查**——药品账目完整性是 GCP 核心要求。计数差异调查权限、偏离判定与保存要求为动态项，以方案 / IB / GCP 与质量体系为准（官方核实）。

#### 4.2.5 随机化最小化法与分配隐藏（workflow E）— 均衡分配须严防信息泄露
- **场景 / 角色**：生物统计师 / CRA — 试验采用最小化（minimization）随机或分层随机，IRT 配置与分配隐藏如何保障不致破盲 / 选择偏倚。
- **正确处理路径**：① **最小化法**：依已入组受试者预后因子动态平衡分配，须由 IRT 自动执行、不向中心透露下例患者分配倾向，防止操纵；② **分配隐藏（allocation concealment）**：随机序列由中心随机系统生成与保管，研究者仅在入组后获分配结果，杜绝前瞻性知晓；③ IRT 配置：分层因子、区组（若用）、最小化权重、紧急破盲（§4.2.2）权限须预设并验证（§4.2 系统验证）；④ 破盲风险：最小化 / 分层信息泄露可致选择偏倚，须审计随机日志与访问权限；⑤ 与 SAP 一致：随机化方法写清于 SAP 与随机手册。
- **关键要点**：最小化提升组间均衡但须严防信息泄露；分配隐藏与盲态维护是随机化完整性的两道防线。
- ⚠️ 最小化实现方式、随机化配置与验证要求为动态项，以方案 / SAP 与现行统计规范为准（官方核实）。

#### 4.2.6 试验用药品召回与系统缺陷收回（workflow E）— 在研期间发现系统性质量缺陷
- **场景 / 角色**：申办方 / 药房 — 在研期间发现某批药品系统缺陷（如密封失效、效价不达标）或需召回，如何执行与报告。
- **正确处理路径**：① **隔离与召回**：立即隔离相关批号、暂停发放、启动召回（recall）程序，通知各中心药房停用；② **调查与裁定**：由质量责任人评估缺陷对受试者安全影响（已用批次），必要时医学监查、上报伦理 / 监管、告知受试者；③ **系统性缺陷**：若为系统性（影响多批 / 多中心），须扩大调查、CAPA（供应商 / 工艺）、评估对整体试验数据可靠性；④ 记录：召回范围、批号、执行、回收数量、受试者影响与纠正，ALCOA+ 留痕；⑤ 与 §4.2.3 冷链偏离、§4.2.4 账目衔接——召回是缺陷处置的升级动作。
- **关键要点**：召回是质量缺陷的强制处置——须快速、全域、留痕，并评估受试者安全与数据影响。
- ⚠️ 召回程序、报告路径与时限为动态项，以 GCP、质量体系与监管缺陷报告要求为准（官方核实）。

#### 4.2.7 药物编盲与包装（双盲一致性 / 应急信封）（workflow E）— 盲态维护从包装起步
- **场景 / 角色**：CRC / 药房 — 双盲试验药品须外观 / 口味一致，应急信封（emergency envelope）管理与破损盲态处理。
- **正确处理路径**：① **编盲与包装**：活性药与安慰剂外观、包装、标签一致，由独立编盲方按随机序列包装，盲底密封保管；② **应急信封**：每受试者 / 每盒配应急破盲信封，仅在紧急医疗需要时可破（呼应 §4.2.2 紧急破盲），破盲须记录并留痕；③ **盲态维护**：药房 / CRC 不得接触盲底，发药按随机号；意外破盲（如包装混淆）须报告、评估对盲态影响、可能该受试者数据按实际处理；④ 编盲方案与盲态检查写于盲态保持计划；⑤ 破损 / 缺失应急信封须补发并记录。
- **关键要点**：双盲的有效性依赖包装一致 + 盲底隔离 + 应急信封受控；任何盲态泄露须即时评估。
- ⚠️ 编盲 / 包装规范、应急信封管理要求为动态项，以方案 / SOP 与 GCP 为准（官方核实）。

#### 4.2.8 响应自适应随机化（RAR）（workflow E / C）— 按疗效动态调整分配比
- **场景 / 角色**：生物统计师 — 试验采用响应自适应随机化（RAR），按中期疗效动态调整各组分配概率，须控制偏倚与操作复杂性。
- **正确处理路径**：① **RAR 逻辑**：基于已入组受试者的应答 / 终点，提高较优臂的分配概率，增加受试者的预期获益；② **控制偏倚**：须预设自适应规则并经模拟验证（type I error 受控），防止中期数据泄露致选择偏倚；③ **与 SAP 衔接**：分配规则、adaptation 时点、盲态维护写清；④ **与 §4.2.5 最小化 / 分配隐藏协同**：RAR 仍需分配隐藏与随机日志审计；⑤ **监管沟通**：Pre-IND / Type B 预先认可（呼应 §3.5 贝叶斯自适应）。
- **关键要点**：RAR 提升伦理但增加操作 / 统计复杂——须预设规则、模拟验证并与监管沟通。
- ⚠️ RAR 接受度、模拟与偏倚控制要求为动态项，以 FDA / EMA / NMPA 适应性设计现行指南为准（官方核实）。

### 4.3 数据质疑生命周期（workflow G · 执行层） 质疑闭环：开启 → 分类（逻辑校验 / 录入差异 / 人工质疑）→ 路由到责任人（研究者 / 中心 / 实验室）→ 响应与更正（在源端改，不覆盖原始值、保留稽查轨迹）→ 核查 → 关闭或重开。质疑类型：系统自动校验（编辑检查 / 逻辑门）、人工抽审、外部数据比对；指标含未关闭质疑数、账龄、按中心 / 变量分布。关闭前确认关键数据完整、重要偏离已分类、分析集决策已记录（见 §4.2 锁库前清单）。质疑不得静默忽略，重要项须留处理记录，不得用"已解决"掩盖未溯源的更正。数据管理员**无权单方面修改 EDC 原始值或强制关闭质疑**：当中心回复「确认无误」但 DM 复核仍认为不合理时，须重发 query 要求中心提供源文件证据 / 复核理由；中心坚持时升级医学监查员 / 研究者裁断，必要时现场源文件比对；全部处理留痕。所有更正必须在源端进行（见 §3.4 SDV 差异闭环）。

### 4.4 缺失数据预设、CDISC 编码与 CSR 透明（workflow C / G） 先判定缺失机制：**MCAR / MAR / MNAR**。非随机缺失（如集中于入组较晚受试者）倾向 MNAR，多重插补（MI，假定 MAR）单独使用会系统性偏倚结论——这是监管接受度的真实风险点。**SAP 须在锁库前、揭盲前定稿**：主分析（明确定义分析集与缺失处理，如 MAR 下混合模型/MI）+ **敏感性分析（必需，针对 MNAR）**：参考基线填补（reference-based imputation，如 J2R/CR）或 tipping-point 分析，证明结论稳健；主/敏分明、多重性受控（引 `ref-regulatory-statistical.md` §3.3）。**CDISC 合规**：SDTM（数据呈现）+ ADaM（分析数据集）须编码缺失——ADaM 要求预定义衍生，缺失原因用专用变量（如 `DTYPE`、缺失原因域）标记，使"为何缺失"可追溯。**CSR 透明（ICH E3）**：呈现主分析 + 全部敏感性分析、缺失模式图（按入组时间分布）、对 MAR 假设的违反说明，不隐藏 MI 假设。监管接受度：MI 在 MAR 下可接受，但须与 MNAR 敏感性分析并列；"MI + 参考基线填补 + tipping-point"组合同时满足统计严谨与监管接受。各地区对缺失数据方法的接受偏好与 CDISC 实施要求为动态项，以官方指南/原文为准（官方核实）。

### 4.5 统计编程与 TFL QC（workflow G / C）— ADaM 定义、可重现性与第三方编程交接
- **场景 / 角色**：统计编程 / DM — 试验锁库后编写 ADaM 分析数据集与 TFL（表格/图形/清单），需保证与 SAP 一致、可重现，并与外部编程供应商顺利交接。
- **正确处理路径**：① **ADaM 定义**：ADaM 数据集须按 SAP 预定义衍生（分析变量、缺失标记 `DTYPE`、伴发事件处理），与 SDTM 映射可追溯（缺失编码呼应 §4.4）；② **可重现性**：编程脚本版本化、随机种子固定、运行环境文档化，同一输入重跑得同一输出；③ **TFL 编程 QC**：双人独立编程（或编程 + 独立 QC 比对）、输出与 SAP / 壳规范一致、小数位 / 单位 / 口径统一；④ **与 SAP 一致性**：TFL 壳（shell）经统计与医学审核，主要分析 / 敏感性 / 亚组呈现口径与 SAP 一致；⑤ **供应商交接**：对外包编程须定义规格书、验收标准、交付物、稽查轨迹与知识转移，避免"黑箱交付"；⑥ 编程产物作为 CSR 支撑证据，纳入 eTMF。
- **关键要点**：ADaM 不是 SDTM 的简单变形——须承载分析语义与缺失原因；可重现性与独立 QC 是监管核查重点。
- ⚠️ ADaM / SDTM 实施指南版本、TFL 壳规范与 QC 要求为动态项，以 CDISC 现行标准与监管实施要求为准（官方核实）。

### 4.6 计算机化系统验证（CSV）与 EDC 上线前验证（workflow G / E）— 数据完整性从源头
- **场景 / 角色**：数据管理员 — EDC 建库后上线前需做 UAT、编辑检查验证，避免逻辑错误致关键字段无法录入。
- **正确处理路径**：① **CSV 原则**：EDC / IRT / ePRO 等系统须按预期用途与风险验证（IQ / OQ / PQ 或等效），配置、测试、放行留痕（呼应 §4.2 系统选择 / 验证）；② **建库与 UAT**：CRF 建模后做用户验收测试，覆盖编辑检查（逻辑 / 范围 / 必填）、跳转、衍生、导出；③ **编辑检查治理**：编辑检查规则须在 SAP / 数据管理计划预定义，变更走版本控制，避免"过度编辑检查"阻断合理录入或"不足"漏错；④ 上线前签署**系统放行（go-live）**审批，问题回溯至测试证据；⑤ 供应商系统须有供应商评估与持续运维 / SOP 衔接。
- **关键要点**：EDC 是数据完整性源头——验证与 UAT 不是一次性，须覆盖全生命周期配置变更。
- ⚠️ CSV 指南（如 GAMP5）、EDC 验证与审计轨迹要求为动态项，以监管计算机化系统验证现行指南为准（官方核实）。

### 4.7 数据治理（data governance）与数据质量框架（workflow G / H）— 从源到 CSR 的质量责任链
- **场景 / 角色**：数据管理员(DM) — 建立覆盖全试验的数据治理框架，确保数据可信、可溯、适用。
- **正确处理路径**：① **治理范围**：数据标准（CDISC SDTM / ADaM）、元数据、编码（字典版本）、数据流向与接口、质量度量；② **数据质量维度**：完整性 / 准确性 / 一致性 / 时效性 / 可追溯（ALCOA+，§4.1）；③ **角色与责任**：申办方对数据完整性负最终责任（§2.3），DM 与统计编程、IT、供应商分工明确；④ **流程控制**：DMP 规定采集、清理、编码、传输、留存、归档规则，变更走版本控制；⑤ **与技术底座衔接**：与 §4.6 CSV 衔接——系统验证是数据治理的技术底座；⑥ **质量度量**：用 KRI（§3.6）监测数据质量趋势，异常触发调查。
- **关键要点**：数据治理把"数据可信"从原则落到标准 + 责任 + 度量闭环；CSV 是底座、ALCOA+ 是属性、所有权是责任。
- ⚠️ 数据治理框架、CDISC 标准版本与数据质量标准要求为动态项，以 CDISC 现行标准与监管数据治理指南为准（官方核实）。

### 4.8 伴随用药（合并用药）采集与判定（workflow E / G）— concomitant medication 的记录与因果分层
- **场景 / 角色**：CRC / DM — 受试者试验期间使用方案外药物（伴随 / 合并用药），须规范采集、编码与对疗效 / 安全性的影响判定。
- **正确处理路径**：① **采集**：每访视系统采集药品名称、适应症、起止、剂量、与试验药时序（呼应 SDV §3.4）；② **编码**：按预设字典（如 MedDRA / WHODrug）标准化编码，版本固定（呼应 §4.7 数据治理）；③ **判定分层**：区分"允许 / 禁止 / 需记录"的伴随用药（方案规定），违禁药构成方案偏离（§6.2）；④ **对终点影响**：伴随用药可作混杂 / 合用药分析（与 §1.3 比较剂、DDI §1.5 衔接），须预设分析处理；⑤ **安全性**：伴随用药是 SUSAR 聚合与 AE 因果评估的协变量（§4.3 / §4.5）。
- **关键要点**：伴随用药不是"顺手记"——须标准化采集 + 编码 + 分层判定，方能支持安全性归因与疗效混杂控制。
- ⚠️ 伴随用药采集范围、编码字典版本与违禁药判定为动态项，以方案 / SOP 与现行数据标准为准（官方核实）。

### 4.9 盲态数据审查（BDR）与锁库前清理（workflow G / C）— 揭盲前的最终数据质量 gate
- **场景 / 角色**：统计 / DM — 数据库锁定（DBL）前组织盲态数据审查（BDR），确认数据完整、逻辑一致、可锁。
- **正确处理路径**：① **BDR 时机**：在 DBL 前、揭盲前，以盲态审查关键质量问题（缺失、逻辑、偏离、外部数据就绪）；② **审查内容**：数据完整性（关键字段）、编辑检查残留、外部数据（中心实验室 / 影像 / 第三方）对齐、编码一致性、偏离分类；③ **与 SAP 衔接**：确认分析集决策、缺失处理、伴发事件策略均已预定义并就绪（§4.4）；④ **行动**：BDR 发现的 open query / 偏离须关闭或记录理由，方可解锁；⑤ **盲态维护**：BDR 全程保持治疗组盲态，参与人员签保密 / 盲态承诺；⑥ **锁库**：DBL 须审批、版本锁定、解锁留痕（§4.2）。
- **关键要点**：BDR 是"揭盲前的最后一次数据体检"——以盲态确认质量而非提前看疗效；盲态承诺不可破。
- ⚠️ BDR 流程、锁库前清单与盲态维护要求为动态项，以现行 GCP 与 CDISC 数据标准为准（官方核实）。

### 4.10 临床试验系统网络安全与数据保护（workflow G / E）— EDC / IRT / ePRO 的系统安全
- **场景 / 角色**：IT / DM — EDC、IRT、ePRO、云端分析等系统承载敏感受试者数据，须满足网络安全与数据保护要求。
- **正确处理路径**：① **安全基线**：访问控制、加密传输 / 存储、审计日志、漏洞管理与渗透测试，叠加 §4.6 CSV 验证；② **数据最小化**：仅收集必要数据，去标识 / 假名化（呼应 §8.5）；③ **第三方 / 云**：与 EDC / CRO / 云签 DPA（§8.5），子处理者安全管理；④ **事件响应**：数据泄露须按 GDPR / 当地法通报（§8.5）；⑤ **与 GCP 衔接**：ALCOA+ 可追溯（§4.1）与系统安全共同保障数据完整。
- **关键要点**：网络安全是数据完整与隐私的交叉防线——验证(CSV) + 加密 + 访问控制 + 泄露响应缺一不可。
- ⚠️ 系统安全基线、加密与泄露通报要求为动态项，以监管网络安全指南与数据保护法现行原文为准（官方核实）。

### 4.12 电子数据迁移与系统退役（workflow G / E）— 系统下线不丢可追溯
- **场景 / 角色**：IT / DM — EDC / IRT 系统升级、退役或数据迁移时，须保证数据完整、可读、可追溯。
- **正确处理路径**：① **迁移**：预定义映射、验证（字段 / 编码一致性）、并行比对与回滚方案；② **退役**：数据导出为受控格式（如可长期读取的归档）、元数据与字典版本随附；③ **可追溯**：迁移 / 退役全程 ALCOA+（§4.1）、审计轨迹保留；④ **衔接**：与 §4.1.1 ISF / eTMF、§4.6 CSV 衔接——验证与归档留痕；⑤ **保留期**：退役后保留期须满足法规与合同（§4.1.1）。
- **关键要点**：系统退役不是"关服务器"——数据须可长期读取、可溯源、保留期达标。
- ⚠️ 数据迁移验证、归档格式与保留要求为动态项，以监管数据管理与 CSV 现行指南为准（官方核实）。

### 4.13 中心影像（central imaging）与独立影像评估（workflow G / E）— 影像终点的一致性保障
- **场景 / 角色**：影像 / 数据管理 — 以影像为主要终点（如肿瘤 RECIST、神经 / 心脏影像）的试验须中心化、独立影像评估以保证判读一致。
- **正确处理路径**：① **独立评审**：设 BICR / 独立中心影像（IRC），盲态、预先章程（呼应 `ref-regulatory-statistical.md` §5.14 BICR 章程）；② **采集标准**：统一序列 / 协议 / 质控、传输与归档（§4.1）；③ **偏倚控制**：与研究者评估一致性（Kappa）、盲态独立；④ **数据链**：影像数据纳入 ALCOA+（§4.1）、版本可追溯（QC §4.5）；⑤ **终点**：影像终点须预设判定标准（RECIST v1.1 等）。
- **关键要点**：中心影像是"一致性 + 独立性 + 标准采集"——避免研究者偏倚污染影像终点。
- ⚠️ 影像评估章程、采集标准与判定标准（RECIST 等）为动态项，以 RECIST / 监管影像终点现行指南为准（官方核实）。

### 4.14 量表 / 患者报告结局（PRO）的翻译与语言验证（workflow G）— 概念等价而非字面翻译
- **场景 / 角色**：数据管理 / 量表团队 — 跨国试验将既定量表 / PRO 翻译为非源语言须进行翻译验证（linguistic validation）以保概念等价。
- **正确处理路径**：① **流程**：前向翻译 - 回译 - 专家评审 - 认知访谈 - 定稿；② **概念等价**：非字面直译，文化 / 语义等价优先；③ **电子部署**：ePRO（§4.10）版本管理与多语言同步；④ **与 COA（§5.24）**：量表属临床结局评估工具，验证支撑终点可接受性；⑤ **记录**：各语言版本与验证报告归档。
- **关键要点**：量表翻译是"概念等价验证"而非字面翻译——认知访谈是等价性证据核心。
- ⚠️ 量表翻译验证方法与 COA 可接受性为动态项，以 FDA PRO 指南 / ISPOR 语言验证现行规范为准（官方核实）。

### 4.15 实验室正常值范围（LLN / ULN）与临床意义判定（workflow G / E）— 数值异常 ≠ 不良事件
- **场景 / 角色**：医学 / 数据管理 — 实验室参数须以中心特异正常值范围（LLN / ULN）判定异常与临床意义。
- **正确处理路径**：① **范围来源**：采用中心实验室或方案规定正常值范围，区分 LLN / ULN；② **分级**：异常（高 / 低）按量级与临床意义（CS / NCS）分级；③ **一致性**：多中心须统一判定规则，AE 编码（§4.7 MedDRA）一致；④ **与 AE**：异常值是否作为 AE / SAE（§5.4）取决于临床意义与研究判定；⑤ **与安全性**：汇总共性异常信号（§4.8）。
- **关键要点**：实验室判定是"范围 + 分级 + 临床意义"三元——数值异常 ≠ 不良事件，须临床判读。
- ⚠️ 正常值范围、异常分级与临床意义判定为动态项，以实验室与 AE 判定现行规范为准（官方核实）。

### 4.16 试验用药品编码与盲态供应（workflow E）— 分配隐藏的实体保障
- **场景 / 角色**：研究药师 / IRT — 盲态试验须对试验用药品编码、随机双盲包装与盲态供应，保证分配 concealment。
- **正确处理路径**：① **编码**：药物编码（药品编码）须按随机号盲态编码（与 §4.2.1 随机化衔接），标签去标识治疗组；② **包装**：双盲双模拟时安慰 / 活性外观一致；③ **供应**：IRT 依随机号发药，研究者不可知分组；④ **应急揭盲**：确需救治时按 §4.2.2 紧急破盲；⑤ **与计数**：编码药品账目（§4.2.4 / §3.23）一致。
- **关键要点**：药品编码 / 盲态供应是"分配隐藏"的实体保障——标签去标识 + IRT 发药 + 应急破盲。
- ⚠️ 药品编码、盲态包装与供应要求为动态项，以 GCP 与盲法设计规范为准（官方核实）。

## 5. Safety execution (workflow F · execution layer)

> The safety **regulatory chain** (SUSAR / RSI / DSUR regulations, RSI rules, oncology SUSAR aggregation, DSUR package) is in `ref-regulatory-statistical.md` §4; this section covers individual-case handling.

### 5.1 Separate six judgments first Within the protocol's collection scope → meets seriousness criteria → mild / moderate / severe → causal relation to investigational intervention → meets applicable RSI expectation → which recording / notification / expedited-report / cumulative / periodic path. Seriousness ≠ severity; causality ≠ whether to record; expectation & report path also depend on RSI version, jurisdiction, role, awareness date.

### 5.2 Individual-case handling loop Immediate medical treatment → obtain key facts → classify & medical assessment → report per applicable path → ongoing follow-up → assess impact on other subjects & the study overall → update documents / communication / risk control. Medical assessment checks temporal relation, alternative causes, concomitant treatment, de-/re-challenge, outcome, follow-up completeness. Overdue is judged by event nature, first-awareness date, jurisdiction, ethics, protocol, SOP; never backdate or rewrite the timeline; when overdue, record the delay truthfully, assess subject-protection impact, find root cause, take CAPA.

### 5.3 Medical monitoring & post-marketing The medical monitoring plan defines data source / frequency, risk triggers, eligibility questions, dose adjustment, hold rules, emergency escalation, PV interface, blinding boundary, decision records. Post-marketing puts spontaneous reports / studies / literature / regulatory information into one signal workflow: detect / verify / prioritize / assess / decide / risk-minimize / communicate / effectiveness-evaluate; report count cannot stand for incidence, nor can missing data imply "no risk found".

### 5.4 个例安全性报告时钟与材料（workflow F · 执行层） 报告路径分两段：研究者 → 申办方（个例 SAE 上报，时限与格式见方案 / SOP，常见为获知后 24 小时内，具体为动态项须官方核实）；申办方 → 监管与伦理（SUSAR 快速报告，时限与路径见 `ref-regulatory-statistical.md` §4.5）。研究者上报材料至少含：受试者识别、事件、严重性判定、起止时间、因果评估、预期性（对照 RSI / IB）、处理与转归；上报不逾期但也不补造时间线，逾期时如实记录延迟、评估对受试者保护影响、查根因、CAPA。上报责任 / 对象 / 表格以《药物临床试验期间安全性数据快速报告标准和程序》为准（动态项须官方核实）。

**妊娠作为安全性事件**：试验中确认的妊娠（即使研究者判与药物无关、受试者状态良好）通常**须按方案 / SOP 作为 SAE 或安全性事件向申办方报告**（妊娠本身是生殖安全重要信号，且须评估药物暴露风险）；申办方收到后须：① 记录并报告（路径见上）；② 提供妊娠登记 / 避孕与风险咨询；③ 追踪妊娠结局（流产 / 活产 / 先天异常），必要时按药物妊娠登记随访；④ 评估是否影响该受试者继续参与与用药；⑤ 若药物存在生殖 / 发育风险，妊娠事件须纳入 RSI / IB 安全性信息更新。妊娠是否按 SAE 报告、登记与随访要求为动态项，以方案 / SOP 与安全性数据快速报告标准为准（官方核实）。

### 5.6 生殖毒性综合评价与育龄 / 妊娠受试者管理（workflow F）— 生殖安全信号的截面
- **场景 / 角色**：PV / 医学 — 试验药物潜在生殖 / 发育毒性，须综合非临床生殖毒性、妊娠事件与风险评估。
- **正确处理路径**：① **非临床**：生殖毒性研究（生育 / 胚胎-胎仔 / 围产期）结果纳入 IB / RSI；② **临床避孕**：依 §5.8 载体 / 药物避孕要求，育龄期避孕与脱落期管理；③ **妊娠事件**：按 §5.4 报告、登记、随访，评估生殖风险；④ **暴露-效应**：生殖风险与暴露水平关联评估；⑤ **沟通**：IB / ICF 平衡告知生殖风险（§5.4、§5.5）。
- **关键要点**：生殖安全是"非临床 + 临床妊娠事件 + 避孕管理"的综合评价，而非单点信号。
- ⚠️ 生殖毒性研究要求、避孕时长与妊娠监测为动态项，以 ICH S5 与现行生殖安全指南为准（官方核实）。

### 5.7 孕妇受试者入组特殊考量（workflow F / D）— 妊娠人群的纳入边界
- **场景 / 角色**：研究者 / 医学 — 试验拟纳入孕妇（如妊娠相关适应症或必须含育龄外推），须特殊保护与设计。
- **正确处理路径**：① **纳入前提**：仅在科学必要且风险可控时纳入，避免"一刀切排除"致证据空白；② **风险收益**：强化获益-风险评估（§5.6 生殖安全）、独立伦理审查；③ **监测**：妊娠结局追踪（§5.4）、胎儿 / 新生儿监测、暴露登记；④ **与非孕区分**：孕妇数据单独分析，避免与育龄混淆；⑤ **衔接**：与 §2.2 / §3.5.1 同意、§5.8 生殖系风险衔接。
- **关键要点**：孕妇入组须"必要 + 强化保护 + 独立审查"——既补证据空白又防伤害。
- ⚠️ 孕妇受试者纳入条件、监测与伦理审查要求为动态项，以现行 GCP 与妊娠药物试验指南为准（官方核实）。

### 5.8 哺乳期受试者与哺乳安全性考量（workflow F / D）— 乳汁暴露量化与婴儿风险决策
- **场景 / 角色**：研究者 / 医学 — 试验药物可能经乳汁排泄或受试者处于哺乳期，须评估哺乳暴露风险与排除 / 中止决策。
- **正确处理路径**：① **排除 / 延期**：哺乳期通常排除或要求停止哺乳（依药物乳汁排泄与婴儿风险）；② **风险评估**：药物乳汁 / 血浆比（M/P）、婴儿暴露量、半衰期；③ **暴露处置**：意外哺乳暴露须上报与随访（§5.4）、婴儿监测；④ **协同**：与避孕 / WOCBP（§2.12）生殖风险管理协同；⑤ **标签**：影响说明书"哺乳期妇女用药"项。
- **关键要点**：哺乳风险是"乳汁暴露量化 + 婴儿风险"决策——排除优先、暴露有随访。
- ⚠️ 哺乳期排除 / 哺乳暴露评估与标签要求为动态项，以现行 GCP 与妊娠 / 哺乳用药指南为准（官方核实）。

### 5.9 受试者死亡与死亡报告流程（workflow F）— 无论因果均须报
- **场景 / 角色**：研究者 / PV — 受试者死亡（无论是否药物相关）须按时限上报与归因分析。
- **正确处理路径**：① **报告**：死亡作为 SAE（§5.4）须在规定时限（通常 24h 初步）上报申办方 / IRB / 监管；② **因果**：死因与试验药物 / 疾病关系判定（§5.2 个例处理）；③ **尸检**：依方案 / 家属同意，尽可能明确死因；④ **与汇总**：死亡事件汇总入 DSUR / CSR；⑤ **与随访**：退出后死亡仍须随访获知（§3.27）。
- **关键要点**：死亡报告是"时限上报 + 死因归因 + 尸检争取"——无论因果均须报。
- ⚠️ 死亡报告时限、尸检与归因要求为动态项，以 GCP 与 SAE 报告现行规范为准（官方核实）。

### 5.10 药物过量与意外暴露处置（workflow F）— 急救 + 上报 + 随访
- **场景 / 角色**：医学 / 研究者 — 受试者服药过量或意外暴露（如儿童误服、医护针刺）须按流程处置与随访。
- **正确处理路径**：① **处置**：依毒性 / 机制急救、去污染、对症、必要时解毒；② **报告**：过量 / 意外暴露常按 SAE（§5.4）上报，特别关注育龄 / 妊娠（§2.12）/ 哺乳（§5.8）；③ **随访**：临床监测至恢复、记录结局；④ **与依从（§3.25）/ 计数（§3.23）**：过量反映依从或可获得性问题；⑤ **与 RMP（§4.9）**：过量风险纳入风险管理。
- **关键要点**：过量 / 意外暴露是"急救 + 上报 + 随访"——与依从和风险管理联动。
- ⚠️ 过量 / 意外暴露处置与上报要求为动态项，以 GCP 与 SAE 报告现行规范为准（官方核实）。

### 5.5 特别关注不良事件（AESI）与 IB / ICF 安全措辞（workflow F / D） **AESI（特别关注的不良事件）** 是申办方基于"临床重要性 + 潜在关联 + 类效应信号"主动预设的安全性关注事件，**不依赖单个研究者的因果判定**——研究者判"可能无关"常见于个例盲态评估偏差，申办方须做独立盲态再评估，不能据此排除 AESI。列入判断：严重性信号（如小样本中出现含致死的同类事件）、类效应 plausibility、机制合理性 → 即使个例因果未定，也应列入并启用增强监测、加速报告、专项 IB/ICF 语言与研究者培训。**IB 描述（CIOMS VI / E2A 精神）**：客观陈述已观察到的事件（含致死例），明确"因果关系尚未确立 / 不能完全排除与试验药物的关联"，列风险最小化与监测要求；IB 须反映当前安全性认知。**ICF 描述（平衡伦理告知与脱落风险）**：诚实告知严重风险（含致死），但用中性因果措辞（"潜在关联 / 尚未确立 / 研究中"），避免"肯定由药物导致"的过度确定性——既满足伦理（重大风险必须披露），又不至引发不必要脱落。CIOMS VI、E2A 现行版本及各地区 IB/ICF 安全信息呈现的具体要求为动态项，以官方原文为准（官方核实）。

## 6. QA, QC & CAPA (workflow D)

QC is embedded in daily confirmation that specific steps / deliverables are correct; QA independently evaluates system effectiveness; sponsor supervision ensures delegated activities stay controlled. Deviations first assess impact on subject safety / rights, primary endpoint, randomization & blinding, data reliability, regulatory obligation, then classify & escalate; record fact / scope / time / immediate correction / root cause / CAPA / effectiveness / impact on analysis & report. Risk–quality chain: key data process → failure mode → risk → preventive & detective control → metric trigger → investigation → CAPA → effectiveness check → lessons learned. Risk is weighted by impact on subject protection & result reliability, not merely frequency. Audit evidence answers: what is required, what actually happened, how big the impact, why it happened, how to prevent recurrence. "More training" is usually a measure, not a root cause; seek root cause in process design / responsibility / workload / system / interface / knowledge / supervision / incentive.

### 6.2 方案偏离实例与伦理报告（workflow D） 偏离先评影响：受试者安全 / 权利、主要终点、随机与盲态、数据可靠性、合规义务；再分类（轻微 / 重要 / 重大）。常见实例：合格性违反（如超龄 / 不合入选标准入组）、访视窗超窗、给药剂量 / 时间偏离、漏做安全性检查、知情同意版本错误。重要 / 重大偏离按方案 / IRB SOP 及时报伦理（会议审查或快速审查视偏离性质与机构要求），报告材料含事实、范围、时间、即时纠正、根因、CAPA、对分析与报告影响；轻微偏离可定期汇总报告。分类与上报节奏为动态项须以方案 / IRB SOP 为准（偏离处理原则亦见 §6 总述）。

**PD 与 PV 的术语区分（现行中国 GCP 框架下）**：ICH E6(R2) 已将「Protocol Violation」统一纳入「Protocol Deviation」范畴，但国内部分机构仍沿用「PV（方案违背）」指代重大 / 实质性偏离。实操区分标准不在于字面，而在于**影响程度与处理层级**：① **PD（方案偏离）** 泛指任何对方案的偏离（含轻微、重要、重大）；② **PV（若机构沿用）** 通常特指**重大 / 重要偏离**（影响受试者安全、主要终点、随机盲态或数据可靠性），须升级 QA / 报伦理 / 根因 CAPA；③ 无论称 PD 或 PV，分类依据应是「对受试者保护 / 结果可靠性的影响」而非术语——避免以「PV 才上报、PD 不报」造成监管漏洞。机构术语习惯与上报阈值以 IRB SOP 与现行 GCP 为准（动态项须官方核实）。

### 6.3 数据完整性造假调查与上报（workflow D）— 先核实后定性，确认即果断
- **场景 / 角色**：申办方合规 / QM — 发现某中心 CRF 数据可疑系统性造假（录入雷同 / 虚构），如何调查、上报与保护数据完整性。
- **正确处理路径**：① 不臆断——先**核实**（源文件比对、现场 SDV、访谈），区分录入错误、培训问题与故意造假；② 若确认造假：立即**隔离受影响数据**，评估对受试者安全 / 主要终点 / 分析的影响；③ 上报：依严重性报伦理委员会、申办方安全 / 合规、必要时监管（数据造假属严重合规事件）；④ 纠正：重做受影响数据、撤回 / 更正、对中心启动质量 audit、必要时终止该中心入组；⑤ 根因与系统性 CAPA（监查加严、源数据核查、人员资质）；⑥ 全程留痕，保护举报人与受试者。
- **关键要点**：造假调查须"先核实后定性"，但一旦确认须果断隔离数据并上报——数据完整性是不可逾越底线。
- ⚠️ 造假上报时限与监管报告路径为动态项，以现行 GCP 与监管合规要求为准（官方核实）。

### 6.4 GCP 核查（inspection）准备与发现回复（workflow D）— 日常即可溯源，回复贵在诚实
- **场景 / 角色**：申办方合规 / QA — 面临监管 GCP 核查（inspection），如何准备溯源材料、回复核查发现（finding）。
- **正确处理路径**：① **准备**：确保源数据、ISF / eTMF、药品账目、SAE / SUSAR、监查报告可追溯（ALCOA+，§4.1），预演溯源路径；② **现场配合**：指定联络人、及时提供 requested 文件、如实记录核查员所见；③ **发现回复**：对 finding 分类（主要 / 一般 / 观察），逐条给**根因 + 纠正 + CAPA + 时限 + 证据**，不掩盖；④ 重大 finding（影响受试者安全 / 数据可靠性）须升级并评估对申报影响；⑤ 整改闭环跟踪至有效性验证，归档回复与证据。
- **关键要点**：核查准备的核心是"日常即可溯源"；finding 回复贵在诚实与闭环，而非辩解。
- ⚠️ 核查程序、finding 分类与回复时限为动态项，以 NMPA / FDA / EMA 核查现行规范为准（官方核实）。

### 6.5 CAPA有效性检查（effectiveness check）（workflow D）— 证明纠正真正防止再发
- **场景 / 角色**：质量管理(QM) — CAPA 实施后仍出现同类偏离，如何做有效性检查（effectiveness check）证明纠正措施有效。
- **正确处理路径**：① **定义成功标准**：CAPA 立项时即定有效性指标（同类事件再发生率、稽查发现关闭率）；② **验证时机**：在措施实施后设观察期（如 1–2 个监查周期 / 季度），用数据证明再发率下降；③ **方法**：趋势分析（KRI，§3.6）、重复稽查、源数据抽查、培训考核通过率；④ **未通过**：返回根因重做（§6 根因非"更多培训"），升级管理；⑤ 有效性证据归档于 CAPA 记录，作为质量体系成熟度的审计证据。
- **关键要点**：CAPA 的闭环终点是"有效性验证"而非"措施已执行"——无验证等于未关闭。
- ⚠️ CAPA 有效性观察期与指标要求为动态项，以质量体系与 GCP 为准（官方核实）。

## 7. Project governance & CSR execution (workflow G)

### 7.1 Unified fact base (Study Profile) At minimum: objective, phase, design, population, intervention & comparator, endpoints, sample size, region, timeline, key risks, key document versions, important decisions, open items. Protocol / IB / ICF / SAP / safety docs / ops plan / TFL / CSR / registration materials all update from this same base.

### 7.2 Governance & CSR writing landing Define decision tier, RACI, meeting cadence, escalation threshold, decision log, change control; risk = uncertain event not yet occurred, issue = event already occurred needing handling, change = baseline adjustment after evaluated & approved. Before CSR writing, lock data cutoff, document versions, analysis sets, blinded-review decision, key outputs; the report explains why the study was designed this way, how it was actually executed, what deviations occurred, what the results can / cannot answer, how the benefit–risk is understood (regulatory structure in `ref-regulatory-statistical.md` §5).

## 8. Cross-file dependencies & methodology QC (workflow H)

### 8.1 Cross-file dependency checklist
| Upstream change | Must-check downstream |
|---|---|
| Study objective / endpoint | protocol, SoA, CRF, SAP, sample size, TFL, CSR |
| Inclusion / exclusion | recruitment, screening, CRF, monitoring, medical monitoring, feasibility |
| Dose / administration | IB, ICF, supply, IRT, accountability, safety monitoring, SAP |
| Safety risk | IB / RSI, protocol, ICF, safety plan, training, monitoring, DSUR / CSR |
| Visit / procedure | SoA, ICF, CRF, budget, supply, lab manual, systems |
| Randomization / blinding | IRT, drug coding, permissions, emergency unblinding, data review, SAP |
| External vendor / data source | contract, quality agreement, interface, transfer spec, verification, archiving |
| Protocol amendment | change rationale & approval, enrolled / future subjects, ethics & regulatory, version switch, training, ICF, CRF / EDC / IRT, SAP, supply |
| Data-handling rule | DMP, SAP, dataset, TFL, CSR, traceable record |

### 8.2 Pre-delivery quality gate (for H judgment)
- [ ] The decision the user must make and the delivery use are explicit;
- [ ] Jurisdiction / date / product / phase / role confirmed or flagged as assumption;
- [ ] Confirmed facts, professional inference, unknowns, dynamic requirements are separated;
- [ ] Both subject-protection and result-reliability impacts are assessed;
- [ ] Conclusion does not exceed the strength the source can support;
- [ ] Key numbers / deadlines / thresholds / versions verified against current official or project source;
- [ ] Upstream–downstream consistency protocol—SoA—CRF—SAP—TFL—CSR checked;
- [ ] Advice includes owner, trigger, record, escalation, closure evidence;
- [ ] When data is missing, false precision stopped; list what is missing / who provides / impact;
- [ ] For formal / submission-level conclusions, document, data version, approval status are locked.

### 8.3 Methodology QC output shape (workflow H deliverable) Overall judgment (acceptable / acceptable with conditions / unacceptable) → issue list (evidence / impact / priority) → remediation plan → information gap → next quality gate. May consume sibling-skill real outputs for the cross-file consistency chain (e.g. cross-check the in-house competitor-landscape brief from `ct-registry` + `ct-safety` + `ct-literature` against protocol design claims).

## 9. Minimal answer template (across B / D / E / G / H)
1. **Conclusion**: one sentence on whether a judgment is possible now; 2. **Applicable boundary**: product / phase / jurisdiction / date / assumption; 3. **Methodology judgment**: objective / risk — evidence — control — decision rule; 4. **Upstream–downstream impact**: subjects / protocol / data / safety / operations / report; 5. **Immediate action**: concrete steps by priority; 6. **Information gap**: what is missing / who provides / impact; 7. **Official verification**: official site / search terms / fields to check for dynamic requirements; 8. **Next quality gate**: what must be met to proceed.

This file's core is to keep the agent always working the closed loop "clinical question — evidence — design — execution — data — interpretation — action", without memorizing every detail.
