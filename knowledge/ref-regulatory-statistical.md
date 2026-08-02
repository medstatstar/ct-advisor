---
file: ref-regulatory-statistical.md
version: 2026-08-02
tier: A
source_urls:
- https://www.ich.org
- https://www.nmpa.gov.cn
- https://www.cde.org.cn
- https://www.fda.gov
last_verified: 2026-08-02
next_refresh: 2027-02-02
serves_workflows: [A, C, F, G]
adapted_from: github.com/A-xin946/clinical-trial-advisor (not verbatim)
note: 不存全文法规；版本/状态/截止日/程序项须实时官方核实
---

# Regulatory & Statistical Foundation Reference

> **Source & refactor note**: Content adapted from the third-party skill `github.com/A-xin946/clinical-trial-advisor` (adapted_from) and reorganized to fit ct-advisor's own architecture — **not a verbatim copy**. This file focuses on **"on what basis, how documents relate, how normative requirements land"** — ICH / NMPA / CDE document location, statistical & estimand principles, safety regulatory chain (SUSAR / RSI / DSUR), CSR regulatory structure, official-currency verification. The "**how to do it**" content (trial design / operations / GCP execution / documents & data) lives in `ref-clinical-operations.md`; the two cross-link by topic and do not duplicate. This file stores no full-text regulation and does not, by static content, confirm current version / status / deadline / procedure.

> **Duty domain**: serves workflows `A` (explain & locate evidence), `C` (statistics & estimands), `F` (safety & DSUR), `G` (documents & reports). **ct-series integration anchor**: workflow `C` hands off to `ct-samplesize` once sample-size parameters are complete; workflow `F` may combine `ct-safety` real FAERS signals; workflow `A` China filing may combine a competitor landscape stitched in-house from `ct-registry` + `ct-safety` + `ct-literature`.

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

## 3. Statistics & estimands (workflow C)

### 3.1 Estimand chain (ICH E9(R1)) `trial objective → clinical question → estimand → main estimation method → sensitivity estimation method → estimate & interpretation`. An estimand defines at least: ① treatment condition; ② target population; ③ variable or endpoint; ④ intercurrent event and its strategy; ⑤ population-level summary quantity. Common intercurrent-event strategies: treatment-policy, hypothetical, composite-variable, while-on-treatment, principal-stratum; different events may use different strategies, each choice mapped to a clear clinical question. Distinguish: stopping treatment / taking rescue / crossover / death may be intercurrent events; dropping out or not collecting data creates missingness; sensitivity analysis addresses robustness of the main analysis' key assumptions under the *same* estimand; supplementary analysis answers a *different* question and cannot masquerade as sensitivity. The estimand must be written back into the protocol, data collection & follow-up must support it, the SAP must give a reproducible estimation method, and the CSR must interpret under the same clinical question.

### 3.2 Analysis set, missingness & minimal sample-size inputs
- Analysis set: Intention-To-Treat (ITT) / Full Analysis Set (FAS) preserves randomization benefit but "ITT" cannot replace a complete estimand; Per-Protocol (PP) supports compliance & non-inferiority robustness, post-hoc exclusion may bias; safety set organized by actual exposure, with pre-specified switch & multiple-exposure rules.
- Missingness: an intercurrent event changes *what* is estimated; missingness means data needed to estimate that target was not observed; first define the estimand and the data that should keep being collected, then discuss missingness mechanism, main estimation and sensitivity.
- **Minimal sample-size inputs**: main estimand and superiority / non-inferiority / equivalence / precision objective; main variable, analysis method and expected effect; standard deviation / event rate / risk ratio / correlation structure; one- or two-sided alpha, power, allocation ratio; multiplicity, interim analysis, clustering / repeated measures; dropout, unevaluable, compliance, event maturity. **Sample size is a function of assumptions, not a fixed truth; missing key parameters → give only the computation framework, parameter table and scenario analysis, no pseudo-precise number.**
- **Handoff to ct-samplesize**: once parameters are complete, route via workflow `C` to `ct-samplesize` for actual computation (see `scripts/workflows.json` `integration.sample_size_handoff`); this skill does not compute n in-house.

### 3.3 Non-inferiority, multiplicity & subgroups
- Non-inferiority margin must be argued from historical control effect and clinically acceptable loss; check constancy, assay sensitivity, compliance, crossover, rescue therapy, and the interpretation when FAS/ITT-class vs PP results disagree.
- Primary endpoint / dose / group / time point / interim decision together form multiplicity, requiring pre-specified error-rate control.
- Subgroups emphasize consistency & interaction; "one significant, one not" does not automatically prove a difference.

### 3.4 期中分析、无效性边界、DSMB 与计划偏离解释（workflow C / D） 预设期中分析须区分**信息时间**（实际事件/预设事件）与日历时间：若按事件数预设，α 消耗边界本就是信息分数的函数，在 0.6 信息分数处运行仍**在设计内**；但事件不足会降检验效能，更稳妥是延长入组/随访达目标事件数以保效能，而非仅提前跑期中。**无效性（futility）分析**跨越边界时结论有效但更不确定，关键是不事后改边界。**DSMB** 在事件数不足/外部标准治疗更新等情境下可建议继续——此属**计划偏离**，处理原则是**透明记录而非掩盖**：记录原设计假设（事件数、α 消耗函数）、实际偏离（信息分数、SOC 更新）、DSMB 书面风险/受益再评估理由、提交方案修正/偏离报告给监管；向监管解释「保持试验完整性」靠**预设偏离处理 + 完整文档**（可经 Type B 沟通预先报备），说明 α 如何保留、分析计划如何修订。α 消耗函数选择、期中时机规则、计划偏离的监管报告要求为动态项，以现行 GCP/统计规范为准（官方核实）。

**DSMB / iDMC 成员利益冲突（COI）的事后发现**：① 若事后发现成员存在潜在 COI（如任申办方其他在研项目 SAB、声誉关联），须**评估其是否实质影响已完成的期中分析独立性**——一次性、低关联（unpaid、无直接经济利益）通常不构成对已完成数据的自动失效，但须**留痕披露并请独立方复核**；② 立即补 COI 声明、将该成员移出后续 DSMB 或设防火墙（不参与相关表决）、记录时间线；③ 已完成的期中分析数据有效性：若 COI 未实质介入决策（有独立统计中心、盲态数据、书面记录可证），通常**仍有效**，但须在监管申报中披露该关系与纠正措施以保证可接受性；④ 重大未披露 COI 且介入关键决策时，可能须重做或解释。DSMB COI 披露与数据有效性判定要求为动态项，以 ICH E6(R3) 独立数据监查完整性要求与现行规范为准（官方核实）。

### 3.5 贝叶斯自适应设计：先验、停止边界与 α 等价（workflow C / B）— 贝叶斯期中停止与频繁主义把握度的监管论证
- **场景 / 角色**：生物统计师 — 计划贝叶斯自适应设计（贝叶斯期中有效性 / 失效 stopping、剂量调整），需论证其与频繁主义 α 消耗的等价性以获得监管接受。
- **正确处理路径**：① **先验选择**：明确先验类型（信息性 / 弱信息性 / 经验性）、来源与合理性，避免先验过强导致结果偏离；敏感性分析检验先验稳健性；② **贝叶斯停止边界**：预设基于后验概率的 stopping rule（如 P(优效) > 阈值 或 P(无效) > 阈值），并说明其频率学性质；③ **α 等价论证**：用**模拟（operating characteristics）**展示该贝叶斯设计在零假设下的假阳性率（type I error）受控、与预定 α 一致——监管通常要求"贝叶斯框架但家族错误率受控"；④ 与 DSMB / 期中分析（§3.4）衔接：贝叶斯期中仍须预设信息披露与盲态维护；⑤ **监管沟通**：Pre-IND / Type B 预先就设计与 α 等价论证达成共识，尤其适应性 / 贝叶斯改动预分类（呼应 `ref-clinical-operations.md` §3.7）。
- **关键要点**：贝叶斯设计不等于"免 α 控制"——须用模拟证明假阳性受控且与预定 α 等价；先验与停止规则须预设、透明、可复现。
- ⚠️ 贝叶斯停止阈值、先验惯例、α 等价接受标准与模拟要求为动态项，以 FDA / EMA / NMPA 适应性设计现行指南为准（官方核实）。

### 3.6 合成对照（synthetic control）构建与偏倚控制（workflow C / B）— 与历史 / 外部对照的区别及监管边界
- **场景 / 角色**：生物统计师 — 单臂试验中用合成对照（synthetic control，基于历史 / 外部数据建模构造的虚拟对照臂）替代同期对照，需说明构建法与偏倚控制。
- **正确处理路径**：① **与历史 / 外部对照区别**：合成对照通过统计模型（如倾向评分、贝叶斯层次模型、混合数据方法）将多个历史 / 外部个体"合成"为一个虚拟对照群，可减少但**不消除**选择偏倚；② **可比人群**：合成对照的协变量（瘤种 / 线数 / 基线）须与试验臂预先对齐，建模协变量写死于 SAP；③ **偏倚控制**：时间趋势（同期性）、测量一致性（RECIST 版本 / BICR）、未观测混杂——用敏感性分析 / 阴性对照检验方向；④ **透明报告**：预设"合成对照局限性"章节（呼应 `ref-clinical-operations.md` §3.8 外部对照 5 点）；⑤ **监管接受**：合成对照证据等级通常低于同期 RCT 对照，须尽早 Pre-IND 沟通且用于支持性而非替代关键证据。
- **关键要点**：合成对照是外部对照的"建模增强版"，偏倚风险仍在；须预先规定构建法与敏感性，且通常仅作支持性证据。
- ⚠️ 合成对照接受度与方法要求为动态项，以 CDE / FDA 外部对照与适应性设计现行指南为准（官方核实）。

### 3.7 诊断生物标志物 / 预后 / 预测性生物标志物验证（workflow C）— 与 PRO 验证类比的证据等级
- **场景 / 角色**：生物统计师 / 医学 — 以诊断 / 预后 / 预测性生物标志物作终点或富集因子，须验证其分析 / 临床有效性。
- **正确处理路径**：① **区分三类**：诊断（detect disease）、预后（predict course）、预测（predict treatment effect）——预测性标志物须证明与**治疗反应**的相互作用，非仅关联；② **分析验证**：检测的准确性、精密度、特异性（与 §4.4 / CDISC 衔接）；③ **临床验证**：预后 / 预测价值须在独立队列验证，避免过拟合；④ **监管接受**：作主要终点或富集须满足验证框架（类比 §5.10 PRO 验证），预设 cutoff 与判定；⑤ 伴随诊断（companion diagnostic）须与药物同步获批路径。
- **关键要点**：预测性 ≠ 预后性——只有证明治疗-标志物交互才有富集 / 预测价值；须独立验证。
- ⚠️ 生物标志物验证指南、cutoff 与伴随诊断要求为动态项，以 FDA / EMA / NMPA 生物标志物与伴随诊断现行指南为准（官方核实）。

### 3.8 罕见病贝叶斯设计与历史数据借力（power prior）（workflow C / B）— 小样本下的证据增强
- **场景 / 角色**：罕见病专家 / 生物统计 — 罕见病微小样本试验用贝叶斯设计借力历史 / 外部数据（power prior）增强证据，须论证借力权重。
- **正确处理路径**：① **power prior**：以历史数据作先验，预设折扣因子（discounting）控制历史与当前试验的异质性影响；② **借力论证**：须说明历史数据可比性（人群 / 设计 / 终点），过强借力掩盖当前数据风险；③ **频率学性质**：用模拟证明贝叶斯设计假阳性 / 把握度受控（呼应 §3.5 α 等价）；④ **监管沟通**：罕见病小样本设计须 Pre-IND 预先认可；⑤ 与 §5.12 孤儿药 / 自然史外部对照衔接——历史数据借力是外部对照的贝叶斯形式。
- **关键要点**：历史数据借力可缓解小样本，但折扣因子须透明预设，避免"借来"虚假 precision。
- ⚠️ power prior 折扣惯例、罕见病贝叶斯接受度为动态项，以 FDA / EMA / NMPA 罕见病与贝叶斯设计现行指南为准（官方核实）。

### 3.9 样本量重估（SSR）与期中再估计（workflow C）— 预设规则下的 sample size re-estimation
- **场景 / 角色**：生物统计师 — 试验进行中基于累积数据做样本量重估（SSR），须控制一类错误并预先规定。
- **正确处理路径**：① **两类 SSR**：盲态 SSR（基于预估参数如方差 / 事件率更新，不改治疗效应假设，通常不加 α 惩罚）与**疗效驱动 SSR**（须预先规定且与 α 消耗 / 错误率控制挂钩，常用对疗效设盲的设计避免破盲偏差）；② **预设**：SSR 触发条件、时机（信息分数）、重估方法、上限与边界须在 SAP / 方案预设，不得事后随意调整；③ **错误率**：疗效驱动 SSR 若依赖中期疗效须用 α-spending / 自适应框架保证 FWER 受控（呼应 §3.3 / §3.5）；④ **沟通**：适应性 SSR 须 Pre-IND 预先认可；⑤ **透明**：CSR 须报告 SSR 决策与对把握度的影响（§5.2 / §5.3）。
- **关键要点**：SSR 可提升效率但须"预设 + 错误率受控 + 透明"；盲态 SSR 与疗效驱动 SSR 的 α 处理不同。
- ⚠️ SSR 接受度、α 控制方法与重估边界为动态项，以 FDA / EMA / NMPA 适应性设计与统计学现行指南为准（官方核实）。

### 3.10 DSMB 章程与运作（workflow C / D）— 独立数据监查委员会的治理
- **场景 / 角色**：生物统计 / 申办方 — 设 DSMB / iDMC 监督安全性与有效性，须有章程、独立性与暂停 / 终止建议机制（呼应临床 §3.7 iDMC、§3.4 DSMB COI）。
- **正确处理路径**：① **章程（charter）**：成员独立性（与申办方运营隔离）、运作规则、揭盲程序、向 IRB / 申办方报告义务；② **运作**：预设会议节奏、信息供给（盲态 / 非盲）、决策（继续 / 暂停 / 终止 / 修改）与建议形式；③ **暂停 / 终止**：DSMB 建议试验暂停 / 终止的触发与执行（呼应 §3.4 计划偏离解释）；④ **COI**：成员 COI 披露与防火墙（§3.4 事后发现）；⑤ **监管沟通**：DSMB 建议与偏离须透明记录并向监管解释（§3.4）。
- **关键要点**：DSMB 价值在独立性与预设规则——章程、独立性、书面建议构成可核查的治理。
- ⚠️ DSMB 章程要素、运作规则与暂停 / 终止建议的接受度为动态项，以 ICH E6(R3) 与现行 DSMB 运作规范为准（官方核实）。

### 3.11 RWE 研究设计与偏倚控制（workflow C / 注册）— 前瞻性 / 回顾性 RWE 的生成
- **场景 / 角色**：RWE / 注册 — 用真实世界数据生成证据（如 RWE 支持标签、外部对照、上市后），须设计研究并控制偏倚（呼应 §3.8 外部对照、§5.16 标签扩展）。
- **正确处理路径**：① **设计类型**：回顾性队列 / 巢式 / 外部对照臂、前瞻性真实世界研究、登记库、目标试验模拟（target trial emulation）；② **偏倚控制**：选择偏倚（PS / MAIC / 熵平衡）、混杂（敏感性分析 / 阴性对照）、时间趋势（同期对照）、测量一致性；③ **数据质量**：RWD 适用性（完整性 / 准确性 / 时效性）评估（呼应 §3.8）；④ **预先注册**：方案预注册与监管事先认可（Pre-IND）；⑤ **透明**：预设局限性章节与偏倚方向应激检验。
- **关键要点**：RWE 证据强度取决于设计预先性与偏倚可控——非预设 / 非透明的 RWE 不被监管接受。
- ⚠️ RWE 研究设计接受度、偏倚控制方法与数据质量要求为动态项，以 FDA / EMA / NMPA RWE 与真实世界研究现行指南为准（官方核实）。

## 4. Safety regulatory chain (workflow F)

> Individual-case handling **execution** is in `ref-clinical-operations.md` §5; this section covers the regulatory chain & cumulative evaluation.

### 4.1 SUSAR / RSI / DSUR loop `individual SAE → causality → expectation / RSI version → SUSAR expedited report → similar-event aggregation → signal → risk characterization → document & measure update → DSUR cumulative evaluation`.

### 4.2 RSI rules RSI sits in the IB and judges the expectedness of a suspected serious adverse reaction; it is not a full safety summary of the investigational drug, nor may its scope be widened to reduce SUSARs. RSI check: has the event already been observed with the investigational drug (mechanism / class speculation alone is insufficient); is there sufficient medical evidence for a reasonable causal relation; a single event is usually insufficient to include (unless strong evidence), repeat occurrence does not automatically mean include; SAEs whose relevance cannot be evaluated are handled with caution; fatal events of a not-yet-marketed investigational drug usually should not be written into RSI; an individual more severe / specific / frequent than the RSI description may still be unexpected; RSI uses MedDRA SOC / PT with an explainable denominator, not over-broad terms that hide risk; different indications / populations may be presented separately; when no expected serious adverse reaction yet exists, still keep an independent RSI section and explain. RSI change needs medical basis, change control, implementation date, impact assessment, version traceability, MedDRA impact; urgent safety information does not wait for the annual update — go through IB other-section update / protocol ICF amendment / urgent measure / regulatory communication.

### 4.3 Oncology SUSAR aggregation & signal action Cumulative analysis across at least six dimensions: count & incidence, severity & outcome, medical specificity, causality, similar-event aggregation (MedDRA / SMQ / predefined concept sets), concomitant medication. CDE oncology guidance suggests: early cumulative 2 cases (especially 3+) of the same PT / concept warrants high attention, and certain mechanism-related or severe individual cases trigger deep evaluation even at 1 case — **this is a signal-detection hint, not a universal statutory threshold**. After signal confirmation, actions: add visits / monitoring / pre-medication / dosing speed / stop-and-rechallenge rules; amend protocol / ICF / IB-RSI / monitoring / medical monitoring; re-train; assess enrollment / dosing / dose / termination hold; if it may significantly affect benefit–risk, follow paths like "other potential serious risk safety information" with regulatory communication; decision / owner / date / affected trials / effectiveness check feed the closed loop.

### 4.4 DSUR (ICH E2F) DSUR centers on the same active ingredient's global development safety information, linking reporting period, cumulative exposure, individual & cumulative, important findings, overall safety evaluation, important risks & conclusions. Core: `new info this period → compare with prior → does risk change → does benefit–risk change → actions taken / planned`. Before writing, lock DIBD / DLP / period / applicable RSI-IB version, global trial scope & responsibility, prior DSUR & regional addenda, safety database / SAR line listings / SAE cumulative / cumulative exposure, clinical / non-clinical / literature / post-marketing / regulatory measures, data cutoff & reconciliation status; for missing data make a gap table (owner / deadline / impact), never use "no obvious risk seen" to mask unreceived / uncoded / unfollowed / unreconciled data. Before submission check: no conflict in DIBD / DLP / period / version; global list consistent with exposure / line listing / cumulative scope; RSI change / signal / regulatory measure / risk control coherent; numbers / terms / MedDRA version / product name / important risks consistent; conclusion does not exceed evidence strength; regional deadline / addendum / entry verified against official original.

### 4.5 SUSAR 快速报告时钟与路径（workflow F） 申办方收到 SUSAR 后向监管与伦理快速报告：致死或危及生命者一般 7 日内首次报告、其他一般 15 日内（具体时限、对象、路径、表格以《药物临床试验期间安全性数据快速报告标准和程序》为准，动态项须官方核实）；首次报告后必要时补充随访报告。SUSAR 触发以 RSI（IB）预期性判定为前提（见 §4.2），因果与预期性评估须留痕；国外中心 SUSAR 同样纳入申办方全球安全信息流，按中国要求同步报告。报告时限按"首次获知日期"起算，不得补造时间线；逾期如实记录、评估受试者保护影响、查根因、CAPA（执行层见 `ref-clinical-operations.md` §5.4）。**报告对象（三接收方）**：申办方须将 SUSAR 快速报告至①国家药监局药品审评中心（CDE）②省级药品监督管理部门③伦理委员会（涉及该 SUSAR 的相关中心伦理 / 总体伦理视情形）。国外中心发生的 SUSAR 同样纳入全球安全信息流，按中国要求同步向上述三方报告。具体接收方范围、路径与表格以《药物临床试验期间安全性数据快速报告标准和程序》为准（动态项须官方核实）。

### 4.6 信号检测与 disproportionality 方法（PRR / ROR）（workflow F）— 累积信号量化的统计工具
- **场景 / 角色**：PV / 生物统计 — 用 disproportionality 分析（PRR、ROR、EBGM 等）从自发报告 / 累积 SAE 中量化信号，支持 SUSAR 聚合与信号判定（呼应 §4.3 肿瘤 SUSAR 聚合）。
- **正确处理路径**：① **方法**：比例失衡分析（PRR 报告比值比、ROR 比值比、IC 信息成分、EBGM 经验贝叶斯）量化"该药-事件"共现超出背景的程度；② **信号 ≠ 因果**：disproportionality 仅提示信号，须临床 / 机制评估（因果、预期性、严重性）后才进入 RSI / IB 更新与监管沟通（§4.2 / §4.4）；③ **数据来源**：自发报告库、SUSAR 累积、文献，须数据完整与编码一致（MedDRA）才可计算；④ **阈值惯例**：各方法常用信号判定阈值（如 PRR≥2 且 χ²≥4、ROR 95%CI 不含 1）为**参考惯例而非法定标准**；⑤ **与 §4.3 联动**：肿瘤 SUSAR 聚合的"2 例 / 3 例"提示可借 disproportionality 量化增强。
- **关键要点**：disproportionality 是信号筛选工具而非因果证据；阈值只是参考，最终靠医学判断 + 监管沟通闭环。
- ⚠️ disproportionality 方法选择、信号阈值惯例与监管接受度为动态项，以 ICH E2E / CIOMS 信号检测与各国 PV 现行指南为准（官方核实）。

### 4.7 个例安全报告（ICSR）处理链与 MedDRA 编码（workflow F）— 从个例到数据库
- **场景 / 角色**：PV — 个例安全报告（ICSR）从采集、MedDRA 编码、录入安全数据库到一致性核查的全流程（呼应临床 §5.4 个例时钟）。
- **正确处理路径**：① **采集与录入**：个例信息结构化录入，因果 / 预期性评估（§4.2 RSI）；② **MedDRA 编码**：事件按 MedDRA 编码（SOC / PT），编码一致性影响聚合与信号（§4.3）；③ **安全数据库**：ICSR 入数据库，与 SUSAR / 定期报告 / 文献整合；④ **一致性**：数据库与 CSR / SAE 列表 / line listing 一致（§5.2 / §5.3）；⑤ **时限**：个例上报时限依 §4.5 / §5.4。
- **关键要点**：ICSR 是安全信息的原子单元——编码一致性与数据库整合决定后续聚合与信号的可靠性。
- ⚠️ ICSR 处理时限、MedDRA 编码与安全性数据库要求为动态项，以《药物临床试验期间安全性数据快速报告标准和程序》与各国 PV 现行规定为准（官方核实）。

### 4.8 安全性数据库与信号管理工作流（workflow F）— 从数据库到信号
- **场景 / 角色**：PV / 生物统计 — 维护安全性数据库，按 §4.3 / §4.6 / §4.7 做信号检测、验证、优先与风险评估。
- **正确处理路径**：① **数据库治理**：ICSR（§4.7）、文献、自发报告、研究数据整合，确保完整可溯；② **信号工作流**：检测（disproportionality §4.6）→ 验证（医学 / 机制）→ 优先（严重性 / 类效应）→ 评估 → 决策（RSI / IB 更新、监管沟通 §4.2 / §4.4）→ 风险最小化 → 有效性评估；③ **信号阈值**：各方法阈值仅参考惯例（§4.6），最终靠医学判断；④ **与安全计划**：信号触发 safety plan 更新与安全监测强化；⑤ **监管沟通**：重大信号走 §4.4 DSUR 与紧急安全措施。
- **关键要点**：数据库是信号管理的底座——"检测 → 验证 → 优先 → 评估 → 决策 → 最小化"闭环方为体系。
- ⚠️ 安全性数据库要求、信号管理流程与阈值惯例为动态项，以 ICH E2E / CIOMS 与各国 PV 现行指南为准（官方核实）。

### 4.9 安全性风险管理计划（RMP / Safety Management Plan）（workflow F）— 安全风险的前瞻管理
- **场景 / 角色**：PV / 医学 — 制定安全性风险管理计划（RMP / 安全计划），系统识别、最小化与沟通风险（呼应 §4.8 信号管理）。
- **正确处理路径**：① **计划内容**：已识别重要风险、潜在重要风险、额外药理 / 流行病学数据、风险最小化措施；② **与 RSI / IB**：风险更新同步 RSI（§4.2）、IB 安全信息；③ **与信号**：信号触发计划更新与安全监测强化（§4.8）；④ **与监管**：RMP 是申报 / 批准条件的一部分（尤其附条件批准 §5.4）；⑤ **有效性**：风险最小化措施须评估有效性（呼应 §6.5 CAPA 有效性）。
- **关键要点**：RMP 把"安全"从被动信号转为主动管理——识别 → 最小化 → 沟通 → 有效性评估闭环。
- ⚠️ RMP 内容、风险最小化措施与监管要求为动态项，以 ICH E2E / 各国 RMP 现行指南为准（官方核实）。

### 4.10 上市后安全性研究（PASS）/ 上市后承诺（workflow F / 注册）— 批准后证据补全
- **场景 / 角色**：PV / 注册 — 依监管要求在批准后开展上市后安全性研究（PASS）或履行上市后承诺（如确证性试验 §5.4）。
- **正确处理路径**：① **PASS 类型**：前瞻性 / 回顾性 / 登记库评估批准时未明的安全性问题；② **与附条件批准**：确证性试验（§5.4）是 PASS 的强约束形式，须按时完成；③ **设计**：预先规定方案、偏倚控制（呼应 §3.11 RWE 设计与 §3.8 外部对照）；④ **报告**：结果纳入 DSUR（§4.4）与定期安全更新，影响标签；⑤ **监管**：未履约可触发监管措施。
- **关键要点**：PASS / 上市后承诺是"批准后的证据闭环"——尤其附条件批准下为硬性义务，须预先设计与按时交付。
- ⚠️ PASS 设计、时限与履约要求为动态项，以 ICH E2E / 各国上市后研究现行指南为准（官方核实）。

## 5. CSR (workflow G)

> CSR **execution** is in `ref-clinical-operations.md` §7; this section covers the E3 regulatory structure.

### 5.1 E3 main chain & consistency chain E3 main chain: `title & synopsis → ethics & organizational structure → objectives → study plan → subject disposition / deviations → efficacy → safety → discussion & conclusions → tables & figures → appendices`. Consistency chain: `final protocol / amendment → SAP & changes → data review & analysis-set decision → database version → TFL → CSR body / synopsis → appendices`. E3 Chinese & English are the same topic in different languages, not two independent evidence sources; translation ambiguity returns to the current official ICH original.

### 5.2 Results presentation & common distortions First state subject flow, exposure, data availability; primary analysis reports effect size, interval and necessary tests around the pre-specified estimand; secondary / exploratory / post-hoc clearly labeled; subgroup interpretation emphasizes consistency & interaction, not isolated single-subgroup significance; safety combines exposure / time / dose / severity / causality / discontinuation / death / clinical context; case narratives consistent with tables / line listings / database / safety reports; discussion answers what is supported, what is not, how limitations affect interpretation. Common distortions: writing only significant results or presenting non-significant as equivalent / no difference / no risk; not explaining missingness / intercurrent events / important deviations / analysis-set changes; inconsistent counts / version / date / endpoint / table口径 across the document; body exceeding what protocol / SAP / data support; missing or wrong-version appendices; transcribing TFL sentence-by-sentence without medical interpretation or benefit–risk judgment.

### 5.3 Submission-level quality gate Lock versions of protocol / SAP / database / TFL / body / synopsis / appendices; reconcile subject disposition / analysis set / deviations / exposure / efficacy / safety counts; estimand / main analysis / sensitivity / conclusion consistent; deaths / SAE / important AE / discontinuations / case narratives cross-consistent; important changes / limitations / data gaps honestly explained; table / figure / listing / appendix references / signatures / approvals meet delivery requirements. Missing key source → output only gap / risk / next quality gate, do not claim "submissible".

### 5.4 附条件/加速批准证据标准、MCID、生物标志物亚组与说明书平衡（workflow B / C / 注册） 主要终点统计显著但效应量低于 MCID 时：**加速批准（accelerated approval）须基于替代终点或中间临床终点（合理可能预测临床获益）**——若为硬终点且效应量 < MCID，AA 通常不适用；可行路径为**限定生物标志物阳性人群的富集传统批准**，或对该亚组以 surrogate 走 AA。**AA 证据标准**：须来自充分对照试验对 surrogate 的「实质性证据」，且**必须承诺上市后确证性试验（常为 IV 期/Phase 4）验证临床获益**——这是条件而非可选项（中国附条件批准逻辑相同：单关键试验 + surrogate + 确证性承诺）。**生物标志物亚组**：若**预设且统计稳健**（交互检验）可支持富集标签传统批准；若事后/探索性须另设确证试验。**说明书「统计显著但临床意义不确定」的平衡**：诚实反映效应量与 CI 是否跨越临床相关性、限定生物标志物人群、载明确证性承诺、用限制性指示语言（「在生物标志物阳性患者中证实」）+ 警示，降低超说明书使用风险。FDA AA 法规（21 CFR 314.500）、确证性试验时限、中国附条件批准标准为动态项，以官方原文为准（官方核实）。

### 5.5 中美双报的桥接策略（workflow 注册 / A） 同一创新药在中美同步申报时，核心差异与桥接：① **CMC 数据互认**：模块 3 质量数据两国审评逻辑不同，CTD/eCTD 技术要求与地域性附录（Module 1）不可互认，须分别满足；② **种族敏感性（Ethnic Sensitivity）**：依据 ICH E5，评估美→中（或反向）外推的桥接需求——若中国亚群占比充足且 PK/PD 与安全一致，可桥接；若占比不足或存在种族因素影响暴露 / 反应，须补充中国数据或单独桥接试验；③ **临床数据外推**：全球多中心试验（MRCT）若中国受试者占比不足，通常**不自动豁免**中国桥接——须论证中国人群代表性、是否达统计把握度、监管接受度；④ 设计须同时满足两国：统一主方案 + 地域性附录 + 预先与两国监管沟通（Pre-IND / Type B）。CMC 互认范围、种族桥接与 MRCT 中国占比要求为动态项，以 NMPA / FDA 现行注册与桥接指导原则为准（官方核实）。

### 5.6 AI 辅助影像学终点判读的监管验证（workflow C / 注册） 以 AI 算法辅助肿瘤影像评估（如 iRECIST）递交 NDA/BLA 时，须证明 AI 判读**非劣效于传统 BICR**：① **算法验证文件**：训练 / 验证数据集构成、金标准（通常 BICR 盲态独立中心审查）标注、性能（敏感性 / 特异性 / 一致性如 Kappa / ICC）、偏倚评估；② **可解释性（Explainability）**：须能展示判读依据（热力图 / 特征），避免黑箱；③ **可重复性（Reproducibility）**：不同运行 / 版本 / 中心结果一致，版本控制与锁定；④ **非劣效验证**：预设 AI vs BICR 的一致性界值（如差异在预设 ±δ 内），主分析以 BICR 为准、AI 作支持或替代须监管事先认可；⑤ 若 AI 替代 BICR，须在 SAP / 影像章程预先定义且经审评接受。AI 影像验证与替代 BICR 的接受标准为动态项，以 FDA / CDE 影像终点与 AI/ML 软件临床验证现行指南为准（官方核实）。

### 5.7 生物类似药免疫原性差异与相似性判定（workflow C / 注册） 生物类似药 III 期等效性试验中，ADA 阳性率差异（如 16% vs 参照药 9%，p<0.05）**不自动否定相似性（Similarity）**：① 相似性基于**整体证据链**（分析相似性、PK、PD、疗效主要终点、安全性主要终点均达等效）→ 若主要终点等效而仅免疫原性（次要 / 探索）有统计差异，通常不推翻相似性；② **临床相关性评估**：须分析 ADA 是否伴临床后果（中和抗体、疗效丧失、严重过敏 / 输注反应）、发生时序、持续性与滴度；③ **补充分析（BLA 须提交）**：免疫原性桥接（检测方法一致性、阳性对照）、ADA 与疗效 / 安全的相关性、风险最小化；④ 监管关注「差异是否有临床意义」而非单纯统计显著。相似性判定与免疫原性桥接要求为动态项，以现行生物类似药技术指导原则与监管原文为准（官方核实）。

### 5.8 基因治疗生殖系风险与育龄期受试者管理（workflow F / 注册） 基因治疗载体（AAV 等）具潜在生殖系整合 / 垂直传播风险，对育龄期受试者：① **避孕要求时长**：基于**载体脱落动力学（shedding）**（血液 / 体液可检测载体 DNA 的持续时间）与生殖毒性研究综合确定，而非仅按给药周期；须在 ICF / 避孕计划预先规定，并覆盖脱落窗口；② **意外妊娠处理**：除常规妊娠报告（见 `ref-clinical-operations.md` §5.4）外，若载体具生殖系风险，须启动**特殊分子检测**（如母体 / 胎儿样本载体 DNA 检测）与**长期子代随访**，纳入专项安全性监测；③ 受试者教育、避孕依从性监测与脱落期禁育须写入方案与 ICF。避孕时长、载体检测与子代随访要求为动态项，以基因治疗产品非临床 / 临床安全现行指导原则为准（官方核实）。

### 5.9 篮式 / 伞式 Master Protocol 设计与多重性（workflow B / C） 篮式（Basket）/ 伞式（Umbrella）/ 平台（Platform）等 Master Protocol 在多个队列评估同一或关联干预：① **各队列假设独立性**：默认各瘤种 / 队列为**独立假设**，各自控制族系错误率（family-wise error rate, FWER）——即每个队列的 α 通常按 **Bonferroni 或分层策略**分配（如 K 个队列各 α/K），而非共享总 α；共享错误率仅在特定预设下（如共同对照、统一样本量再估计）适用，须预先声明；② **多重性控制**：在 SAP 预先规定各队列 α、是否设主队列 / 探索队列、是否允许多重性回收（multiplicity borrowing）；③ **获批解释**：若仅 2 个队列显效、其余阴性，FDA / NMPA 通常**仅基于显效队列的支持性证据批准对应适应症**——阴性队列不「拖累」阳性队列，但申请人须解释整体安全性与跨队列一致性（class effect）、阴性是否因把握度不足或生物学异质性；④ 单臂篮式（如罕见突变）须结合 §3.8 外部对照与附条件批准逻辑。队列划分、α 分配与获批策略为动态项，以 FDA / NMPA Master Protocol 相关指导原则与现行审评逻辑为准（官方核实）。

### 5.10 患者报告结局（PRO / ePRO）作为主要终点的验证与可接受性（workflow C / 注册） 将患者报告结局（PRO，经 ePRO 采集）作为**支持批准的主要终点**（如症状 NRS 评分）须满足监管验证与可接受性：① **终点验证（qualification）**：PRO 量表须有**内容效度、信度、可解释性（anchor-based MCID）**，最好经 FDA / EMA PRO 量表验证框架或等效证据；ePRO 系统须验证（界面、计算、离线、数据完整）；② **ALCOA+ 与盲态**：ePRO 每日自报具 ALCOA+ 优势（时间戳、不可篡改），但**缺乏独立盲态验证**——若终点主观且开标，须强化盲态设计（如盲态终点判定委员会 BEC、中心化评估、评估者盲态）以控测量偏倚；③ **监管接受度**：FDA / NMPA 对「以患者自报症状作主要终点」持审慎——须证明该症状临床重要性、量表能检测真实变化、且非仅替代硬终点规避；伴随客观终点（如活动耐量、客观生理指标）增强说服力；④ 缺失与补采须按 §4.4（CDISC / CSR 透明）。PRO 作为主要终点的验证标准与接受度为动态项，以 FDA PRO 指南 / EMA 及 NMPA 现行要求为准（官方核实）。

### 5.11 药物经济学（HEOR）与准入证据：EQ-5D、效用映射与 QALY（workflow 注册 / 准入）— 试验内采集 PRO / 成本数据支持医保准入
- **场景 / 角色**：HEOR / 注册事务 — 关键试验并行采集健康相关生命质量（HRQoL，如 EQ-5D-5L）与医疗资源 / 成本数据，计划用于医保准入与定价，需说明效用值与 QALY 的处理。
- **正确处理路径**：① **效用值映射（mapping）**：当未直接用偏好效用量表（如 SF-36）时，须用经验证的映射函数转 EQ-5D 效用，注明映射模型与不确定性；② **QALY 计算**：基于效用 × 生存时间，缺失 / 截尾的 HRQoL 用预定义方法插补（呼应 `ref-clinical-operations.md` §4.4 缺失处理），明确时间偏好与贴现；③ **试验内 EE（经济评价）设计**：预先规定视角（卫生体系 / 社会）、成本项、折扣率、敏感性分析（确定性 / 概率性），避免事后拼凑；④ **与监管关系**：HRQoL / PRO 作终点须满足 §5.10 验证与可接受性；经济证据支持**准入 / 定价**而非注册有效性结论；⑤ **数据源**：真实世界成本可联动 RWE（§3.8），但须区分"注册证据"与"准入证据"用途。
- **关键要点**：QALY / 效用是准入证据而非注册疗效证据；映射方法与缺失处理须预先规定并做不确定性分析。
- ⚠️ EQ-5D 版本、贴现率、QALY 阈值与医保准入标准为动态项，以各国 HTA / 医保与 NMPA 现行要求为准（官方核实）。

### 5.12 孤儿药资格认定与自然史研究外部对照（workflow 注册）— 罕见病减免试验路径
- **场景 / 角色**：罕见病专家 / 注册事务 — 罕见病药物申请孤儿药资格认定（orphan designation），并用自然史研究（natural history study）作外部对照支持附条件批准。
- **正确处理路径**：① **孤儿药认定**：依 jurisdiction 提交认定（患病人数阈值、严重性、无满意疗法），获认定后享税费 / 审评激励；② **自然史外部对照**：罕见病缺乏同期对照时，用前瞻性 / 回顾性自然史研究构建外部对照（呼应 `ref-clinical-operations.md` §3.8 外部对照 5 点 + RWE）；须预先规定可比人群、协变量、时间趋势与偏倚控制；③ **减免路径**：孤儿药 + 单臂 + 自然史对照常用于附条件批准，但须 Pre-IND 预先认可（§3.8）；④ 自然史数据质量（完整性 / 代表性）须达证据标准，避免"凑对照"。
- **关键要点**：孤儿认定是资格激励而非证据替代；自然史外部对照须同样满足预先规定与偏倚控制。
- ⚠️ 孤儿药患病人数阈值、认定程序与激励、自然史数据接受度为动态项，以 FDA ODA / EMA / NMPA 罕见病与孤儿药现行规定为准（官方核实）。

### 5.13 疫苗 / 生物制品桥接与免疫原性可比性（workflow 注册）— 扩展适应症或人群
- **场景 / 角色**：注册事务 / 临床药理 — 已上市疫苗 / 生物制品拟扩展人群（如年龄、地域）或变更工艺，需桥接试验证明免疫原性可比。
- **正确处理路径**：① **桥接逻辑**：以免疫原性（几何平均滴度 GMT、血清转化率）为主要桥接终点，证明新人群 / 工艺与原获批人群的**可比性（bridging）**；② **设计**：常为非劣效于原人群免疫原性，预设可比性界值（如 GMT 比值的 95% CI 下限 > 某比例）；③ **安全性**：新人群 / 工艺的局部 / 全身不良反应谱须可比且不劣；④ **工艺变更**：按可比性研究（analytical + 非临床 + 临床免疫原性）层级递进，重大变更可能需新确证；⑤ 与监管预先沟通桥接界值与接受标准。
- **关键要点**：疫苗桥接以免疫原性可比为核心，界值须预先规定；工艺变更须走层级可比性证据。
- ⚠️ 桥接界值、血清转化判定与工艺变更可比性要求为动态项，以 FDA / EMA / NMPA 疫苗与生物制品桥接现行指南为准（官方核实）。

### 5.14 独立影像（BICR）章程与评估不一致处理（workflow C / 注册）— 影像学终点判读治理
- **场景 / 角色**：独立影像(BICR) / 统计 — 设定 BICR 章程，处理 BICR 与研究者评估不一致、影像 QC 与偏倚控制。
- **正确处理路径**：① **BICR 章程（charter）**：预设评估标准（RECIST / iRECIST 版本）、盲态、独立阅片人资质、仲裁机制、QA 与重读规则；② **不一致处理**：BICR 与研究者评估不一致时，以**预设的主要评估者（通常 BICR）**为准，不一致率作敏感性分析；不得擅自用"有利于结果"的一方；③ **影像 QC**：影像采集协议统一、传输完整、中心化复核、重读一致性（Kappa / ICC）；④ 与 SAP 衔接：影像终点判定规则、缺失 / 不可评估处理写清；⑤ AI 辅助判读须满足 §5.6 非劣效于 BICR 的验证。
- **关键要点**：BICR 价值的本质是盲态与独立——章程预设、不一致按预设裁定，避免选择性采用。
- ⚠️ BICR 章程要素、不一致处理与影像 QC 要求为动态项，以 FDA / CDE 影像终点现行指南为准（官方核实）。

### 5.15 平台试验 MAMS 与封档（flagging）规则（workflow B / C）— 多臂多阶段与臂的退出
- **场景 / 角色**：生物统计师 / 注册 — 平台试验（platform trial）采用 MAMS（多臂多阶段），某臂无效时如何"封档"（flagging / stopping）并控制错误率。
- **正确处理路径**：① **MAMS 结构**：多实验臂共享对照、分阶段（interim）评估，无效臂被"封档"停止入组但不影响其他臂；② **错误率控制**：封档须预设 α 消耗（如 alpha-spending 或错误发现率 FDR），共享对照下整体家族错误率受控（呼应 §5.9 多重性）；③ **封档规则**：基于期中分析的疗效 / 安全性边界，预设封档与继续标准，透明执行；④ **对照臂共享**：共享对照提升效率但须维护对照完整性；⑤ **监管接受**：平台试验设计须 Pre-IND 沟通，封档决策的可解释性对获批关键（§5.9 按阳性队列获批）。
- **关键要点**：平台试验效率来自共享对照与阶段评估；封档须预设且错误率受控，否则跨臂推断失真。
- ⚠️ MAMS α 控制、封档边界与平台试验接受度为动态项，以 FDA / EMA / NMPA Master Protocol 现行指南为准（官方核实）。

### 5.16 RWE 用于标签扩展（label expansion）的可靠性与边界（workflow 注册 / RWE）
- **场景 / 角色**：医学事务 / 注册 — 用真实世界证据（RWE）支持已获批药物的新适应症 / 人群标签扩展，须论证可靠性。
- **正确处理路径**：① **证据等级**：RWE 用于标签扩展证据等级低于 RCT，须预先方案（靶试验模拟，§3.8）+ 偏倚控制（PS / 工具变量 / 阴性对照）；② **适用边界**：仅当 RCT 不可行或作为支持性证据时考虑，重大疗效声称仍以 RCT 为主；③ **数据质量**：RWD 来源（登记 / 医保 / EMR）须满足适用性（§3.8 RWE 方法）；④ **监管沟通**：标签扩展的 RWE 路径须 Pre-IND / Type B 预先认可；⑤ 与 §5.12 自然史、§3.8 外部对照衔接——RWE 标签扩展是其应用之一。
- **关键要点**：RWE 可支持标签扩展但非替代 RCT 的确证——须预先设计、偏倚可控、监管认可。
- ⚠️ RWE 标签扩展接受度与数据要求为动态项，以 FDA / EMA / NMPA RWE 与标签现行指南为准（官方核实）。

### 5.17 临床终点裁定委员会（CEC / EAC）（workflow C / 注册）— 临床事件盲态裁定
- **场景 / 角色**：独立影像 / 统计 — 设定临床终点裁定委员会（CEC / EAC）对临床事件（心梗 / 卒中 / 死亡）盲态裁定，与 BICR（影像）区别。
- **正确处理路径**：① **CEC 职责**：对临床复合终点事件（如心血管事件）按预设标准盲态裁定发生与否、时间、性质，减少测量偏倚；② **与 BICR 区别**：BICR 管影像终点（§5.14），CEC 管临床事件，二者可并行；③ **章程**：预设裁定标准、盲态、仲裁、QA，裁定者独立于申办方 / 研究者；④ **与 SAP 衔接**：事件定义、缺失 / 不可裁定处理写清；⑤ 裁定不一致率作敏感性分析。
- **关键要点**：CEC 本质是临床事件的盲态独立裁定——章程预设、独立执行，避免研究者偏倚。
- ⚠️ CEC 章程要素与事件裁定要求为动态项，以 FDA / CDE 终点裁定现行指南为准（官方核实）。

### 5.18 生物类似药临床桥梁与可比性边界（workflow C / 注册）— 分析 / PD / 临床的层级证据
- **场景 / 角色**：注册事务 / 临床药理 — 生物类似药在分析 + PD 高度相似下，是否可豁免部分临床试验（临床桥梁 / 精简临床），边界如何。
- **正确处理路径**：① **层级可比性**：分析相似性（结构 / 功能）→ PK / PD 相似性 → 临床相似性，证据自下而上累积（呼应 §5.7 整体证据链）；② **临床豁免边界**：当分析 + PD 充分相似且 MOA / 免疫原性支持时，可精简或豁免确证性临床试验（"精简临床"路径），但须监管事先认可；③ **残留不确定性**：若某维度证据不足，须补临床（如疗效确证或免疫原性桥接，§5.7）；④ **监管沟通**：可比性证据与豁免范围须 Pre-IND / Type B 认可。
- **关键要点**：生物类似药临床豁免非"免全部"——与分析 / PD 相似度层级挂钩，边界须监管认可。
- ⚠️ 生物类似药临床豁免边界与可比性要求为动态项，以 FDA / EMA / NMPA 生物类似药现行技术指导原则为准（官方核实）。

### 5.19 种族因子（RFE）定量评估与桥接论证（workflow 注册 / A）— E5 外推的量化
- **场景 / 角色**：注册事务 / 临床药理 — 中美双报中超越定性种族敏感性，定量评估种族因子（RFE = (μ_E - μ_A) / σ）与外推必要性。
- **正确处理路径**：① **RFE 定量**：以群体 PK / PD 差异量化种族因子（RFE = 暴露 / 效应均值差 / 标准差），评估是否超预设阈值需桥接；② **桥接论证**：RFE 小且 CIs 窄 → 可外推；RFE 大或不确定 → 需中国数据 / 桥接试验（呼应 §5.5 种族敏感性）；③ **协变量**：体重、代谢酶频率、医疗实践等作为 RFE 解释变量；④ **监管沟通**：定量种族分析须 Pre-IND / Type B 认可，MRCT 中国占比论证（§5.5）与之联动；⑤ 与 §5.16 RWE、§3.8 外部对照互补。
- **关键要点**：种族桥接从"定性 E5"走向"定量 RFE"——阈值须预设并经两国监管认可。
- ⚠️ RFE 阈值、桥接定量要求为动态项，以 ICH E5 与中国 / NMPA、FDA 种族桥接现行指南为准（官方核实）。

### 5.20 生物等效性（BE）试验设计与判定（workflow C / 注册）— 以 BA / BE 证明治疗等效
- **场景 / 角色**：临床药理 / 注册 — 仿制药 / 改剂型以 BE 试验证明与参比制剂生物等效，须满足设计（空腹 / 餐后）与判定标准（呼应临床 §1.5 BA / BE）。
- **正确处理路径**：① **设计**：交叉设计（常见 2×2）、受试者例数、空腹 / 餐后、采血时点、washout 须满足把握度；② **判定**：以 AUC / Cmax 的几何均值比（GMR）及其 90% CI 落在预设等效界值（常见 80.00%–125.00%）内判定 BE；③ **高变异药物（HVDP）**：可考虑 scaled average bioequivalence（SABE）或重复设计，预设方法；④ **窄治疗窗（NTID）**：采用更严判定；⑤ **与 §5.7 区分**：BE 用于化学仿制药 / 改剂型，相似性用于生物类似药，证据层级不同；⑥ **注册**：BE 结果支撑仿制药 / 一致性评价申报。
- **关键要点**：BE 以药代终点 + 预设等效界值判定，界值与高变异 / 窄窗处理须预先规定；与生物类似药"相似性"是不同路径。
- ⚠️ BE 等效界值、高变异 / NTID 处理方法与样本量要求为动态项，以 NMPA / FDA / EMA BE 与生物等效性现行技术指导原则为准（官方核实）。

### 5.21 同情用药与扩展性用药（expanded access / compassionate use）（workflow 注册 / A）— 试验外获取在研药的合规路径
- **场景 / 角色**：医学事务 / 注册 — 无标准治疗且不符入排的重症患者申请使用在研药（同情用药 / 扩展性用药 / 名义患者），须走合规路径。
- **正确处理路径**：① **路径类型**：依 jurisdiction 有 compassionate use、expanded access（individual / intermediate / treatment IND）、名义患者（named patient）等不同程序；② **前置条件**：通常须试验已显示一定安全性、患者无替代疗法、伦理与监管批准、申办方同意供应；③ **责任与监测**：同情用药仍须安全监测与报告（SUSAR / AE 仍纳入安全信息流），不得替代 RCT 证据；④ **知情同意**：单独知情同意（非试验 ICF），明确研究性、风险与自愿；⑤ **与注册关系**：同情用药数据通常不作为上市主要证据，但可入安全数据库（§4.4 DSUR）；⑥ **多国差异**：各辖区程序、准入与报销不同，须分别合规。
- **关键要点**：同情用药是"人道主义例外"而非上市通道——须合规审批 + 持续安全监测，且不构成疗效证据。
- ⚠️ 同情用药 / 扩展性用药程序、批准条件与报告要求为动态项，以 FDA expanded access、EMA compassionate use 与 NMPA 现行规定为准（官方核实）。

### 5.22 儿科研究计划（PIP）与儿科适应症监管路径（workflow 注册）— 儿科开发的强制规划
- **场景 / 角色**：注册事务 / 儿科专家 — 新药须按辖区（如 EU Pediatric Regulation）提交儿科研究计划（PIP）或儿科适应症开发，获取儿科 exclusivity / 激励。
- **正确处理路径**：① **PIP 内容**：儿科适用性评估、研究规划（剂量 §1.7、年龄分层、安全性）、时限与豁免 / 延期；② **监管互动**：PIP 须监管批准（如 EMA PDCO），与成人开发计划协调；③ **激励**：pediatric exclusivity / 优先审评等；④ **衔接**：与 §1.7 儿科剂量 / Assent、§3.5.1 儿科同意衔接；⑤ **中国**：儿科用药研发技术指导原则与适宜剂型 / 口感要求。
- **关键要点**：儿科开发是"强制规划 + 监管批准"——PIP 与成人计划协同，剂量与同意须儿科特化。
- ⚠️ PIP 要求、儿科激励与剂型 / 口感要求为动态项，以 EMA Pediatric Regulation、NMPA 儿科用药指导原则为准（官方核实）。

### 5.23 统计分析报告（SAR）与 CSR / TFL 关系（workflow C / G）— 分析层的独立交付
- **场景 / 角色**：统计 / 医学写作 — 锁库后出具统计分析报告（SAR），作为 CSR 的统计支撑，须独立、完整、可溯。
- **正确处理路径**：① **SAR 内容**：分析集定义、基线、主要 / 次要 / 亚组 / 敏感性分析、伴发事件（§4.4）、估计目标（§3.1）落地，与 SAP 一致；② **与 CSR 关系**：SAR 是 CSR 统计章节的依据，CSR 不重复全部细节但须引用且一致（§5.1）；③ **独立 QC**：统计分析与编程（§4.5 TFL）须独立 QC，SAR 经统计与医学审核；④ **衔接**：与 §4.4 缺失 / CDISC、§4.5 编程衔接——数据版本锁定；⑤ **透明**：SAR 须披露所有分析（预设 / 探索）与偏离。
- **关键要点**：SAR 是"分析层独立交付"——与 CSR 一致但不重复，独立 QC 与透明披露是监管核查重点。
- ⚠️ SAR 内容、与 CSR 一致性及披露要求为动态项，以现行统计规范与监管提交要求为准（官方核实）。

### 5.24 临床结局评估（COA）与终点选择（workflow C / G）— 未验证工具难支撑关键终点
- **场景 / 角色**：统计 / 临床终点 — 选择临床结局评估工具（COA：clinician-/observer-/patient-/performance-reported）作为有效性 / 安全性终点须保证信效度。
- **正确处理路径**：① **COA 类型**：PRO / ePRO（§4.10）、ObsRO、ClinRO、PerfRO 适用场景不同；② **信效度**：工具须经验证（可靠性 / 有效性 / 响应度），跨文化须语言验证（§4.14）；③ **终点层级**：把 COA 放在估计目标（§3.1）框架，明确主 / 次要；④ **偏倚控制**：盲态评估、避免问诊偏倚；⑤ **与监管**：关键终点须预先与监管确认可接受性（§8.11）。
- **关键要点**：COA 选点是"工具验证 + 层级定位 + 偏倚控制"——未验证工具支撑的终点难被接受。
- ⚠️ COA 类型、验证要求与终点可接受性为动态项，以 FDA COA / PRO 指南与 ICH 现行规范为准（官方核实）。

### 5.25 遗传毒性与致癌性非临床安全性证据（workflow C / 非临床）— 非临床安全底座
- **场景 / 角色**：非临床 / 注册 — 药物须提供遗传毒性（致突变）与致癌性（长期）非临床证据，支撑临床安全窗与标签。
- **正确处理路径**：① **遗传毒性**：标准组合（细菌回复突变 Ames + 体外染色体畸变 / 微核 + 体内微核），依 ICH S2；② **致癌性**：常规 2 年啮齿类或转基因 / 短期模型，依暴露时长与适应症（长期用药须致癌）；③ **光致癌**：具光吸收者叠加光致癌评估（§1.14）；④ **与剂量**：安全窗由 NOAEL / 暴露比推算（§1.5 FIH）；⑤ **与临床**：遗传毒性阳性须临床监测策略联动（§5.3）。
- **关键要点**：遗传 / 致癌性是"非临床安全底座"——标准组合 + 暴露驱动致癌策略，支撑临床风险沟通。
- ⚠️ 遗传毒性组合、致癌性试验策略与判定为动态项，以 ICH S1 / S2 与监管非临床安全性现行指南为准（官方核实）。

## 6. GCP version discipline (A / D boundary)

To answer a current GCP question: 1. Check ICH official site for E6(R3) principles / annex / Step status; 2. Check NMPA current China GCP release / implementation date / transition; 3. Judge applicable version by the event or activity execution date; 4. Also check whether project protocol / SOP / IRB approval / contract is stricter. Local E6(R1) may be used to understand the classic responsibility framework, but not as the sole current-GCP basis. Judgment主线 unchanged across versions: subject rights / safety / welfare first; study must be scientific with acceptable benefit–risk; responsibility may be delegated but oversight accountability does not disappear; informed consent is a continuous process; data trustworthy & traceable fit for intended use; quality focuses on factors affecting subject protection & result reliability; computerized systems / data governance / service providers / new technologies must enter risk oversight.

## 7. CTD & M4 series (A / G)

| Module | Core content | Main basis |
|---|---|---|
| Module 1 | Regional admin / application form / prescription | Region-specific, not the unified CTD body |
| Module 2 | CTD preface, quality / non-clinical / clinical overview & summary | M4 / M4Q / M4S / M4E |
| Module 3 | Quality core data | M4Q and current Q-series / region |
| Module 4 | Non-clinical study reports | M4S and current S-series |
| Module 5 | Clinical study list, CSR & reports | M4E, E3 etc. |

M4E: 2.5 clinical overview (development strategy / evidence strength / limitations / benefit–risk / supports labeling, not result repetition); 2.7 clinical summary (more detailed cross-study summary & comparison); Module 5 holds study list / single CSR / pooled analysis / post-marketing / individual data. E3 CSR answers a single study, M4E 2.7 answers cross-study facts, M4E 2.5 answers whole-program regulatory interpretation & benefit–risk. M4Q / M4S do not push manufacturing / non-clinical issues into clinical argument. Granularity supports lifecycle replacement & version control; complete module numbering ≠ sufficient data — check evidence gaps & cross-module consistency; eCTD version / technical spec / regional validation rules verified against official implementation documents.

### 7.1 申报资料与 eCTD 递交准备（workflow A / G）— 从 CSR 到提交的组装
- **场景 / 角色**：注册事务 — 将 CSR、临床概述 / 总结（§5.1 M4E 2.5 / 2.7）、模块 5 等组装为申报资料并按 eCTD 递交。
- **正确处理路径**：① **模块组织**：Module 2 临床概述 / 总结、Module 5 研究列表 / CSR / 汇总分析（§7 M4）；② **eCTD**：按 eCTD version / 技术规范（§7）组装，地域性附录（Module 1）分别满足；③ **一致性**：申报资料与 CSR（§5.3）、SAP、数据库版本一致，跨模块一致（§8.1 依赖）；④ **递交前核对**：版本 / 日期 / 编号 / 签名 / 附件齐备，缺失项（§5.3 gap table）关闭；⑤ **地域差异**：中美 / 欧盟递交格式与入口不同（§5.5 CMC、§8.3）。
- **关键要点**：递交准备是"一致性 + 格式合规"的最后一公里——模块组织对、eCTD 技术规范对、跨模块一致。
- ⚠️ eCTD 版本、技术规格与递交入口要求为动态项，以各国 eCTD 实施指南与监管官网现行原文为准（官方核实）。

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

### 8.4 人类遗传资源合规与数据跨境（workflow A / 注册）— 人遗资源采集、出境审批与数据对外提供
- **场景 / 角色**：人类遗传资源办 / 注册事务 — 多中心试验采集血液 / 组织拟出境送中心实验室检测或外方分析，须走人遗资源审批 / 备案与数据跨境合规。
- **正确处理路径**：① **人遗资源范围**：人类遗传资源材料（血液 / 组织 / 细胞等含人体基因组 / 基因）与信息（基因数据）均受《人类遗传资源管理条例》规制；② **审批 / 备案**：涉及重要遗传家系、特定地区、外方单位参与或资源出境的，通常须**人类遗传资源采集 / 保藏 / 国际合作 / 材料出境审批或备案**（依情形），与伦理审查、CTA 并行；③ **数据跨境**：基因数据 / 受试者个人健康信息对外提供须同时满足人遗规定与数据安全 / 跨境传输要求（呼应 §8.5），明确接收方、用途、去标识化与再转移限制；④ **国际合作**：外方单位参与须走国际合作科学研究审批 / 备案，权益与知识产权归属写清；⑤ **文档**：审批批件、知情同意（含样本 / 数据出境告知）、伦理批件、数据出境安全评估留档。
- **关键要点**：人遗合规是独立于伦理 / CTA 的前置义务，样本 / 基因数据出境须专门审批且不得"先送后补"；与数据跨境隐私要求叠加。
- ⚠️ 人遗审批 / 备案范围、出境条件、数据对外提供与安评要求为动态项，以《人类遗传资源管理条例》及科技部 / 卫健委现行规定为准（官方核实）。

### 8.5 跨国数据隐私与跨境传输合规（GDPR / DPO）（workflow A / 注册）— EU 受试者数据传境外云 EDC 的落地
- **场景 / 角色**：数据保护官（DPO） / 申办方 — 含 EU 受试者的试验将个人健康数据传至境外云端 EDC / 分析，须满足 GDPR 跨境传输与数据主体权利。
- **正确处理路径**：① **传输机制**：EU 数据出境通常依赖**标准合同条款（SCC）/ 约束性企业规则（BCR）**或充分性认定，并做传输影响评估（TIA）；② **数据主体权利**：受试者有权访问、更正、删除（被遗忘权）、限制处理、可携，须在流程与系统中可落地（撤回同意的数据删除见 `ref-clinical-operations.md` §4.1.4）；③ **数据最小化与去标识**：仅收集必要数据、传输前假名化 / 去标识化、密钥境内外分离；④ **泄露通报**：个人数据泄露须在规定时限内通知监管与（重大时）数据主体；⑤ **DPO 与合同**：设数据保护职责（DPO），与云 / EDC / CRO 签数据处理协议（DPA），明确子处理者与再转移；⑥ **与 GCP 衔接**：ALCOA+ 可追溯（§4.1）与隐私删除权存在张力，须以合同 / 方案预先约定数据保留与删除边界。
- **关键要点**：GDPR 跨境传输需 SCC / BCR + TIA；数据主体删除权与 GCP 数据保留义务须预先协调；DPA 与子处理者管理不可缺。
- ⚠️ SCC / BCR 版本、通报时限、数据主体权利范围与本地化要求为动态项，以欧盟 GDPR 与各国数据保护法现行原文为准（官方核实）。

### 8.6 发表透明度与选择性报告防控（workflow A / G）— 避免 cherry-picking 与事后亚组
- **场景 / 角色**：医学事务 / 研究者 — 研究者发起的 post-hoc 亚组分析拟投稿，如何避免选择性报告、满足预注册与透明度要求。
- **正确处理路径**：① **预注册 / 登记**：关键试验须于公众登记平台注册（靶点 / 主要终点透明），事后亚组不得伪装为预设；② **选择性报告防控**：主要 / 次要 / 探索 / 事后分析须明确标注（呼应 `ref-clinical-operations.md` §5.2 结果呈现），不得仅报显著、隐瞒非显著；③ **透明度**：CSR 与注册信息一致（§5.3），发表须与监管申报结论协调，不得矛盾；④ **数据完整性**：投稿数据须源自可溯源数据库，避免"美化"；⑤ 利益冲突与资助披露按期刊 / 规范。
- **关键要点**：透明度不是"多发表"而是"全貌可查"——预设分析与事后探索须分明标注。
- ⚠️ 试验注册平台、选择性报告与披露要求为动态项，以 ICMJE / 注册平台与现行规范为准（官方核实）。

### 8.7 医学事务（MSL）沟通合规与透明（workflow A）— 与研究者互动边界
- **场景 / 角色**：医学事务 / MSL — 医学科学联络员（MSL）与研究者沟通，须避免不当影响研究者判断 / 数据、满足透明与反贿赂要求。
- **正确处理路径**：① **边界**：MSL 提供科学信息（已获批标签 / 公开数据），不得诱导处方、不得影响研究者的方案执行或数据判读；② **透明**：互动记录可查，与 HCP 的咨询费 / 讲者费符合反贿赂（如阳光法案 / 反商业贿赂）与披露要求；③ **与研究分离**：MSL 不参与研究者发起研究的方案设计以规避利益冲突，研究者独立性须保留；④ **信息准确**：所提供科学信息须基于权威来源，不超出标签或证据；⑤ 与 PV 接口：MSL 获取的医学信息（含安全性信号）须按流程转 PV。
- **关键要点**：MSL 价值在科学中立沟通——任何"影响数据 / 处方"的越界都构成合规风险。
- ⚠️ 反贿赂 / 阳光法案披露阈值与 MSL 合规要求为动态项，以当地反商业贿赂法与行业规范为准（官方核实）。

### 8.8 多区域 / 多国试验的伦理协调（workflow A / D）— 多地 IRB 与伦理差异管理
- **场景 / 角色**：机构办 / 伦理协调 — 国际多中心（MRCT）涉及多国多中心 IRB，伦理审查要求与标准不一，须协调而不降标。
- **正确处理路径**：① **中央 vs 本地 IRB**：部分辖区认可中央 / 统一 IRB，部分要求本地 IRB 独立审查，须按各辖区规定；② **协调原则**：统一伦理提交包（通用方案 / ICF / 知情同意元素）经本地化适配，确保受试者保护标准不降低；③ **差异管理**：各国对风险受益、弱势群体、知情同意、补偿、数据隐私要求不同，须识别差异并以最严格适用或本地特化；④ **持续审查**：多中心跟踪审查（§3.7 持续审查）须满足各辖区频率与报告；⑤ **文件**：伦理批件、版本、协调记录留档，支持 GCP 核查（§6.4）。
- **关键要点**：MRCT 伦理协调核心是"统一基线 + 本地适配 + 不降标"；中央 IRB 接受度因辖区而异。
- ⚠️ 多区域 IRB 接受度、伦理协调与本地化要求为动态项，以各辖区 GCP / 伦理审查现行规范为准（官方核实）。

### 8.9 数据保护影响评估（DPIA）与高风险处理（workflow A）— GDPR Art.35 与类似评估
- **场景 / 角色**：DPO / 申办方 — 涉及大规模 / 高风险个人健康数据处理的试验（如全基因组、跨境、可穿戴连续监测）须做数据保护影响评估（DPIA）并管理高风险。
- **正确处理路径**：① **DPIA 触发**：依 GDPR Art.35 等，对大规模敏感数据、画像、跨境、新技术采集等高风险处理须事先 DPIA；② **内容**：描述处理目的 / 必要性、风险识别（再识别、滥用、跨境）、缓解措施（假名化、最小化、访问控制）、剩余风险与咨询 DPO / 监管；③ **与 §8.5 衔接**：DPIA 是跨境传输（SCC / BCR + TIA）的上游评估，强化数据主体权利落地；④ **持续**：处理变更（新终点、新第三方）须更新 DPIA；⑤ **文档**：DPIA 报告留档，支持核查与数据主体询问。
- **关键要点**：DPIA 是高风险数据处理的"事前风控"——识别再识别 / 跨境 / 滥用风险并留缓解证据，与跨境传输评估叠加。
- ⚠️ DPIA 触发阈值、评估内容与监管要求为动态项，以欧盟 GDPR Art.35 与各国数据保护法现行原文为准（官方核实）。

### 8.10 人工智能 / 算法工具的伦理与监管审查（workflow A / D）— AI 辅助决策的合规边界
- **场景 / 角色**：申办方 / 伦理 — 试验中使用 AI 工具（如 AI 影像 §5.6、AI 入组筛选、AI 安全信号、可穿戴算法），须伦理与监管审查。
- **正确处理路径**：① **用途界定**：区分"辅助"（决策仍由人）vs "替代"（须严格验证 §5.6）；② **验证与透明**：算法性能、可解释性、版本锁定、偏倚评估（呼应 §5.6）；③ **伦理**：AI 对受试者权益 / 隐私影响（数据、自动化决策）须伦理审查；④ **责任**：算法错误时责任归属明确，人工复核不可省；⑤ **数据**：AI 训练 / 推理数据合规（§8.5 DPIA §8.9）。
- **关键要点**：AI 工具须"用途分级 + 验证 + 人工兜底 + 责任清晰"——不得用黑箱替代临床 / 伦理判断。
- ⚠️ AI / 算法工具监管审查、验证与透明度要求为动态项，以 FDA / EMA / NMPA AI / ML 软件临床验证现行指南为准（官方核实）。

### 8.11 沟通交流会议（Type A / B / C）准备与纪要（workflow A / 注册）— 关键决策前的监管沟通
- **场景 / 角色**：注册事务 — 在关键开发决策前申请与监管的沟通交流会议，须准备充分并落实纪要。
- **正确处理路径**：① **会议类型**：Type A（阻碍程序）/ B（关键决策如 EOP2、Pre-IND、Pre-NDA）/ C（一般）各有程序与时限（呼应 §8.3）；② **准备**：背景包（问题清单、数据、方案、拟议路径）、预设议程与预期产出；③ **纪要**：会议达成的共识 / 分歧 / 行动项书面确认，作为后续申报依据；④ **多区域**：中美 / 欧盟会议程序不同，须分别安排（§5.5、§5.19）；⑤ **衔接**：与 §3.9 / §3.5 适应性 / 贝叶斯、§3.8 单臂等预先认可衔接。
- **关键要点**：沟通交流的价值在"预先共识"——准备充分 + 纪要闭环，降低后期申报不确定性。
- ⚠️ 会议类型、程序、时限与纪要要求为动态项，以 CDE / FDA / EMA 沟通交流现行指南为准（官方核实）。

### 8.12 临床试验暂停 / 临床 hold 与恢复（workflow A / 注册）— 监管叫停与重启
- **场景 / 角色**：注册事务 / 申办方 — 试验被监管临床 hold（暂停）或因安全 / 质量自行暂停，须处理与恢复。
- **正确处理路径**：① **触发**：监管 clinical hold（如重大安全风险、GCP 问题、数据完整性）或申办方自行暂停（DSMB §3.10 建议、安全信号 §4.8）；② **应对**：评估原因、暂停入组 / 给药、通知中心 / 伦理 / 受试者、保护已入组者；③ **回复**：向监管提交纠正措施与证据，申请解除 hold；④ **恢复**：满足条件后重启，须方案 / 流程更新与再培训；⑤ **联动**：与 §4.2.6 召回、§6.4 核查联动。
- **关键要点**：临床 hold 是监管对受试者保护的强制暂停——须快速响应、根因纠正、证据充分方得恢复。
- ⚠️ 临床 hold 触发、回复程序与恢复条件为动态项，以 NMPA / FDA / EMA 现行法规为准（官方核实）。

### 8.13 中国数据出境安全评估（PIPL / 数据安全法）与个人信息保护（workflow A / 注册）— 中国受试者数据的出境合规
- **场景 / 角色**：人类遗传资源办 / DPO — 含中国受试者的个人健康数据 / 人遗信息出境，须满足 PIPL《个人信息保护法》与《数据安全法》出境安全评估（呼应 §8.4 人遗、§8.5 GDPR）。
- **正确处理路径**：① **出境路径**：依 PIPL 个人信息出境可通过安全评估 / 标准合同 / 认证，重要数据须申报安全评估；② **与人遗叠加**：人遗材料 / 信息出境还须 §8.4 审批 / 备案，二者并行不替代；③ **去标识**：出境前假名化 / 去标识、密钥分离（呼应 §8.5）；④ **告知同意**：受试者单独同意与出境告知（契合 §2.2 持续同意）；⑤ **与监管**：跨境数据传输合规影响多中心与申报。
- **关键要点**：中国数据出境是 PIPL / 数据安全法 + 人遗条例的多重合规——安全评估与单独同意不可缺，与人遗审批叠加。
- ⚠️ PIPL / 数据安全法出境路径、安全评估阈值与单独同意要求为动态项，以中国《个人信息保护法》《数据安全法》及 CAC 现行规定为准（官方核实）。

### 8.14 临床试验结果登记与透明度（ClinicalTrials.gov / EU CTIS）（workflow A / G）— 结果公示义务
- **场景 / 角色**：注册事务 / 医学事务 — 试验须于公共登记平台注册并公示结果，满足透明度与法规义务（呼应 §8.6 发表透明度）。
- **正确处理路径**：① **注册**：关键试验于 ClinicalTrials.gov / 中国临床试验注册中心 / EU CTIS 等注册（方案 / 主要终点透明）；② **结果公示**：按平台时限提交结果摘要（疗效 / 安全），与 CSR / 注册一致（§5.3）；③ **与发表**：登记与发表一致，不得选择性报告（§8.6）；④ **辖区差异**：各国登记与结果公示要求不同；⑤ **衔接**：与 §7.1 申报衔接——登记信息支撑监管可信度。
- **关键要点**：结果登记是"透明度义务"而非可选——注册 + 结果公示 + 与申报发表一致构成公开可信。
- ⚠️ 登记平台、结果公示时限与内容要求为动态项，以 ClinicalTrials.gov、NMPA 注册平台与 EU CTIS 现行规定为准（官方核实）。

### 8.15 加快上市程序（fast track / 突破性疗法 / 优先审评）（workflow 注册）— 加速开发的监管路径
- **场景 / 角色**：注册事务 — 在研药物申请 FDA / EMA / NMPA 加快上市程序（fast track、breakthrough therapy、priority review、附条件批准 §5.4），须理解路径与承诺。
- **正确处理路径**：① **程序类型**：fast track（严重疾病 + 未满足需求）、breakthrough therapy（初步临床证据显著优于）、priority review（审评时限缩短）、rolling review；② **各辖区对应**：NMPA 有突破性治疗药物、优先审评、附条件批准（§5.4）、特别审批；③ **承诺**：加快程序常伴随上市后承诺（§4.10 PASS）与风险计划（§4.9 RMP）；④ **沟通**：须 Pre-IND / Type B（§8.11）预先确认资格与路径；⑤ **联动**：与 §3.8 单臂 / 附条件、§5.16 RWE 标签联动。
- **关键要点**：加快程序是"路径加速"非"标准降低"——须以更严的上市后承诺与沟通换取时间。
- ⚠️ 加快上市程序的资格、程序与承诺要求为动态项，以 FDA / EMA / NMPA 加快程序现行指南为准（官方核实）。

### 8.16 数据共享与个体水平数据（IPD）共享（workflow G / 透明度）— 研究数据对外共享的合规与治理
- **场景 / 角色**：医学事务 / 数据治理 — 申办方应监管要求或期刊政策对外共享临床试验数据（含个体水平数据 IPD），须平衡透明度、受访者隐私与知识产权。
- **正确处理路径**：① **共享层级**：从摘要级（CSR 摘要 / 结果登记 §8.14）→ 表级（TFL）→ 个体水平数据（IPD / 数据集），逐级开放、须事先规划；② **IPD 机制**：建数据申请门户、发布数据字典 / 分析说明、设使用协议（DUA）与独立评审委员会；③ **隐私与去标识**：IPD 须假名化 / 去标识、最少必要字段，契合 §8.5 GDPR / §8.13 PIPL 出境（出境须另行评估）；④ **同意基础**：共享范围须在 ICF（§2.1）/ 持续同意（§2.2）中预先告知，超范围须再同意；⑤ **知识产权与竞争**：设 embargo 期 / 发表政策（§8.6），防止选择性披露；⑥ **与登记**：登记平台元数据（§8.14）指向共享门户，构成透明度闭环。
- **关键要点**：数据共享是"有限开放、可追溯、受控 reused"——IPD 须去标识 + 使用协议 + 同意基础，与隐私 / 登记 / 透明度一致。
- ⚠️ IPD 共享政策、去标识标准、出境与同意要求为动态项，以 ICMJE / EMA / FDA / NMPA 数据共享与 PIPL 现行规定为准（官方核实）。

### 8.17 数据保护期与专利期补偿（workflow A / 注册）— 市场独占的组合布局
- **场景 / 角色**：注册 / 法务 — 创新药上市后享有的数据保护（data exclusivity）与专利期补偿（Patent Term Restoration / Supplementary Protection Certificate）是市场独占的重要机制。
- **正确处理路径**：① **数据保护**：原研新药 / 罕见病 / 儿童药等依辖区享不同年限数据独占，阻止仿制依赖原研数据申报；② **专利补偿**：因审评占用而损失的专利期可获延期（SPC / PTE），各辖区规则不同；③ **叠加策略**：数据保护 + 专利 + 市场独占（孤儿药 §5.11 / 儿科独占）组合布局；④ **与仿制 / BE（§5.20）**：数据保护期内仿制申报受限；⑤ **与加快程序（§8.15）**：优先审评缩短审评占用、影响补偿计算。
- **关键要点**：市场独占是"数据保护 + 专利补偿 + 特殊独占"组合拳——须按辖区分别测算布局。
- ⚠️ 数据保护年限、专利期补偿规则与儿科 / 孤儿独占为动态项，以各国药品数据与专利现行法规为准（官方核实）。

## 9. Official online retrieval & currency verification (workflow A)

### 9.1 Official entries ICH `https://www.ich.org/` (guideline index `https://www.ich.org/page/search-index-ich-guidelines`); NMPA `https://www.nmpa.gov.cn/`; CDE `https://www.cde.org.cn/`.

### 9.2 Retrieval process First turn the question into `jurisdiction + product + phase + topic + document type + activity date`; for each candidate document verify: official full title & issuing body; document number / version / Step / revision; official / draft / pending / superseded / withdrawn / historical status; release & implementation date; applicable product / population / phase / role / activity; section / clause / table / footnote / appendix supporting the conclusion; official page & attachment link; retrieval date. Search snippets only locate, do not replace the original; when PDF tables / footnotes / flowcharts / attachments affect meaning, check the corresponding page image; never judge currency by file-name version number alone.

### 9.3 Recommended search terms `full document name + release / implementation / attachment`; `site:ich.org topic + guideline + Step`; `site:cde.org.cn product / indication + 临床试验技术指导原则`; `site:cde.org.cn SUSAR / RSI / DSUR + 安全性`; `site:nmpa.gov.cn 药物临床试验质量管理规范 + 实施`; `site:nmpa.gov.cn 药品注册管理办法 + 临床试验`.

## 10. Conflict handling, citation & stop rules (workflow A)

Conflicts compared in order: jurisdiction & activity date → law / regulatory tier → official / pending / draft / historical → general vs product/therapeutic-area → problem scope & role → whether project approval / protocol / SOP is stricter. Unresolvable → state the conflict & impact, do not declare a document invalid on your own. Citation format: `document name (version / date), section or clause + official link + retrieval date`; explicitly mark `regulatory / mandatory requirement`, `formal technical guidance suggestion`, `draft / Q&A / example`, `methodology judgment`, `project practice suggestion`. Stop rule: when official site inaccessible / only secondary source / version-status conflict / missing body location / jurisdiction-date unknown and changes the conclusion → stop definitive judgment, output what is unconfirmed, why it cannot be confirmed, which conclusions are affected, conservative measures before verification, official site / search terms / fields to check, pages the user can return.

## 11. Minimal regulatory answer template (workflow A)
1. **Conclusion**: how far confirmation reaches now; 2. **Applicable boundary**: jurisdiction / product / phase / role / activity date; 3. **Document role**: what each applicable regulation / guidance resolves; 4. **Official basis**: document status / body location / link / retrieval date; 5. **Project impact**: on subjects / protocol / IB-RSI / data / statistics / operations / DSUR-CSR / filing; 6. **Immediate action**: owner / time point / record / escalation / closure evidence; 7. **Unverified items**: what is missing / impact / how to verify.
