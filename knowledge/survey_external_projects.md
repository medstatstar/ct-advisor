# 外部同类项目检索参考报告（GitHub + ClawHub / OpenClaw）

> 目的：为 ct-advisor 检索 GitHub 与 ClawHub / OpenClaw 生态中类似的临床试验 / 医疗 AI Agent 项目，提取可借鉴信息。 检索日期：2026-08-02 红线约束（全程有效）：本报告仅作本地参考，**不 git push / 不 publish**；涉及法规版本、动态项一律保留「官方核实」标记，不写入全文法规；任何落地改造须先与用户确认。

---

## 一、项目地图（按类型）

| # | 项目 | 类型 | 核心技术 | 与 ct-advisor 关联度 |
|---|------|------|----------|----------------------|
| 1 | A-xin946/clinical-trial-advisor | 同源 Skill 原始版 | Markdown 三参考结构 | 高（改编源头） |
| 2 | arnold117/clinical-trial-advisor | 镜像 fork | 同上 | 中（同步验证） |
| 3 | cyanheads/clinicaltrialsgov-mcp-server | ClinicalTrials.gov MCP | FastMCP / STDIO+HTTP | 中（data_intel 可复用） |
| 4 | pascalwhoop/medical-mcps（medical-research-toolkit） | 统一生物医学 MCP | 14+ 库统一端点 + ID 归一化 | 中（data_intel 后端） |
| 5 | CONSORT-RCT-Assistant (pouriamrt) | RAG + 幻觉护栏 | LangChain/LangGraph/Chainlit | 高（证据边界思想同构） |
| 6 | clinical-protocol-review (pooja-k-swamy) | 多智能体协议审阅 | LangChain + MCP 接口 + 风险评分 | 中（审阅范式） |
| 7 | Microsoft Prior-Authorization-Multi-Agent | 多智能体 + HITL + 审计 | 4 Agent + Pydantic 结构化输出 | 高（架构哲学契合） |
| 8 | Clinical-Trial-Success-Predictor | FAISS RAG + 元数据清单 | docs_manifest.csv | 中（知识库元数据控制） |
| 9 | NexClinicalMind | 合规自治哨兵 | Google ADK + Gemini + CrewAI + MCP | 低（CDISC 哨兵，超范围） |
| 10 | ClinTrialsGPT | A2A 协议 Agentic RAG | Agent-to-Agent | 低（协议层，暂不需） |
| 11 | OpenClaw-Medical-Skills (aradotso/hermes) | 医疗 Skill 集 | 869 模块 / FDA·CE·IEC62304·ISO14971 模板 | 中（监管模板参考） |
| 12 | 云知声五大医疗 Skill | 医疗助理（中文） | "活的医学逻辑引擎"后台 | 低（商业后台，不可复用） |
| 13 | Andyxcg/intelligent-triage-symptom-analysis | 症状分诊 | 650+ 症状 5 级分级 | 低（分诊，非试验设计） |

---

## 二、逐类可借鉴点详解

### 2.1 Markdown 定义智能体行为 —— 与 ct-advisor 架构高度契合（强验证）
- **Microsoft Prior-Authorization** 明确原则：*Agent behavior defined in markdown skill files, not Python code*；CMS 政策更新时**临床/合规人员改一个文本文件即可重新部署，无需工程 PR**。
- **ct-advisor 现状**：SKILL.md + `knowledge/ref-*.md` + `menu.yaml` + `workflows.yaml` + `system_prompt.md` + `prompts.md` 全套 Markdown/YAML 定义行为，动态项带「官方核实」标记。
- **结论**：外部成熟项目印证了 ct-advisor 的"知识即配置"设计是正确的。无需改动，建议**保持并强化**这一范式。

### 2.2 知识库元数据清单（docs_manifest 思路）—— 高契合、低成本
- **Clinical-Trial-Success-Predictor** 用 `docs_manifest.csv` 控制语料元数据（来源/版本/有效期）。
- **ct-advisor 现状**：`ref-regulatory-versions.md` 已有维护日期(2026-08-01)与官方核验入口，但三份主文件缺少统一"元数据头"。
- **建议**：为 `ref-clinical-operations.md` / `ref-regulatory-statistical.md` / `ref-regulatory-versions.md` 各加一个 YAML 头块或独立 `_manifest.yaml`：
  ```yaml
  file: ref-regulatory-statistical.md
  version: 2026-08-01
  source_urls: [ich.org, nmpa.gov.cn, fda.gov]
  last_verified: 2026-08-01
  next_refresh: 2027-02-01   # 每 6–12 月
  ```
直接支撑「官方核实」审计链，且便于将来压缩/拆分知识库时按优先级索引。

### 2.3 RAG + 幻觉护栏（Grounding Score / Hallucination Guard）—— 与证据边界同构
- **CONSORT-RCT-Assistant**：916 篇论文 RAG + Self-Query Retriever；每答案经 **LLM JSON 评分做 Grounding / Hallucination 检查**，低 grounding 直接拦截。
- **ct-advisor 现状**："证据边界 + 动态项官方核实"在思想上等价——答案必须可溯源、动态项须标注待核实。
- **建议（增强现有，不引入 RAG）**：在 `prompts.md` 增加一条硬规则——*任何事实性断言必须标注出处章节（如 §3.6）；无法标注来源者一律标记「官方核实」并提示用户核对*。这把 CONSORT 的"护栏"思想用纯方法论方式落地，不破坏"纯方法学不联网"红线。

### 2.4 MCP Server 接入注册库 / 生物医学库 —— 与 data_intel 层相关，但与 ct-registry 重叠
- **cyanheads/clinicaltrialsgov-mcp-server** v1.5.0（2025-10-15，覆盖率 92.46%，190+ 测试）：STDIO/HTTP 双传输；`find_eligible_studies`（患者匹配）、`compare_studies`、`time-series`；auth 支持 none/jwt/oauth；Apache-2.0。
- **pascalwhoop/medical-mcps**（medical-research-toolkit）：统一端点 `https://mcp.cloud.curiloo.com/tools/unified/mcp`，**100+ 工具覆盖 14+ 库**（ChEMBL/OpenTargets/ClinicalTrials.gov/PubMed/OpenFDA/OMIM/nodenorm 等）；nodenorm 做 ID 归一化；多数库免 key（OMIM/NCI 需 key）；MIT。
- **ct-advisor 现状**：纯方法学层**不联网、不调兄弟技能**；但 data_intel 层本就可调用本工作区已有的 **ct-registry 技能**（已覆盖 ClinicalTrials.gov/WHO ICTRP/CDE/PubChem）。
- **建议**：若 data_intel 需要实时数据，**优先复用 ct-registry 技能**，避免再引入 cyanheads/pascalwhoop MCP 造成双重维护。仅当 ct-registry 未覆盖某库（如 OpenFDA 药物警戒、ChEMBL 靶点）时，才考虑挂 pascalwhoop 统一端点。优先级：低–中。

### 2.5 多智能体协议审阅 + 风险评分 —— 未来增强项
- **clinical-protocol-review**：PI / Site Physician / Health Authority 三角色 Agent；MCP 接口按章节暴露协议；`risk_assessor` 给 Low/Medium/High 严重度；`scoring_engine` 给数值总分；Streamlit UI。
- **Microsoft Prior-Auth**：4 Agent（Compliance/Clinical Reviewer/Coverage/Synthesis）并行+顺序流水线；**结构化 Pydantic 输出（无 JSON 解析）**；**HITL 默认 LENIENT（不自动拒绝，需临床医师 Accept/Override 并记录理由）**；8 节审计 PDF。
- **ct-advisor 现状**：单 Agent 方法学顾问，Workflow A–K。
- **建议（未来，非当前）**：在协议设计类 Workflow（B 层方法学）增加"多视角审阅清单"——科学严谨性(PI)/可行性(Site)/法规符合(HA) 三栏 + 严重度分级 + 总分。结构化输出与 HITL 审计思想可直接纳入 `prompts.md` 的输出模板。架构改动较大，待用户确认后再做。

### 2.6 ClawHub / OpenClaw 发布模式 —— 可选，受红线约束
- pascalwhoop 将 medical-mcps + medical-research-toolkit 作为 OpenClaw Skill 发布；OpenClaw-Medical-Skills 含 869 模块；云知声强调"活的医学逻辑引擎"后台持续更新。
- **ct-advisor 现状**：本地技能，用户已明确"保持本地不 commit / 不 publish"。
- **建议**：仅记录为**未来可选动作**——若未来要发布到 ClawHub，可参考 pascalwhoop 的 SKILL.md + OPENCLAW-USAGE.md 结构。当前红线：**不发布，等用户确认**。

---

## 三、与 ct-advisor 现有架构契合度矩阵

| 外部模式 | ct-advisor 对应层 | 契合度 | 落地成本 | 备注 |
|----------|-------------------|--------|----------|------|
| Markdown 定义行为 | SKILL.md + ref-*.md | ★★★★★ | 无（已具备） | 外部验证设计正确 |
| 知识库元数据清单 | ref-*.md 头块 | ★★★★★ | 低 | 直接支撑官方核实 |
| 幻觉护栏 / Grounding | 证据边界 + prompts.md | ★★★★☆ | 低 | 加溯源硬规则即可 |
| 结构化输出 + HITL 审计 | prompts.md 输出模板 | ★★★★☆ | 中 | 增强审阅类 Workflow |
| 多智能体协议审阅 | B 层方法学 Workflow | ★★★☆☆ | 高 | 架构扩展，待确认 |
| 注册库 MCP（cyanheads） | data_intel 层 | ★★☆☆☆ | 中 | 与 ct-registry 重叠 |
| 统一生物医学 MCP | data_intel 层 | ★★☆☆☆ | 中 | 仅补 ct-registry 盲区 |
| ClawHub 发布 | 发布流程 | ★☆☆☆☆ | 低 | 红线：等确认 |
| A2A / CDISC 哨兵 | — | ☆☆☆☆☆ | — | 超范围，不采纳 |

---

## 四、可落地建议（按优先级，标注红线）

1. **【高·低成】加知识库元数据头**：为三份 ref-*.md 增 YAML 头（version/source_urls/last_verified/next_refresh）。本地改动，不 push。
2. **【高·低成】prompts.md 增"溯源硬规则"**：事实断言必须标 §章节，无来源标「官方核实」。强化证据边界，不联网。
3. **【中·中成】输出模板增结构化 + HITL 审计段**：审阅/设计类答案带严重度分级与"需人工核实"提示。
4. **【低·中成】data_intel 实时数据优先复用 ct-registry**：避免重复挂外部 MCP。
5. **【可选·红线】ClawHub 发布**：仅当用户明确确认后再做。

---

## 五、不建议采纳 / 需谨慎的点

- **NexClinicalMind（CDISC 合规哨兵）、ClinTrialsGPT（A2A）**：超出 ct-advisor「方法学顾问」范围，且引入持续联网自治，与"纯方法学不联网/证据边界"红线冲突。
- **云知声"活的医学逻辑引擎"**：依赖商业后台自动更新，与"动态项官方核实 + 手动每 6–12 月刷新"的本地可控策略相悖，不采纳其自动更新哲学。
- **重复引入外部 MCP**：ct-registry 已覆盖主要注册库，再挂 cyanheads/pascalwhoop 会造成双重维护与版本漂移风险。

---

*本报告为本地参考文档，所有落地改造须先与用户确认；红线（不 push / 不 publish / 动态项官方核实）全程有效。*
