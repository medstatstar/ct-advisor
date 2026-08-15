# User-Facing Prompt Strings (bilingual) / 面向用户的提示语（双语）

> This file is the **agent-facing mirror** of `scripts/i18n.py`. In local mode the methodology agent reads this table to render clarification questions, menus, warning boxes, QC labels and stop messages. `scripts/i18n.py` is the machine-readable single source of truth for the Coze backend / any future CLI — **keep the two in sync**.

> 本文件是 `scripts/i18n.py` 的**面向 Agent 镜像**。本地模式下方法学 Agent 读取本表来生成澄清问题、菜单、警示框、QC 标签与停止提示。`scripts/i18n.py` 是供 Coze 后端 / 未来 CLI 使用的机器可读单一来源——**两者须保持一致**。

## Language rule / 语言规则（来自 ct-base `references/language_policy.md`）

- **Default: follow OS locale.** Chinese on `zh-*` OS or when the user writes in Chinese; English otherwise — no explicit request needed. One-sentence switch: say "switch to English" / "用中文回复" (this conversation) or "always use X" / "永久用X" (persists the preference across sessions). / 默认跟随系统区域：`zh-*` 系统或用户用中文时输出中文，否则英文，无需显式要求。一句话切换：说「用中文回复」/"switch to English"（仅本次对话），或「永久用X」/"always use X"（跨会话持久化偏好）。
- **Render only the active language.** Do not mechanically append an English translation after a Chinese heading (and vice versa). / 只输出当前语言；不要在中文标题后机械附带英文翻译（反之亦然）。
- **Code output (R / Python) is always English** and unaffected by this policy. / 代码输出（R / Python）始终为英文，不受本策略影响。
- In any bilingual doc, join EN and ZH on the same line with ` / ` (slash, spaces both sides); never use `|` (Markdown column delimiter). / 双语文档中，中英文一律用 ` / `（斜杠，两侧空格）连同一行；不要用 `|`。
- Placeholder `{...}` in ZH strings keep the same name as EN (e.g. `{profile}`, `{source}`, `{date}`). / 中文串中的占位符 `{...}` 与英文同名。

## Prompt table / 提示语对照表

### Generic / 通用
- `generic.think_first`: Let me think this through before answering. / 我先梳理一下再回答。
- `generic.proceed`: Proceeding on the stated assumptions. / 基于所述假设继续。
- `generic.need_more`: To give a precise answer I need to confirm a few things first: / 为给出准确结论，我需要先确认几点：

### Clarification gate (gate 0) / 澄清门
- `clarify.understand_as`: I understand your question as: {profile} / 我理解您的问题为：{profile}
- `clarify.offer_options`: Which of the following best matches your need? (pick 1–3) / 以下哪一项最符合您的需要？（可多选 1–3 项）
- `clarify.insufficient`: The question is not yet specific enough to decide. Please clarify: / 问题尚未明确到可下结论，请补充：
- `clarify.high_risk_intro`: Before the formal answer, let me confirm my understanding of the problem profile: / 在给出正式结论前，我先确认一下对问题画像的理解：
- `clarify.not_impersonate`: I can explain why this is needed or give urgent safety actions, but I won't pretend a project-specific formal conclusion from general principles alone. / 我可以解释为何需要该信息，或给出紧急安全措施，但不会仅凭一般原则冒充针对项目的具体正式结论。
- `clarify.grill_intro`: Let's pin down what you actually need. I'll ask 1–3 focused questions per round; each comes with a recommended default — confirm or adjust. No data fetch, no handoff to other skills. / 我们先把您真正需要的理清楚。我会每轮问 1–3 个聚焦问题，每个都附带推荐默认答案——您确认或调整即可。不取数、不转交其他技能。
- `clarify.grill_summary`: Here is your needs portrait and my recommended route: / 这是您的需求画像与我的推荐路由：
- `clarify.triage_simple`: Quick answer below — just say the word if you want me to open the full menu or go deeper. / 下面直接给结论——若需要我打开完整菜单或进一步展开，告诉我即可。
- `clarify.vague_invite`: Your question is still open-ended — let's pin it down step by step via the Local Clarify Loop: I'll ask 1–3 focused questions per round, each with a recommended default. / 您的问题仍比较开放——我们用本地澄清菜单（Local Clarify Loop）逐轮把它理清楚：每轮问 1–3 个聚焦问题，每个都带推荐默认答案。

### Workflow routing menu (A–J + gate 0) / 工作流路由菜单
- `menu.title`: Which workflow best fits your need? / 哪个工作流最符合您的需要？
- `menu.gate0`: 0 · Clarify / scope the question / 0 · 厘清问题范围
- `menu.A`: A · Explain & locate evidence / A · 概念解释与证据定位
- `menu.B`: B · Trial design / B · 试验设计
- `menu.C`: C · Statistics & estimands / C · 统计与估计目标
- `menu.D`: D · GCP & quality / D · GCP 与质量
- `menu.E`: E · Clinical operations / E · 临床运营
- `menu.F`: F · Safety & DSUR / F · 安全性与 DSUR
- `menu.G`: G · Documents & reports / G · 文件与报告
- `menu.H`: H · Methodology QC / H · 方法学 QC
- `menu.I`: I · User tone writing / I · 用户语气写作
- `menu.J`: J · Local memory / J · 本地记忆

### Clarification menu (gate 0 → decidable) / 澄清菜单（gate 0 → 可决策） > Tree: `scripts/menu.json`. Two entry flows split by a `capability` tier: methodology (`ground → capability → intent area → workflow → sub-intent → output`) and data_intel (`ground → capability → data_skill → data_subintent → output`). The `intent` tier splits into area + workflow because one question caps at 4 options. / 菜单树见 `scripts/menu.json`。两条入口流程由 `capability` 层分流：methodology（背景 → 能力 → 领域 → 工作流 → 子意图 → 输出）与 data_intel（背景 → 能力 → 数据技能 → 数据子意图 → 输出）。因单题最多 4 选项，「意图」拆为领域+工作流两步。

- `menu.ground.title`: Quick context (helps me scope the answer) / 快速背景（帮助我界定回答范围）
- `ground.role.q`: Your role? / 您的角色？
- `ground.role.sponsor`: Sponsor (medical / stats) / 申办方（医学 / 统计）
- `ground.role.cro`: CRO / CRA / CRO / CRA
- `ground.role.investigator`: Investigator / site / 研究者 / 研究中心
- `ground.role.reg`: Regulatory affairs / 注册事务
- `ground.role.other`: Other / 其他
- `ground.stage.q`: Development stage of the asset? / 在研品种所处阶段？
- `ground.stage.preind`: Pre-IND / IND 前
- `ground.stage.ph1`: Phase I / I 期
- `ground.stage.ph2`: Phase II / II 期
- `ground.stage.ph3`: Phase III / III 期
- `ground.stage.ph4`: Phase IV / IV 期
- `ground.stage.postmarket`: Post-marketing / 上市后
- `ground.stage.nda`: NDA / BLA filing / NDA / BLA 申报
- `ground.stage.unsure`: Not sure yet / 还不确定
- `ground.input.q`: What do you have in hand? / 您手头有什么？
- `ground.input.question`: Just a question / 仅一个问题
- `ground.input.protocol`: Draft protocol / 方案草稿
- `ground.input.sap`: SAP / 统计分析计划（SAP）
- `ground.input.csr`: CSR / 临床研究报告（CSR）
- `ground.input.safetydb`: Safety database / 安全性数据库
- `ground.input.otherdoc`: Other document / 其他文件
- `ground.input.none`: Nothing yet / 还没有
- `menu.intent.title`: Which area fits your need? / 哪个领域符合您的需要？
- `menu.intent.q`: Pick an area (workflows shown next): / 选择一个领域（下一步显示具体工作流）：
- `menu.area.design_stats`: Trial design & statistics (B, C) / 试验设计与统计（B, C）
- `menu.area.safety_ops`: Safety & clinical operations (E, F) / 安全性与临床运营（E, F）
- `menu.area.docs_qc`: Documents & methodology QC (G, H) / 文件与方法学 QC（G, H）
- `menu.area.explain_other`: Explain / GCP / writing / memory (A, D, I, J) / 解释 / GCP / 写作 / 记忆（A, D, I, J）
- `menu.workflow.title`: Which workflow? / 哪个工作流？
- `menu.workflow.q`: Pick the closest workflow: / 选择最贴近的工作流：
- `menu.sub.title`: What specifically do you need? / 您具体需要什么？
- `menu.sub.q`: Pick a sub-intent: / 选择一个具体意图：
- `menu.sub.A.define_term`: Define a confused term / 厘清一个易混概念
- `menu.sub.A.find_basis`: Find the current official basis / 查找现行官方依据
- `menu.sub.A.compare_guide`: Compare guidelines / 对比不同指导原则
- `menu.sub.B.design_new`: Design a new trial / 设计新试验
- `menu.sub.B.critique`: Critique / optimize an existing design / 评审 / 优化现有设计
- `menu.sub.B.endpoints_estimand`: Endpoints & estimand / 终点与估计目标
- `menu.sub.B.adaptive`: Adaptive / enrichment feasibility / 适应性 / 富集设计可行性
- `menu.sub.C.estimand_setup`: Set up estimand & estimator / 设定估计目标与估计量
- `menu.sub.C.samplesize`: Sample-size plan (→ ct-samplesize) / 样本量方案（→ ct-samplesize）
- `menu.sub.C.missing_data`: Missing data & sensitivity / 缺失数据与敏感性分析
- `menu.sub.C.ni_eq`: Non-inferiority / equivalence / 非劣效 / 等效
- `menu.sub.D.deviation_capa`: Deviation / CAPA handling / 偏离 / CAPA 处理
- `menu.sub.D.audit_ready`: Audit / inspection readiness / 稽查 / 核查准备
- `menu.sub.D.consent_irb`: Informed consent / IRB / 知情同意 / IRB
- `menu.sub.E.enroll_feas`: Enrollment forecast / feasibility / 入组预测 / 可行性
- `menu.sub.E.monitoring_vendor`: Monitoring / site / vendor / 监查 / 中心 / 供应商
- `menu.sub.E.dblock_ready`: Database-lock readiness / 数据库锁定准备
- `menu.sub.E.reg_path`: Regulatory submission pathway / 注册申报路径
- `menu.sub.F.susar`: Individual SUSAR / expedited report / 个例 SUSAR / 快速报告
- `menu.sub.F.dsur`: DSUR preparation / DSUR 撰写
- `menu.sub.F.signal`: Safety signal / 安全性信号
- `menu.sub.F.benefit_risk`: Benefit–risk assessment / 获益 - 风险评估
- `menu.sub.G.csr_review`: CSR review / CSR 评审
- `menu.sub.G.protocol_review`: Protocol review / 方案评审
- `menu.sub.G.sap_review`: SAP review / SAP 评审
- `menu.sub.G.draft_section`: Draft a section from scratch / 从零起草某章节
- `menu.sub.H.design_qc`: Design QC / 设计 QC
- `menu.sub.H.document_qc`: Document QC / 文件 QC
- `menu.sub.H.crossfile`: Cross-file consistency / 跨文件一致性
- `menu.sub.H.submission_ready`: Submission readiness / 申报就绪度
- `menu.sub.I.reply_tone`: Reply in my tone / 用我的语气回复
- `menu.sub.I.rewrite`: Rewrite a draft / 重写草稿
- `menu.sub.J.recall`: Recall prior context / 回顾既往上下文
- `menu.sub.J.save_pref`: Save a preference / 保存一项偏好
- `menu.out.title`: Preferred output format? / 偏好哪种输出形式？
- `menu.out.q`: How should I deliver? (default: just answer) / 希望以何种形式交付？（默认：直接回答）
- `out.format.advisory_memo`: Advisory memo (structured) / 咨询备忘录（结构化）
- `out.format.checklist`: Checklist / 检查清单
- `out.format.redline_review`: Redline review / 修订批注式评审
- `out.format.option_compare`: Option comparison / 方案对比

### Methodology QC labels (workflow H) / 方法学 QC 标签
- `qc.overall`: Overall judgment / 总体结论
- `qc.verdict.acceptable`: Acceptable / 可接受
- `qc.verdict.conditional`: Acceptable with conditions / 有条件接受
- `qc.verdict.unacceptable`: Unacceptable / 不可接受
- `qc.issue_list`: Issue list (issue / evidence / impact / priority) / 问题清单（问题 / 证据 / 影响 / 优先级）
- `qc.remediation`: Remediation plan / 整改方案
- `qc.gap`: Information gap (what is missing / who provides / impact on judgment) / 信息缺口（缺什么 / 由谁提供 / 对结论的影响）
- `qc.next_gate`: Next quality gate (what must be met before the next stage) / 下一质量门（进入下一阶段前须满足的条件）

### Warnings / stop rules / 警示与停止规则
- `warn.verify_incomplete`: Verification not yet complete — no definitive judgment on items depending on this basis. / 核实尚未完成——对依赖该依据的事项不下确定结论。
- `warn.unconfirmed`: Unconfirmed items — why unconfirmable — what judgment this affects: / 未能确认项——为何无法确认——影响哪些结论：
- `warn.complex_patience`: The analysis is running — please wait for the result. / 分析正在进行，请稍候结果。
- `stop.tracing`: Definitive judgment withheld. Official tracing path below; please return the original for re-check. / 不下确定结论。官方溯源路径如下，请返回原文复核。
- `stop.no_risk_mask`: Do not use "no risk found" to mask unreceived or unreconciled data. / 不得用「未发现风险」掩盖未收到或未核对的资料。
- `stop.fabricate`: Do not fabricate sample size, deadline, effect size or risk conclusion when key parameters are missing. / 关键参数缺失时，不得编造样本量、时限、效应量或风险结论。

### Official tracing card / 官方溯源卡
- `trace.title`: Official tracing card / 官方溯源卡
- `trace.body`: Applicable body & entry / suggested document or topic / copyable search terms / document number, version, status, implementation date, scope / body clause / page or PDF to return / 适用机构与入口 / 建议文件或主题 / 可复制检索词 / 文号·版本·状态·实施日·范围 / 正文条款 / 待返回页面或 PDF
- `trace.retry`: Please return the original page/PDF so I can re-check against the official source. / 请返回原始页面/PDF，以便我对照官方来源复核。

### AskUserQuestion option templates / 选项模板
- `ask.adopt`: Adopt the above / 采用以上
- `ask.revise`: Revise / 修改
- `ask.cancel`: Cancel / 取消
- `ask.confirm_assumption`: Continue under the following assumptions? / 在以下假设下继续？

### Source-tier labels (evidence boundary) / 来源层级标签
- `src.mandatory`: Regulatory / mandatory requirement / 法规 / 强制要求
- `src.guidance`: Guidance suggestion / 指导建议
- `src.judgment`: Methodology judgment / 方法学判断
- `src.practice`: Project practice suggestion / 项目实践建议

### Grounding rule (cite § or mark 官方核实) / 溯源硬规则（标注章节或官方核实） > **Hard rule (from `survey_external_projects.md` §2.3 — CONSORT grounding-guard idea, methodology-only landing)**: Every factual / normative assertion in the answer **must carry a traceable source** — cite the specific `ref-*.md` section (e.g. `§3.6`) or an official document clause. If a claim cannot be traced to a source, it **must be flagged `⚠️ 官方核实`** and the user told to verify against the official original; do not present untraceable claims as settled fact. / **硬规则（源自 `survey_external_projects.md` §2.3——CONSORT 护栏思想，纯方法论落地）**：回答中每条事实性 / 规范性断言**必须可溯源**——标注具体 `ref-*.md` 章节（如 `§3.6`）或官方条款。若无法溯源，须标记 `⚠️ 官方核实` 并提示用户对照官方原文核实；不得把无法溯源的断言当作确定结论。
- `grounding.require_cite`: This point is based on {ref} §{section}; verify against the official original if used for a filing / decision. / 该点依据 {ref} §{section}；若用于申报 / 决策，请对照官方原文核实。
- `grounding.official_verify`: ⚠️ 官方核实 / Officially verify — I cannot confirm the current version / status / deadline from static content; please check the official source. / 我无法凭静态内容确认现行版本 / 状态 / 截止日，请查官方来源。
- `grounding.low_confidence`: Source not found for this claim — treated as unverified, not stated as fact. / 该断言未找到来源——按未核实处理，不作事实陈述。

### Data grounding & handoff hints / 数据接地与转交提示
- `ground.performed`: Data grounding performed: {source} on {date}. / 已执行数据接地：{source}（{date}）。
- `ground.skipped`: No data grounding performed (pure methodology / design / compliance question). / 未执行数据接地（纯方法学 / 设计 / 合规问题）。
- `handoff.samplesize`: Sample-size parameters complete → handing off to `ct-samplesize` for computation (this skill does not compute n in-house). / 样本量参数齐全 → 转交 `ct-samplesize` 计算（本技能不内置计算 n）。

### Routing (absorbed ct console: total entry) / 路由（吸收 ct 控制台：总入口）
- `menu.cap.title`: Which kind of help do you need? / 您需要哪一类帮助？
- `menu.cap.q`: Pick a capability (routes your request): / 选择能力类别（决定请求路由）：
- `menu.cap.methodology`: Methodology & regulatory advice (design / stats / compliance / QC) / 方法学与法规顾问（设计 / 统计 / 合规 / QC）
- `menu.cap.data_intel`: Real data & competitive intel (registry / safety / literature) / 真实数据与竞品情报（注册 / 安全性 / 文献）
- `menu.cap.clarify`: Clarify my needs first (I'm not sure what I want) / 先帮我理清需求（我还不确定要什么）
- `menu.ct_registry`: Trial-registry landscape (CT.gov / CDE / WHO ICTRP / EU-CTR / ChiCTR / ISRCTN / DRKS) / 试验注册格局（CT.gov / CDE / WHO ICTRP / EU-CTR / ChiCTR / ISRCTN / DRKS）
- `menu.ct_safety`: Safety signals (FAERS PRR / ROR / IC) / 安全性信号（FAERS PRR / ROR / IC）
- `menu.ct_literature`: Published literature (OpenAlex / Europe PMC / Semantic Scholar) / 已发表文献（OpenAlex / Europe PMC / Semantic Scholar）
- `menu.ct_competitive`: Full competitive-intel brief (call registry + safety + literature, stitch in-house ⭐) / 完整竞品情报简报（调用注册 + 安全性 + 文献三源，本技能缝合 ⭐）
- `menu.explain_diff`: Can't decide? → say "explain the differences", I'll clarify before you choose / 还拿不准？→ 说「详细解释差异」，我先讲清再让你决定（Complex 路由菜单必带的 §4.4 入口，详见 `ct-base/references/search_menu.md §4.4`）
- `menu.data_skill.title`: Which data source? / 哪个数据源？
- `menu.data_skill.q`: Pick the data skill to invoke: / 选择要调用的数据技能：
- `menu.data_subintent.title`: How should I proceed? / 如何继续？
- `menu.data_subintent.q`: Run now, or scope the search first? / 直接运行，还是先聚焦检索范围？
- `menu.data_subintent.run`: Run now (the skill asks follow-ups inline) / 直接运行（技能内联追问）
- `menu.data_subintent.focus`: Scope first (drug / indication / time window / comparator set) / 先聚焦范围（药物 / 适应症 / 时间窗 / 对照集）
- `route.trigger_data`: Routing to data skill `{skill}` for real-data retrieval (via Skill tool). / 正在路由到数据技能 `{skill}` 获取真实数据（通过 Skill 工具）。

### Boundary / red line reminder / 边界与红线提示
- `boundary.no_pii`: Note: I will not expose personal info, subject info, unpublished project data, private paths or access credentials in the answer. / 提示：我不会在回答中泄露个人信息、受试者信息、未公开项目数据、私有路径或访问凭据。
