---
file: reference-index.md
version: 2026-08-08
purpose: knowledge file-level routing table + series contract content — consult this table first to locate the topic file, then use search_refs.py to locate the line/section
auto_generated: false  # 2026-08-08: 合并 contract 文件后改为手动维护
---

# Reference Index — 文件级路由表 + 系列契约

> **用法**：收到提问 → 按关键词匹配下表「覆盖主题」列 → 用 `python3 scripts/search_refs.py "<关键词>" --context 3` 定位行段，或 Read 目标文件（单次 ≤60 行）。

## Clinical Operations 系列（ref-ops-*，执行层）

| 文件 | 覆盖主题（workflows） |
|---|---|
| `ref-ops-data.md` | ALCOA+ data chain, ISF retention, DCT compliance, biospecimen chain, CRF/lock, randomization/emergency supply/unblinding, drug temperature, drug accountability, query, missing-data imputation; statistical programming/TFL QC, CSV validation, data governance, concomitant meds, BDR, cybersecurity, data migration, central imaging, PRO translation, lab normal ranges, drug coding blind supply [C, D, E, G, H] |
| `ref-ops-design.md` | Design decision loop, design-choice comparison, inclusion/exclusion/endpoint/control, ct-series integration anchors; early-phase, DDI R-value, pediatric dose/Assent, CRM/BOIN, hepatic/renal impairment, PopPK/PK-PD, geriatric, PGx, abuse potential, photostability, pediatric formulation, QTc, bioanalysis [B, C, D] |
| `ref-ops-execution.md` | QTL, GCP training, contract/insurance, re-consent, SIV, recruitment/retention, site closeout, IRB composition, drug return, medical devices, compliance, recruitment ads, discontinuation/withdrawal; cross-file dependency checklist, pre-delivery quality gate, methodology QC output, minimal answer template [B, D, E, G, H] |
| `ref-ops-gcp-site.md` | Ethics judgment order, informed consent as a continuous process, delegation does not transfer accountability, role responsibilities, WOCBP pregnancy screening; institution filing/PI change, feasibility, monitoring, SDV, protocol amendment, ICF execution, KRI/RBM, adaptive FIH ethics, single-arm external control, cell/gene LTFU, compensation, depot logistics, institution change, CRO audit [D, E] |
| `ref-ops-safety.md` | Six-judgment, individual-case handling loop, medical monitoring, SAE clock, reproductive toxicity, pregnancy/lactation, death report, overdose handling, AESI; deviation examples/ethics reporting, fraud investigation, GCP inspection prep, CAPA effectiveness; unified fact base, decision hierarchy/RACI, risk-issue-change, CSR writing implementation [D, F, G] |

### Clinical Operations 系列契约

#### 可做 / 不可做

- **可做**：解释设计/执行/数据/安全/质量/运营的共性执行逻辑；把模糊问题转化为决策问题、信息缺口、行动步骤、风险控制和质控门；审查方案/CRF/监查计划/数据流/供应链/CSR 是否形成上下游闭环；为培训/SOP/项目复盘和方法学 QC 提供审查维度。
- **不可做**（动态项须官方核实）：不单独确认现行法规/指南及其实施状态；不单独确认法定报告期限、固定阈值、表单/数据库版本；不单独确认中美欧日申报路径；不单独确认特定项目的方案/IB/ICF/SAP；不单独确认具体产品的剂量、洗脱期、样本量、非劣效界值或安全结论。这些按来源层级走 `ref-regulatory-versions.md` 官方核实。

#### 来源层级

1. 辖区现行法律法规和强制性监管文件；2. 已实施的 ICH/官方指南；3. 研究特定文件（方案/IB/ICF/SAP）；4. 机构控制文件（SOP/方案）；5. 本参考（解释、串联、风险框架）。本文件不把"行业实践"改写为"监管要求"。

## Regulatory & Statistical 系列（ref-reg-*，证据层）

| 文件 | 覆盖主题（workflows） |
|---|---|
| `ref-reg-cn.md` | China regulatory routing basis, safety document chain, CTA/IND & communication meetings; human genetic resources, cross-border data/GDPR/DPO, publication transparency, MSL compliance, multi-region ethics, DPIA, AI ethics, meeting prep, pause/clinical hold, data export, result registration; registration transparency, accelerated approval, IPD sharing, data protection period [A, D, G] |
| `ref-reg-gcp-version.md` | E6(R2)/E6(R3) version judgment, transition-period handling [A, D] |
| `ref-reg-safety.md` | SUSAR/RSI/DSUR loop, RSI rules, oncology SUSAR aggregation, DSUR E2F, SUSAR expedited-report clock, signal detection PRR/ROR, ICSR chain, safety database, RMP, PASS [F] |
| `ref-reg-stats.md` | Estimand E9(R1), analysis sets/missing, non-inferiority/multiplicity, interim analysis/DSMB, Bayesian adaptive, synthetic control, biomarker, rare-disease power prior, SSR, DSMB charter, RWE [C] |
| `ref-reg-submission.md` | E3 main chain & consistency chain, results presentation & common distortions, submission-level quality gate; CTD five modules, eCTD submission prep; conditional/accelerated approval, MCID, biomarker subgroup, label balance, US-China dual filing bridge, AI imaging read, biosimilar immunogenicity, gene-therapy germline; Master Protocol multiplicity, PRO primary endpoint, HEOR/QALY, orphan drug, vaccine bridging, BICR charter, MAMS; RWE label expansion, CEC, biosimilar bridge, RFE, BE, compassionate use, PIP, SAR, COA, genotoxicity [A, B, C, F, G] |
| `ref-regulatory-versions.md` | Regulatory version snapshot: ICH/NMPA/CDE controlled quick-reference, version applicability routing |

### Regulatory & Statistical 系列契约

#### 可做 / 不可做

- **可做**：按问题定位法规/指南/条款；解释每份文件在安全/设计/统计/GCP/报告/申报中的角色；提炼不依赖时效性的核心方法学原则；构建「结论—依据—条款—适用条件—行动」证据链；识别本文件历史版本/示例/译文与当官方文件的差异。
- **不可做**（须官方核实）：当前有效版本、ICH Step 状态、中国实施状态与过渡；法定报告时限、申报入口、表单、系统、数据标准；文件是否正式发布/征求意见/被替代/废止/撤销；产品/适应症/人群/辖区/日期特定要求；对外/伦理/监管沟通/检查/申报级别结论。

#### 来源层级

1. 辖区现行法律法规和强制性监管文件；2. 该辖区已实施的 ICH 指南；3. 监管当局正式发布的一般/产品/治疗领域技术指导原则；4. 项目批准文件（方案、IB、ICF、SAP、安全计划、正式监管沟通）；5. 征求意见稿/Q&A/培训/示例（仅辅助，须标注状态）；6. 方法学文献与经过验证的实践知识。ICH Step 4 ≠ 自动实施；译文仅供参考，关键词须同时核对 ICH 原文和中国实施文件。来源冲突时不机械选"最高层级"——先核对范围/版本/辖区/阶段/项目约束并记录采用依据。

#### 适用性路由表

| 文件 | 主要用途 | 局限 |
|---|---|---|
| CDE《抗肿瘤药物临床试验中 SUSAR 分析与处理》 | 肿瘤 SUSAR 累积分析、信号、监管沟通 | 治疗领域指南；勿将其建议阈值写成通用法定标准 |
| CDE《研究者手册中安全性参考信息（RSI）撰写》 | RSI 纳入/呈现/版本/变更/质量 | 当前版本与实施状态：CDE 官网核实 |
| ICH E2F / DSUR | DSUR 范围/周期/结构/总体安全性评估 | 中国报送周期/入口/区域增补：NMPA/CDE 核实 |
| ICH E3 | 单 CSR 结构/数据呈现/附录 | 以当前 ICH 官方原文为关键解读依据 |
| ICH E6(R1) | 理解经典 GCP 责任与基本文件框架 | 历史版本；非唯一现行 GCP 基础 |
| ICH E9 | 随机化/偏倚/样本量/分析集/缺失/多重性 | 须与 E9(R1) 和当前主题指南配合使用 |
| ICH E9(R1) | 估计目标/伴发事件/估计/敏感性 | 勿将估计目标等同于终点/分析集/填补 |
| ICH M4(R4) | CTD 五模块/粒度/生命周期 | 模块 1 和电子申报为区域特定 |
| ICH M4E(R2) | 临床概述/临床摘要/模块 5 CSR | 非单 CSR 模板；须与 E3 配对 |
| ICH M4Q(R1) / M4S(R2) | 质量/非临床数据组织 | 须与当前 Q 系列/S 系列和区域要求配对 |

## Interaction style（跨切面）

| 文件 | 覆盖主题（workflows） |
|---|---|
| `ref-interaction-style.md` | Clarification gate (gate 0), user tone writing (workflow I), local user memory (workflow J), official retrieval & conflict handling (workflow A), privacy & delivery checks |

---

> **维护说明**：`ref-ops-contract.md` / `ref-reg-contract.md` 已于 2026-08-08 合并进本文件。编辑 contract 内容时直接编辑本文件的对应小节。`ref-interaction-style.md` 下的检索流程（§5）仍可直接编辑。
