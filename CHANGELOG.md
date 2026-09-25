# Changelog

## [Unreleased] — 2026-09-25 · >5MB 附件路径修正：转 md 后按 .md 附件上传（用户指正）

- **原错误**：entry.py `_handle_attachment_oversized` 把 >5MB 附件转 md 后**拼进 question 文本**且不上传（"附件未上传，仅本地解析"）——文档结构、分块检索与「文档§N」引用全部失效。
- **正确行为（用户口径）**：>5MB → 本地转 Markdown（office_to_md / 直读），**把 .md 写成临时文件后按 <5MB 同一条 doc_context 通道上传**（/upload_file → mode=file_id），并附 ℹ️ 提示"云端基于转换后的 md 作答"。
- 实现：`_handle_attachment_oversized` 返回 `(question, doc_context)` 二元组；临时文件 `%TEMP%/ctadv_<stem>_oversized.md`；SKILL.md / AGENTS.md 管线图与附件矩阵同步修正。
- **回归**：8.6MB txt 端到端——Coze 正确引用文档**尾部** END_MARKER 编号（7391，§4286），证明上传+分块检索真实生效；<5MB docx 路径不变；py_compile 通过。

## [Unreleased] — 2026-09-25 · v1.2.0 框架整理（用户："技能内容复杂了，整理框架使流程更清楚"）

- **文档-代码对齐**：SKILL.md / AGENTS.md 此前仍写旧流程（OOXML 本地转 md 追加 question、
  4 档难度分级）。重写为 v1.1.0 修正后的**规范 5 步管线**：① 附件门（<5MB 原文件上传→
  doc_context / >5MB 本地转 md 拼问题）→ ② vague 门（唯一难度判定，is_vague 纯正则）→
  ③ 澄清循环 → ④ orchestrate 直发 Coze → ⑤ delegate 缝合 + 定界符/sha256 输出。
  frontmatter `network_note` 同步。
- **死代码删除（coze-only 重构遗留，主链 0 引用）**：`adapters/backend.py` /
  `data_context.py` / `qa_store.py`（早期 LocalBackend+QA 日志 seam，与 coze-only 红线冲突）、
  `_patch14*.py`、`drug_name_resolver / keyword_breadth / landscape_scorer / source_guard /
  r_libs`、`workflows.json`、`menu.json`、`test_modeB.py`。`adapters/__init__.py` 瘦身为
  仅 refiner/sanitize 出口（build_backend/build_data_context/build_qa_store 一并删除）。
- **快照目录清理（~185 MB）**：`_TRASH-20260924-clean`、`scripts.park-20260924-attach/-p2`、
  `adapters/coze.park-20260924-fixedeps/-v125`、`workbench.park-20260924-wbpatch`（git rm）、
  `out/`。当前部署源 = `adapters/coze/`（源码）+ `workbench/`（本地壳），park 系列全部是
  9-24 之前的旧副本。
- **AGENTS.md 新增模块分层图**（L0 入口 / L1 编排 / L2 适配 / L3 支撑），
  `scripts/entry.py` 为唯一可调用面的边界声明。
- **回归**：删除后 6 套测试 155/155 全绿（test_local_doc_payload 的 menu.json 断言改用
  tool_mapping.json 同扩展名样本）；entry.py 主链 import + 端到端 Coze 问答复测通过。
- 版本 1.1.0 → **1.2.0**。

## [Unreleased] — 2026-09-25 · 代理容错全覆盖 + doc_context 透传断链修复

- **代理容错（用户问"以后还会不会错走代理"引出）**：
  1. `adapters/refiner.py` `_call_coze`：绕过代理直连重试的条件扩为 `ProxyError/ConnectionError/ReadTimeout`（此前半死代理——能建 TCP 但不转发 HTTPS——导致的 ReadTimeout 不在重试范围）。实测死代理 `127.0.0.1:59999` 下主链路正常返回。
  2. `scripts/doc_memory.py` `_coze_upload_available` 探测：原实现网络异常直接判"不可用"→ 死代理下永远回退老通道。改为与 refiner 同策略：失败 → `ProxyHandler({})` 直连重试一次。
  3. `scripts/doc_memory.py` `upload_to_coze`：补同款两步重试 + **urllib 陷阱修复**——`Request` 对象经历代理路由失败后内部残留代理状态，复用同一 req 绕过重试仍打死代理；重试必须用**全新 Request**（headers 暂存后重建）。实测死代理下真实上传成功（file_id 返回）。
- **doc_context 透传断链（严重）**：`scripts/orchestrate.py` `_build_request` 只取 query_meta/original_question/draft_answer 三字段，entry.py 构建的 `doc_context`（附件载荷）被**静默丢弃** → Coze 永远收不到附件，表现为"你未提供文档内容"。修复：`_build_request` 透传 `doc_context/scope_hint/conversation_history/is_followup`。
- **entry.py 附件通道升级**：`_handle_attachment_normal` 显式 `allow_upload=True` 强制 file_id 上传通道（Coze 原生解析原始文件，保真度高于 base64 内联转发）；`instruction` 改用用户真实问题；内部失败自动降级老通道。
- **回归（死代理 + 正常代理双环境）**：① 无附件简单题 → Coze 正常；② 带 36.8KB docx → Coze 按「文档§1-§5」结构化引用附件内容作答 ✓；③ 上传探测/真实上传死代理下绕过成功 ✓。

## [Unreleased] — 2026-09-24 · 文档上传 Coze 终端：file_id 真实上传通道（v1.25）

- **依据**：用户 2026-09-24 08:56 需求——飞书归档暂停，优先做"文档上传到 Coze 终端"；
  ≤5MB 传原文件给 Coze 解码，>5MB 本地转 MD 后上传；新/老 Office 格式统一流程。
- **冲突（读源码核实）**：现有 `mode=file`+`file_b64` 内联上限 ≈3.75MB 且只接老格式；
  `GraphInput` 仅 `doc_context` JSON 字符串字段，无文件上传入口。
- **方案**：file_id 真实上传（绕开 3.75MB 上限，任意大小 Office 可传）；5MB 分流仅本地"传原文件还是 MD"的判断，传输统一为一次 file_id 上传；新/老格式走同一条路。
- **服务端改动（Coze v1.25，需重新上传部署包生效）**：
  1. `src/utils/file/upload_store.py`（新增）：自托管临时落盘（`/tmp/coze_uploads/<file_id><ext>`），50MB 上限，uuid.hex 命名。
  2. `src/main.py`：新增 `/upload_file` 端点（multipart，鉴权/限流与 `/run` 同源，平台前置校验）；回传 `file_id`/`file_name`/`size`。
  3. `src/doc/payload.py`：`DocPayload` 新增 `file_id`/`file_url` 字段 + `is_file_id` 属性；mode 推断新增 `file_id` 退化规则（不复用 `mode="file"`）。
  4. `src/doc/__init__.py`：新增 `_decode_file_id`（调 `upload_store.resolve_path` → `office_reader.read_bytes`，OLE2+OOXML 通用）；`ingest_and_select` 在 `is_file` 分支后加 `is_file_id` 分支；`doc_ingest_node` 无需改动（`file_error` 统一分支已覆盖）。
- **本地改动**：`scripts/doc_memory.py` 新增统一上传入口 `build_upload_payload`/`upload_to_coze`/`prepare_file_upload`；5MB 分流（`UPLOAD_THRESHOLD_BYTES=5*1024*1024`）；OOXML 不再本地转文本，改为传原文件。
- **向后兼容**：旧 `mode=file`+`file_b64` 内联路径保留（回退）；老 Coze 未读 `file_id` 字段 → 静默走旧路径。
- **决策**（用户拍板）：① file_id 取回 = 工作流侧直接调 Coze API（当前实现为服务端自托管落盘 + 内部路径解析，一行可切真 `files.retrieve`）；② 合规 = 暂不设 TTL，未来飞书清理；③ 限流 = 与 `/run` 同源；④ mode 命名 = 新增 `file_id`。

## [Unreleased] — 2026-09-23 · 作答契约 C14：交付物边界（不返回修改后的文档）

- **依据**：用户口径——用户索要「改好的 / 修改后的文档」时，**直接提示「目前不提供此功能」**，
  只能提供修改建议等文字信息。
- **服务端改动（coze v1.24：需重新上传部署包才生效）**：
  1. `config/full_analysis_cfg.json`（sp）：新增作答契约 **C14 交付物边界**（位于「文档类请求的
     参考性边界」之后、「模板归纳请求」之前），自检清单新增**第 26 条**；顶部注释 `C1-C13` → `C1-C14`。
  2. `config/shared_contract.md`：补 **C14 全文**，并补 **C13 指针**——修掉「C1-C13 唯一落点」
     与文件实际只写到 C12 之间的既存漂移。
  3. `config/review_cfg.json`：镜像精简版 C14（含核查动作：发现文件承诺必须删除并补声明，保留文字建议部分）。⚠️ 该文件是 `pack.py` **明确排除**的孤儿配置（review 节点 v1.20 已移除）→ **不进运行镜像**，仅同步留档。
  4. 代码层：`src/graphs/nodes/answer_postprocess.py` 新增 `ensure_deliverable_boundary` /
     `asks_for_deliverable_file`（确定性判定 + 幂等前置固定能力说明）；
     `full_analysis_node.py` 在 accuracy 提取后、**写缓存前** 调用（与 C12 范围声明同层、同
     `substance_len` 空答案防线）→ 缓存命中的答案同样带该说明。
  5. `_doc_prompt_directive` 新增第 7 条（文档在场时首句声明 + 转为可直接替换的文字措辞）。
- **新增自测**：`tests/test_deliverable_boundary.py`（59 项：判定正/负例、四态与幂等、
  契约落点、接线顺序）。
- **本地文档**：`SKILL.md` 附件章节新增第 8 条、`AGENTS.md` 新增交付物边界小节、
  `adapters/coze/docs/deliverable-boundary.md`（新增专文）、`coze_modification_guide.md` §八、
  `ct-base §6.8`（底座对等条款）。
- **兼容性**：入口契约字段未变 → **可单独升级 Coze 端**（不要求与本地同期，区别于 v1.23）。

- **回归中发现并修复的既有缺陷（审计器 L4 长期静默失效）**：`scripts/test_adapter_audit.py`
  的 `MODULES` 仍列出 v1.20 已中性化的 `graphs.nodes.review_node` /
  `graphs.nodes.validity_check_node`（现为 `*.py.disabled`）→ L3 必然 `ModuleNotFoundError`
  → `ok=False` → **整个 L4 被跳过**（L4a 图装配一致性、L4b 写闸×范围声明不变量、
  L4d 基线 md5 比对从未执行）。修法：L3 **自行识别同名 `.py.disabled` 并跳过**
  （名字保留作历史记录，对未来再次中性化的节点免疫）。修后审计 `PASS=10 → 23 / FAIL=0`，L4 恢复执行。

## [Unreleased] — 2026-09-21 · 作答契约 C13：需求分解与 B 类能力边界

- **依据**：用户反馈——多子需求问题（如"请给出 1/2/3/4"）被混为一谈逐点输出，且涉及 B 类技能
  （`ct-protocol` / `ct-csr` / `ct-analysis` 等）专业范围的内容被本技能"硬答"，质量不可接受。
  需要：① 先拆解子需求、逐一判定；② 对 B 类范围子需求输出"专业提示 + 兜底答案"两段式。
- **服务端改动（coze：需重新上传部署包才生效）**：
  1. `config/full_analysis_cfg.json`（sp）：新增作答契约 **C13 需求分解与能力边界感知**（位于 C11 之后、自检之前），
     含 B 类技能清单（`ct-protocol` / `ct-csr` / `ct-analysis` / `ct-sdtm` / `ct-eligibility` / `ct-synthdata`）
     及"提示段 + 兜底段"两段式输出规范；自检清单新增第 24/25 条 C13 检查项。
  2. 修复 sp 内残留的 `review_cfg.json` 注释（改为"C1-C13 唯一落点"）。
- **本地文档**：`SKILL.md`（C13 加入契约摘要 + Tier B 描述对齐）、`coze_modification_guide.md`
  （作答契约内容补 C11/C12/C13）、`CHANGELOG.md`（本条目）。

## [Unreleased] — 2026-09-21 · 移除答案双重核查（v1.20 架构简化）

- **依据**：v1.16~v1.19 的「答案双重核查」层（`review` / `review_guard` 节点 + 前置 `validity_check` 门）
  实际 0% 命中——`draft_answer` 上游恒定空，`validity_check` 永远判无效 → 全流量走 `full_analysis`，
  双核查等于没生效；且 `full_analysis`/`review` 双写缓存与飞书、`review` 会把 `full_analysis` 自评 good 降级。
- **服务端改动（coze：需重新上传部署包才生效）**：
  1. `src/graphs/graph.py`：删除 `validity_check` 门与 `route_after_validity_check` 路由；图简化为 4 节点直线图
     `cache_check → generate_organized_problems → full_analysis → tool_router → END`（`full_analysis` 为唯一产出节点，`tool_router` 零 LLM 规则判定 need_tool）。
  2. `src/graphs/nodes/review_node.py` / `validity_check_node.py` 改名 `.disabled`（不再随包加载）；`review_guard` 相关代码一并清除。
  3. `full_analysis_node.py` 成为唯一缓存/飞书写入点（消除双写与 accuracy 降级）。
  4. `config/review_cfg.json` 成为孤儿配置（无 active 代码引用），不再随包发布。
  5. `src/graphs/nodes/_version.py::COZE_VERSION` 由历史漂移的 `1.18` 升到 `1.20`（与部署包 `ct-advisor_coze_v1.20_20260921.zip` 对齐；上一轮 v1.19 包未同步此常量）。
  6. `src/kb/__init__.py`：`detect_scope` 新增 `general_knowledge` 档（ICH/GCP 等简单定义类问题返回温和 💡 提示，不再弹「未命中知识库」式吓人声明）；三个知识缓存改为 (mtime,size) 失效，覆盖线上索引即自动热重载；`build_knowledge_index.py` 新增 `--merge` 可重复重建且保留既有键。
- **文档同步（本次随包）**：`AGENTS.md`（节点清单/流程图/分支函数/accuracy 说明）、`README_部署说明.md`（标题升 v1.20 + 当前架构段）、`UPGRADE_20260814.md`（v1.20 现状段）、`coze_modification_guide.md`（v1.20 架构变更横幅 + 旧 review 章节标注历史）、`NEED_TOOL_SCHEMA.md` / `coze_sync_guide_knowledge.md`（节点引用修正）均更新为 v1.20 现状。
- **部署包**：`adapters/coze/ct-advisor_coze_v1.20_20260921.zip`（105 文件，8.98 MB）。上传后须**重建/重启 Coze 镜像**（长驻进程，光传 zip 不生效）。

## [Unreleased] — 2026-09-17 · 飞书补写 `coze_version`（版本字段落点统一，ct-base §2.1）

- **依据**：ct-base `references/coze_io_contract.md` §2.1（2026-09-17 定）——版本类元数据
  （`skill_version` / `coze_version`）一律写在**出参侧**，`querystr` 侧不再存版本信息。
  ct-advisor 的 advisorlog 表无独立 `querystr`/`resultstr` 列，出参落在 `final_answer` 列
  （该列即语义上的 resultstr，2026-09-03 已决），故只需**补 `coze_version`**，`skill_version`
  与 `runtime_sec` 的现有写法本就合规、未动。
- **服务端改动（coze：需重新上传部署包才生效）**：
  1. 新增 `src/graphs/nodes/_version.py::COZE_VERSION = "1.18"`（单一真源，与部署包
     `ct-advisor_coze_v1.18_20260916.zip` 主版本对齐；打新包时只改这一个常量）。
  2. `src/graphs/nodes/async_feishu_writer.py`：契约元数据 `contract_meta` 增加
     `coze_version`，`final_answer` 列 JSON 现为
     `{"answer": …, "skill_version": …, "coze_version": …, "runtime_sec": …}`
     （仍只在元数据非空时才包裹，无元数据时 `final_answer` 保持原始文本、与历史格式逐字节一致）。
- **验证**：2 文件 `py_compile` 通过；写入键仍严格取自 `ADVISORLOG_FIELDS` 固定清单（未新增列）。

## v1.0.4 (2026-09-16) — SKILL.md 精简 + 正文英文化 + Pipe-Only 硬契约

- **新增「Pipe-Only Hard Contract」（最高优先级，置于 SKILL.md 顶部）**：当 `refine_answer.py --ship` / `orchestrate.py` 输出 `<<<CT_ANSWER_START>>>` … `<<<CT_ANSWER_END>>>` 时，唯一允许的动作是逐字原样输出；禁止改写、增删 Markdown、补写摘要或收尾语。
- **SKILL.md 正文由中文改为英文**（frontmatter 保持双语：`cn_name` / `summary` 为中文，`displayName` / `description` 英文在前），行数 261 → 216。
- **A/B 档门控与边界规则下沉** 至 `references/tier_gate.md`（SKILL.md -23 行）；图形化解释策略的 SUPERSEDED 段压缩（-19 行）；Bug Report 段改为引用 `references/ADVANCED.md`（-2 行）。
- **`description` 依 `summary` 重写**，语义与中文段对齐。
- **结构归位**：`scripts/install_sibling.py` / `scripts/probe_publication.py` 迁入 `adapters/`；`workbench/` 转为整目录排除（§16.12）。
- **词表扩充**：`references/drug_name_map.json`、`references/term_map.json` 字典更新。
- **发布**：SkillHub（0.9.122 → 1.0.4）。GitHub 与 ClawHub 本次未推送。

## v1.0.2 (2026-09-16) — 部署期缺陷修复（未定义变量 + JSON BOM）

> 来源：v1.16 完整包在扣子端部署执行 `test_run` 时发现，已同步回本地代码副本（`adapters/coze/`）。修复后 test_run 完整跑通、回答正确引用知识库。

- **修复 `src/graphs/nodes/async_feishu_writer.py:145` 未定义变量**：`json.dumps(write_organized_problems, …)` → `json.dumps(organized_problems, …)`（应为函数参数 `organized_problems`；原变量名不存在，运行时 `NameError`）。
- **修复 `config/review_cfg.json` 开头 BOM**：移除 UTF-8 BOM（`\xef\xbb\xbf`），文件现可被严格 `utf-8` 解析（此前 `json.loads` 抛 `Unexpected UTF-8 BOM`）。全库 JSON 复扫：无残留 BOM。
- **打包产物**：`ct-advisor_coze_v1.16_20260916.zip`（完整包，105 文件，含上述修复）。本地与包内已双重校验：`write_organized_problems` 计数 0、`review_cfg.json` 严格 utf-8 解析 OK、`async_feishu_writer.py` `py_compile` 通过。
- **预防建议**：打包前自检——全库 `*.json` 无 BOM + 全量 `.py` 通过 `py_compile`（本次两个缺陷均可在该自检中提前拦截）。

## v1.0.1 (2026-09-16) — 基于 AdvisorLog 真实问答数据的技能改进（P0 + P1 + P2 + 知识库整理）

> 基于 58 条真实 AdvisorLog 问答数据（2026-08-13 ~ 2026-09-15）的质量分析，落地改进。
>
> **🔴 知识库双轨架构约定（用户 2026-09-16 明确）**：ct-advisor 有**两个** knowledge 库——
> ① `knowledge/`（本地代码运行时库，**冻结、不再更新**）；② `adapters/coze/knowledge/`（**扣子端生产库，必须随时更新**，线上检索只走此库）。因此本批次所有知识改动（P0 新建文件、路由、索引）**均落到 Coze 副本**，本地源库仅作历史冻结参考。
>
> **📌 已固化进技能文档（2026-09-16）**：上述双轨架构已写入 `SKILL.md`「Knowledge Map & Read Discipline」规则 8（含致命错误模式 + 标准动作四步），并在 `adapters/coze/coze_sync_guide_knowledge.md` 顶部以 🔴 铁律重申——后续任何知识改动按此执行，避免 P0 上线即失效。

### P0：资料库补强

- **新建 `knowledge/ref-ops-compliance-practical.md`（9.4 KB）**：覆盖 CRA 日常高频场景——关中心全流程（关中心启动→ISF回收→尾款结算→纸质销毁→关中心小结）、HGR 自查判断、归档预约与伦理结题、给药周期计算、MedDRA PT 编码实操、研究背景撰写模板。对应 AdvisorLog 中 compliance:D good 率仅 29% 的 gap。
- **新建 `knowledge/ref-safety-practical.md（6.8 KB）**：覆盖安全信号检测实操、ICI irAE 管理速查、SUSAR 报告时限与流程、妊娠暴露处理、RMP 要点、死亡报告、过量用药处理、安全性数据库锁库。对应 AdvisorLog 中 safety good 率 0% 的 gap。
- **✅ 已同步至 Coze 生产库（关键）**：两个文件已复制到 `adapters/coze/knowledge/`，并在 `src/kb/__init__.py` 的 `_CATEGORY_KNOWLEDGE` 表 d/e/f 类追加；`knowledge_index.json` 经 `build_knowledge_index.py` 重建（compliance-practical 226 键 / safety-practical 132 键，关中心/HGR/归档/尾款/妊娠/过量等核心词已正确命中）。**线上检索现可命中 P0 新知识**——此前仅在本地源库新建、Coze 副本缺失，导致 P0 线上空转。

### P1：答案质量改进

- **答案长度后处理（Coze 端）**：新建 `adapters/coze/src/graphs/nodes/answer_postprocess.py`，提供 `apply_length_cap()` 函数，按 difficulty 硬天花板截断（simple ≤200 / middle ≤700 / complex ≤1000），截断到最近段落/句子边界并标注「⚠️ 已截断」。`full_analysis_node.py` 与 `review_node.py` 均已接入。对应 AdvisorLog 中 >1500 字符答案 good 率仅 39% 的问题。
- **⚠️ 已撤销（v1.0.1 部署前）**：硬截断上线前复核 AdvisorLog 数据，发现长度与准确率非单调（600-800 字 good 率最高 71%，200-400 字仅 50%），且 simple 平均已 598 字、complex 平均 2053 字，硬截断会误伤 good 答案。**已移除 `full_analysis_node.py` 与 `review_node.py` 中的 `apply_length_cap` 调用**，改为依赖 C3 提示词引导 LLM 自发控制长度。`answer_postprocess.py` 保留函数但暂不调用，备后续软提示方案复用。
- **空答案兜底（Coze 端，上轮已落盘）**：`async_feishu_writer.py` 检测 final_answer 为空时，用 organized_problems 构造最小本地兜底文本写入飞书。

### P2：category 规范化 + 多轮上下文

- **Category 规范化（Coze 端）**：`answer_postprocess.py` 提供 `normalize_problem_categories()`，统一 organized_problems 的 category 字段值（regulatory→compliance:d / statistics→methodology:c / 中文标签映射等）。`generate_organized_problems_node.py` 的 LLM 解析后和 simple/middle 本地合成后均调用。对应 AdvisorLog 中 category 命名异常（缺后缀/斜杠/中文标签）问题。
- **多轮上下文保持（Coze 端）**：`full_analysis_node.py` 与 `review_node.py` 的长会话（>5 轮）仅保留最近 5 轮，避免上下文溢出稀释；注入时额外强调「基于承接、不重复已知信息、聚焦当前问题增量」。对应 AdvisorLog 中多轮追问质量递减问题。

### 知识库整理

- **路由完整性**：`reference-index.md` 补 `methodology_core.md` / `prompts.md` / `ref-gcp-13-principles.md` 三文件路由；去 `ref-ops-compliance-practical.md` 重复条目。
- **废弃清理**：删除 `survey_external_projects.md`（DEPRECATED，内容已不用于回答）；修 `prompts.md` 中对它的悬空引用。
- **最终状态**：21 文件 / 401.5 KB，路由覆盖率 100%，悬空引用 0。

## v1.0.0 (2026-09-15) — 首个正式发布：§16 发布前规范整改（发布包排除项 + 共享件同步 + 出站归位）

> **版本跃迁说明**：本批次内容原标 `v0.9.122`，发布前经决定**直接升至 `v1.0.0`**——ct-advisor 的
> **首个对外正式发布版本**（major 跃迁），承接历史序列 `v0.9.111–v0.9.122`。功能能力与 `v0.9.122`
> 完全一致，差异仅在版本号本身；`SKILL.md` / 两份 `README` / `AGENTS.md` / 出站信封
> `skill_version`（读 `SKILL.md` 单一真源）已同步为 `1.0.0`。
>
> 依 ct-base §16 发布前检查清单逐条整改，**无功能逻辑改动**，全部为打包 / 一致性 / 规范项。

- **§16.12 工作台整目录排除**：两份 ignore 由 `workbench/*.html` 改为 `workbench/` 整目录。
  原逐文件列举方式漏掉 4 个文件（`llm_loader.py` LLM 加载器、`tokens.css`、`wb-list.css`、`wb-list.js`
  以及 `workbench.config.json`），已随之 `git rm -r --cached` 移出索引（磁盘文件保留）。
- **§16.8 测试内容排除**：新增 `scripts/test_*.py` 通配规则（替代逐文件列举），
  `scripts/test_sibling_contract.py` 移出索引；仅 `test_modeB.py` / `test_tool_router.py` 被列名的
  旧写法导致该文件长期随包发布，本轮修复。
- **§16.8 审计痕迹文档排除**：新增 `docs/*audit_trace*.md` 排除项，对应留痕文档移出索引；
  文档内容同步改写为**描述性指代**（不复述审计签名原文，避免扫描器再次命中形成告警自我维持）。
- **§16.8 共享件一致性（原本 5 项漂移，exit 1）**：四项从 ct-base 真源同步并逐项 MD5 校验一致——
  `references/term_map.json`（底座多 5 词）、`references/drug_name_map.json`（底座多 15 药名，`_meta` 值对齐）、
  `scripts/kw_localize.py`、`scripts/r_libs.py`。整改方向严格遵循 §16.8 单一真源（底座 → 叶子，未反向改叶子）。
- **§3 frontmatter 对齐（F08 ERROR）**：`description` 中文段在 A/B 档门控句补「在答案末尾」5 字，
  与 `summary` 逐字一致；扫描器 F08 清零。
- **§16.0 安全审计 · 措辞项**：内嵌凭据相关披露共 **7 处**改写为等价措辞，消除签名命中
  （`README.md` / `SKILL.md` / `references/ADVANCED.md` ×2 / `references/ops.md` / `CHANGELOG.md` /
  `workbench/index.html`）；审计留痕文档改写为**描述性指代**版并移出发布包。
  判定结果：`STILL_PRESENT` **5 → 4**，其中「内嵌凭据措辞」项转为 `RESOLVED`。
- **§16.0 安全审计 · 代码加固**：针对审计「子进程可执行体路径未做白名单校验 / 映射表无信任边界」
  的指控，在 `scripts/handle_need_tool.py` 的 `subprocess` 调用前新增
  `_execution_boundary_violation()` **双闸门**——① 解释器 basename 须命中白名单
  （python / py / Rscript 系）；② 所有 `.py` 脚本参数解析后须落在技能根目录内。
  实测：6 个构造用例（越界绝对路径 / 相对逃逸 `../../` / 非白名单解释器 / 空命令）全部正确拦截，
  真实映射表 4 个条目全部放行。原审计签名（代码行）仍会命中，属**变量名误命中**，非缺陷。
- **§16.0 安全审计 · 披露加固**：针对审计「附件处理未在主概览显著警告内容可能被远程传输」，
  在 `README.md` / `README_zh-CN.md` 的「范围现实核对」段后新增**附件传输显著警告**
  （附件抽取文本与手打提问走同一云端路径、敏感内容须先移除）。

### 第二轮（2026-09-15 下午）— 出站调用归位 + 排除项补全 + 死存根清理

> 三项由彤拍板执行（前一轮报告列为「待拍板」）。**仍无功能逻辑改动**。

- **① §16.10 / §16.11 出站调用归位（`spec_lint` F17 告警消除）**：两个**真出站**脚本
  由 `scripts/` 迁入出站调用专用目录 `adapters/`——`install_sibling.py`（打 SkillHub
  search / download API）、`probe_publication.py`（打 SkillHub + GitHub API）。迁移后
  `scripts/` **出站归零**，`spec_lint` 的 WARN 由 3 降为 2（F17 不再出现）。
  > 规范注记：§16.10 第 2 条本允许「既有出站代码无需迁移、维持现状」，本轮属**主动收口**
  > （超出规范最低要求），目的是让 `scripts/` 目录语义保持纯净（`adapters/` = 出站，
  > `scripts/` = 纯本地计算）。
  - 同步修正 **9 个文件**中的路径引用：`SKILL.md`（5 处）、`knowledge/system_prompt.md`（5 处）、
    `scripts/check_deps.py`（2 处）、`scripts/handle_need_tool.py`（3 处，含路径探测的两个候选：
    用户态规范路径与 `__file__` 解析路径）、`scripts/test_sibling_contract.py`（1 处）、
    `README.md`、`README_zh-CN.md`、`references/ADVANCED.md`、`scripts/tool_mapping.json`（`tiers.note`）。
  - 验证：5 个相关 `.py` 全部 `py_compile` 通过；`_helper_path()` 正确定位到新位置；
    `_install_command()` 生成的命令已含 `adapters/` 前缀；离线契约分支（`test_sibling_contract`
    的 `run_install_helper`）**6 项全 PASS**。
  - `CHANGELOG` 历史条目**有意不改**：它们记录的是当时的事实（脚本当时确在 `scripts/`），§16.6 亦明文豁免历史 CHANGELOG。
- **② `references/coze_cache_policy.md` 列入发布排除（§16.7 ②）**：该文档通篇描述 Coze 端
  缓存治理与响应信封的内部实现（节点文件、配置项与模型名、内部表字段），语义属「Coze 对接
  操作参考 / 接口契约」类，故列入两份 ignore + `git rm --cached` 移出索引（磁盘保留作开发参考）。
  同时 `SKILL.md` 规则 7 末尾对它的路径引用改为**描述性表述**（该规则正文已自足，不留死链）。
  > **判定说明**：未采用「改写为英文」的方案——该文档的内容本身就是不可公开的实现细节，
  > 翻译成英文仍然泄露内部契约；规范正解是**排除发布**而非翻译（§16.7）。
- **③ 三个零内容占位文件删除**：`knowledge/ref-ops-contract.md`、`knowledge/ref-reg-contract.md`、
  `knowledge/ref-reg-retrieval.md`——各仅 2–3 行 `DEPRECATED` 声明、零实质内容（内容早已分别
  并入 `reference-index.md` 与 `ref-interaction-style.md`），且 Coze 端同步指南已将其列入
  「**已删除的旧文件（不要再上传）**」清单，本地残留反成不一致。
  - 副作用（正向）：删除后 `knowledge/` 的 topic file 计数**恢复为 15**，与 `SKILL.md`
    的「15 topic files」口径一致（删除前实为 17，口径本身已失真）。
  - `knowledge/reference-index.md` 的维护说明同步改写为**不复述已删文件名**的表述。

## v0.9.111–v0.9.121 (2026-09-10) — 兄弟技能调用新增 A/B 档门控（检查安装 / 提示安装 / B 档不对外发布）

> **同日第二轮修正（彤 2026-09-10 补充要求）** —— 见文末「追加修正」小节：
> ① `ct-pipeline` **尚未发布**（SkillHub 未上架、GitHub 仅空占位仓库）→ 新增第 4 个状态 `unpublished_a`；
> ② 发布状态判据**改为以 SkillHub 上架为准**（GitHub 空仓同样 200，会误判）→ 新增 `scripts/probe_publication.py`；
> ③ `ct-samplesize` 已补装 → 契约测试由 SKIP 转为实跑并全绿。
>
> **同日第三轮修正（回归最初目标复查时发现）** —— 见文末「第三轮：安装通道实测修复」小节。
>
> **同日第四轮修正（彤 2026-09-10 追加要求：安装改为「建议」）** —— 见文末「第四轮：安装姿态改为
> 『建议安装』」小节。要点：**安装需下载技能包并写入本地技能目录，可能触发本机安全警告** →
> 默认姿态由「征询同意后代办安装」改为「**只建议安装**」（把命令原样交给用户，用户可自行执行）；
> 仅当用户**明确授权**（`install_consent="approved"` → `install_mode="authorized"`）才可由 agent 代办。
> 门控状态集合不变（仍 4 个），`install_required` 仅新增 `install_mode` 授权门。
>
> **同日第五轮修正（彤 2026-09-10：README 示例按实测校对）** —— 见文末「第五轮：README 示例逐条实测校对」小节。
> 实跑 8 个示例后发现 README 的**机制描述**与真实返回不一致（日期标签、并行三源、vague 直连 Coze、
> 一次执行卡只跑一个技能、样本量为 JSON 而非叙事改写、Coze 60s 超时回退等），已按实测逐条改写
> `README.md` / `README_zh-CN.md`，并连带修正 `references/ADVANCED.md` 与 `knowledge/system_prompt.md`
> 中的同类旧说法（GitHub clone 安装、`requests` 自动安装、日期标签）。
> 复查「同意 → 安装 → 调用」这一环时，实测发现**给出的安装命令根本执行不了**（三重坑），
> 该环实为断链；已新增自带安装器 `scripts/install_sibling.py` 并跑通**端到端闭环**
> （未装 → install_required → 执行命令装成 v0.10.0 → 重跑同卡 `status=ok`，真实取到 50 项试验）。
> 判据仍是「4 个状态」，第三轮只修安装通道本身，**未改动门控语义**。
>
> **同日第六轮修正（彤 2026-09-10：串行回退消息超时值纠偏）** —— 见文末「第六轮」小节：
> 串行路径的 `FALLBACK_TO_LOCAL_DRAFT` 消息此前把超时**硬编码为 60s**，长任务（300s）超时会误报；
> 已改为由 `refiner.resolve_timeout()` 解析出的**真实有效超时**。
>
> **同日第七轮修正（彤 2026-09-10：默认超时 60s → 90s）** —— 见文末「第七轮」小节：
> `refiner.timeout` 由 **60 提到 90**（`long_timeout=300`、`race_window=30` 不变）；运行时默认值、
> 条件化超时判定与注释、回退消息兜底、全部文档同步更新。版本 v0.9.111 → **v0.9.112**。
>
> **同日第八轮修正（彤 2026-09-10：README 案例改为「用户可见」表述）** —— 见文末「第八轮」小节：
> 案例里的「助手实际返回」原为内部协议 dump（need_tool / JSON / 检索日志 / 产物路径），过于 IT 化；
> 已按「用户所见即所得」改写为**自然语言回答 + 一行内部机制注**，多轮案例补「首轮追问 + 补参后最终答案」。
>
> **同日第九轮修正（彤 2026-09-10：示例 1 换题 + 兄弟技能调用后提示「直接用该技能」）** —— 见文末「第九轮」小节：
> ① 示例 1 原为泛泛的「E9(R1) 五要素」问答，改为**具体场景**（III 期肿瘤 OS、进展后交叉用药 → 估计目标怎么设）并实跑取回答案；
> ② 调用兄弟技能时缝合层**由代码追加一行 💡**：所给为可读摘要，如需核实或获取更详细的原始输出，建议直接运行该技能；
> ③ 英文 README 开头与中文版**同步**（去掉与实测不符的「并行预取」表述），并修复中文版被存成 LF 的换行与 5 处 `\r>` 残字、3 处 HTML 实体。
>
> **同日第十轮修正（彤 2026-09-10：示例 1 暴露的「答案长度失控」根因修复）** —— 见文末「第十轮」小节：
> 示例 1 的答案「讲得很细却没回答问题」，追查发现根因在**云端出答案提示词**——`full_analysis` 与 `review`
> 两个节点都写着「不设字数上限」，并把 difficulty 降级为「仅作详略软信号 / 质量优先于标签」，于是任何
> 单点方法学问题都返回多节长报告。实测：问「怎么把总 I 类错误率控制在 0.05」得到 **5 节 / 4522 B**，
> 含 DSMB 角色与决策流程、信息时间选取等**完全没被问到**的内容；问「主要估计目标该怎么设」两轮在
> 治疗政策 / 假设策略之间摇摆、**始终不给推荐**，另一轮长到被 `max_completion_tokens` **截断在「### 四」**。
> v1.5 本有档位字数上限（simple ≤150 / middle ≤400 / complex ≤600 字），但只写在**无任何代码引用**的
> `coze_system_prompt_v1.4.md`，故长期失效。已把**作答契约**（C1 先答后展 / C2 边界锁定 / C3 难度即字数
> 硬上限 / C4 单一推荐）写入 4 个**真正生效**的 `config/*.json`（full_analysis / review /
> generate_organized_problems / judge_difficulty），同步知识库镜像与本地 brain，清除「不设字数上限」表述；
> 示例 1 换成**单点有唯一正解**的题（期中分析 α 控制）。版本 v0.9.114 → **v0.9.115**；Coze 部署包 **v1.11**
> （需上传 + 重建镜像才生效）。

> **同日第十一轮修正（彤 2026-09-10：C3 由「字硬上限」校准为「预期量级 + 硬天花板」）** —— 见文末「第十一轮」小节：
> 第十轮的 C3 只有上限没有下限，且明文压过「完整覆盖」，于是模型靠**删要素**达标 → 答案有时过精简；
> 同时存在单位不一致（`config/*.json` 写 `字`，知识库与 `steps.md` 写 `words`，差约 1.6 倍，而
> `methodology-core.md` 确实被云端读取）。已改为 **simple ~100/≤200 · middle 300–500/≤700 · complex 500–800/≤1000（中文字符）**，
> 明确「**要素完整优先于字数**」，并规定删减顺序：跑题 → 重复 → 压缩。版本 v0.9.115 → **v0.9.116**；部署包重出为 **v1.12**。

> **同日第十三轮修正（彤 2026-09-10：README 示例改版 —— 实操题上位）** —— 见文末「第十三轮」小节：
> 用户提议用**角色实操题**替换前面偏空泛的案例，故：示例 1 改为「受试者因 SAE 提前退出的交通补贴怎么给（GCP）」、
> 新增示例 2「IB 列为『少见』但实测 15%，PV 要不要更新 IB 与标签」；原「控 α」例移出示例区，原示例 2–8 顺延为 **3–9**（共 9 例）。
> 改版过程中实测发现示例 2 被**误判为注册库检索**并弹补参追问：根因是本地 registry 触发词含裸词「在研」，
> 命中了「在研|究者手册」。同时发现上一轮云端 `_kb_hit` **只接上了 GUIDELINE 两处**、`TOOL_RULES` 主循环仍是裸子串
> `kw in q`（即 `ror` ⊂ `error` 的修复并未真正生效），且边界写法 `(?!s?[a-z])` 会因正则回溯**误伤所有复数召回**。
> 三处均已修，并新增云端词表回归测试 `scripts/test_tool_router.py`（**39/39**）。版本 v0.9.116 → **v0.9.117**。

> **同日第十四轮修正（彤 2026-09-10：云端补英文咨询意图护栏 + 回答姿态改为「先自身作答、末尾建议」+ 收紧调用门槛）** —— 见文末「第十四轮」小节：
> ① 云端 `tool_router_node` 补齐**中英咨询意图护栏**（镜像本地 `route_tool` 的 DEF / METHOD / DOC，外加「明确取数动作」例外），
> 根治「英文方法学问句（…how do I keep the overall type I error rate at 0.05?）被裸词 trial 判成检索注册试验」；
> ② 按用户口径**收紧调用门槛**：只有**强触发词**（具名数据源 / 具名统计量 /「检索动词＋明确对象」句式）才**自动调用**兄弟技能；
> 泛词（信号 / 文献 / 试验 / 安全性 / 设计）降级为**弱命中 → 不调用**；
> ③ 回答逻辑改为「**先基于自身能力作答，最后再建议是否安装 / 调用兄弟技能**」：新增 `route_tool.suggest_footer` 软建议页脚，
> 接进 `orchestrate.build_output` 与 `refine_answer --ship`；`install_required` 由「阻断式委托」改为「答案在前、安装建议在后」。
>
> **同日第十五轮修正（彤 2026-09-10：接手复核发现的两处不一致 →「① 按代码文件改；② 修改」）** —— 见文末「第十五轮」小节：
> ① 交接口径更正（仅文档）—— 交接文件原把「查 XX 药的文献」当弱命中抽验句，**与代码 / 测试矛盾**（该句按强触发规则
> ③ 本就是 `ct-literature` 强命中），**以代码为准**更正；
> ② 修复「**软建议溢出**」—— 护栏命中时此前仍回落弱词表，裸弱词 `trials?` 会给纯定义 / 方法论题附一条题不对路的
> `ct-registry` 建议（已消灭的误报换位置继续出现）；现改为**只保留强命中的建议**，本地 `route_tool` 与云端
> `tool_router_node._suggest_tools(strong_only=…)` 同步修。
>
> **同日第十六轮（彤 2026-09-10：按 v1.15 线上实测重写 README 案例回答）** —— 见文末「第十六轮」小节：
> 两份 README 各新增**示例 10 / Example 10**，首次把「**soft suggestion**」这一用户可见尾巴写进对外案例 ——
> ① 纯方法学题（英文问句）**末尾零建议**；② 泛词题（查 XX 药的安全性信号有哪些）**自身作答在前、末尾一行建议**。
> 案例全部取自当次端到端**实测输出**原文，并如实标注「云端对英文问句返回中文正文」。
>
> **同日第十七轮（彤 2026-09-10：删除示例 7，编号顺延）** —— 见文末「第十七轮」小节：
> 删除原**示例 7「切换输出语言」**，其后 3 例顺延（原 8/9/10 → **7/8/9**），现共 **9 例**；
> 引导句的示例计数与多轮编号引用同步更新，删除后编号连续无断号。
> 语言切换能力本身未删（FAQ「中文系统下输出是中文吗」仍完整说明）。
>
> **同日第十八轮（彤 2026-09-10：删除示例 9，末例移除）** —— 见文末「第十八轮」小节：
> 删除现**示例 9「只沾边兄弟技能的方法学题」**（第十六轮按实测新增那条），现共 **8 例**，编号 1–8 天然连续；
> 引导句的计数与多轮编号引用同步更新，「两种尾巴对照」的引导语整句移除。
> 软建议机制说明未受影响（§2「调用门槛」与 §4「安全预览」两处仍在）。

### 背景（彤 2026-09-10 要求）
- **A 类技能**：先检查是否安装；未安装则提示用户安装。用户**拒绝** → 给出自身能力范围内的分析结果；用户**同意** → 安装后调用该技能完成分析。
- **B 类技能**：直接提示需要调用 B 类技能、但该技能不对外发布，然后用自身能力范围内的功能完成分析。

### 审计结论（改造前）
5 条要求 4 条未实现、1 条仅文字规范未落代码；另有 4 个连带缺陷。实测（Anaconda base）：
- Coze 下发 B 档 `ct-protocol` → `handle_need_tool.py` 落到「未在 tool_mapping.json 中找到技能映射」**硬错**；
- A 档技能缺失（`CT_SKILLS_DIR` 指向空目录）→ `技能执行失败 rc=2: No such file or directory` **硬错**，无安装提示、无征询。

### 改造
- **`scripts/tool_mapping.json`**：新增顶层 `tiers` —— ct 系列 A/B 档登记（23 条：A 档 9 / B 档 12 / 元层 2），每条含 `tier` / `published` / `github` / `purpose`；`default_tier: "B"`（未登记技能保守按 B 档处理）。**权威口径** = ct-base §11（唯一分类轴 `input_sensitivity`）+ §13.1（保密声明）；`published` 判据见下方「追加修正」——**已改为以 SkillHub 上架为准**。本表是档位与安装地址的**单一事实来源**。
- **`scripts/handle_need_tool.py`**：`execute_card` 在 subprocess 之前插入**档位门控**，新增 3 个状态 ——
  - `unreleased_b`：B 档（或未登记）技能 → 说明「该技能不对外发布、无法安装」+ 用自身能力作答；**不再走「未映射」硬错**；
  - `install_required`：A 档未安装 → 结构化上报 `github` / `install_hint` / `purpose` / `missing`（缺失参数一并算好，供同轮追问）；
  - `local_fallback`：卡片带 `install_consent="declined"` → 自身能力作答 + 标注「未取数」。
  新增 `_resolve_tier()` / `_skill_installed()` 两个纯本地探测函数（不执行、不联网）。**🔴 本模块只做「检测 + 上报」，绝不执行安装** —— ct-base §5「禁止静默安装」红线：安装须由 agent 在用户明确同意后执行，非交互模式不得阻塞。
- **`scripts/refine_answer.py`**：新增 `INSTALL_MARKER = "<<<CT_INSTALL_REQUIRED>>>"`；`_merge_answer` 补 3 个状态分支（中英双语），拒装路径组装为「Coze 草稿 + 数据未取数说明」，B 档路径组装为「Coze 草稿 + 需调 B 档技能但不对外发布」。
- **`scripts/orchestrate.py`**：`build_output` 识别 3 个新状态 —— `install_required` 走**委托**路径（需人工决策，非 error，`extra.install_request` 透出 github/install_hint）；`unreleased_b` / `local_fallback` 由**代码直接缝合包裹**（无技能可执行，免一次委托往返）；无预判且 Coze 要 B 档技能时**短路**为直接包裹。`_render_delegate` 新增 `extra` 参数。
- **`scripts/check_deps.py`**：`KNOWN_DEPS` 硬编码表**删除**，改为从 `tool_mapping.json` → `tiers` 读取。**修正既有档位标注错误** —— 旧表把 `ct-registry` / `ct-safety` / `ct-literature` 标成 `tier B`、`ct-samplesize` 标成 `tier A`，与 ct-base §11 及 `SKILL.md` `dependencies`（四个全 A）三处矛盾，等于把三个确认已发布的公开技能标为「不发布」。输出改为分组呈现：A 档（可安装，逐个探测）+ B 档/meta（列出但明示「无可安装项」）。
- **`SKILL.md`**：新增 **"🔴 A/B Tier Gate"** 小节（三分支表 + 「安装是用户决定，不是 agent 决定」红线）；Step 3b 行、Requirements「Sibling skills」行、「Skill-card execution protocol」的「Only two cases need you」→「Only three cases」（补 `install_required`）、「Boundaries with Sibling Skills」（补档位划分段）。
- **`knowledge/system_prompt.md`**：`Missing a sibling skill` 段改写为**分档降级**（A 档：给 GitHub 地址 + 征询安装；B 档：说明不对外发布 + 自身能力作答 + 标注「深度分析未实际执行」），并说明 runner 的三个新状态。
- **`scripts/test_sibling_contract.py`**：新增 `run_tier_gate()` 9 条断言（B 档 → `unreleased_b`；未登记 → 保守 B；A 档未装 → `install_required`；拒绝 → `local_fallback`；已装不误报；referral 不被吞；注册表自洽 ×2；check_deps 档位正确）。
  **连带修复**：契约测试路径白名单在**软链接安装**下恒误报「脚本路径越界」（`resolve()` 后落到真实路径、与 `SKILLS_DIR` 不同根，本机实测契约 0/4）→ 改为两级判定（解析后在内 **或** 未解析路径在 SKILLS_DIR 下且不含 `..`，保留防逃逸语义）；未安装技能由 FAIL 改 **SKIP**（A/B 档门控下「未安装」是合法状态，非契约漂移）。

### 规范连带修正（ct-base）
- `ct-base/docs/05-version-build.md` §11 的 `publish` 口径与 §13.1 冲突（§11 称 B 档包「可发布」并把 `ct-protocol` 标为「已发布」；§13.1 称 B 档「均不对外公开发布」）→ 按 GitHub 实测（B 档 404）**以 §13.1 为准**修正 §11，详见 ct-base CHANGELOG 2026-09-10 条。

### 验证
- `scripts/test_sibling_contract.py` → 契约 **3/3 = 100%**（ct-samplesize 未安装，SKIP）+ **A/B 档门控 9/9 = 100%**，`exit=0`。
- `scripts/orchestrate.py --self-test` → **8/8 = 100%**（原有八条决策路径无回归）；新增四路径实测（B 档短路包裹 / `install_required` 委托 / `local_fallback` 包裹 / `unreleased_b` 包裹）输出正确。
- `scripts/route_tool.py --self-test` → 工具命中 **22/22** + 参数抽取 **6/6**。
- `scripts/test_modeB.py` → **10/10**。
- `scripts/test_seven_flows.py` → 环境性失败（依赖本地 Coze 节点 `adapters/coze/project_20260812_152011/...`，该目录按 §16.7 不随发布副本），与本次改动无关。
- 实测三场景：B 档 `ct-protocol` → `unreleased_b`；A 档未装 → `install_required`（含 github/install_hint）；A 档未装 + `install_consent=declined` → `local_fallback`。

### 追加修正（同日第二轮，彤 2026-09-10）
**触发的两点新信息**：①「`ct-samplesize` 装了，补一下」；②「`ct-pipeline` 尚未发布」；并指定**发布状态以 SkillHub 上架为准，GitHub 可能有空库**。

1. **发布判据改为 SkillHub（权威源）** —— 此前 `tiers.published` 按 `github.com/medstatstar/<slug>` 的 HTTP 200/404 核定，**该判据是错的**：GitHub 上「已创建但从未推送内容」的空占位仓库同样返回 200。实测 `ct-pipeline`：仓库存在但 `size=0`、contents 返回 `This repository is empty`、`created_at == pushed_at = 2026-08-07`，在 SkillHub 上**搜索无结果**（`api.skillhub.cn/api/v1/search`）。即第二轮审计前，`published=true` 会让 `install_required` 给用户一个**装了也是空目录**的假安装地址（「假可安装」）。
2. **新增 `scripts/probe_publication.py`**（发布状态复核工具）——
   - **判据**：SkillHub 搜索 API 按 `publicSlug` **精确命中**（`slug` 或 `namespace.publicSlug` 全等，避免 `ct-safety` 命中 `ct-safety-review` 之类包含式误判）→ 已发布；
   - **GitHub 仅作诊断**（说明「为什么没上架」：空占位仓库 / 404 / 非空但未上架 → 提示人工确认）；**多端点故障转移**（`--search-url` > env > 公网 `api.skillhub.cn` > CLI `metadata.json`；本机 `metadata.json` 指向内网 LB，直连会证书不匹配，故公网端点优先）；命中端点后缓存复用，避免 21 项 × N 端点重复重试；
   - 端点全不可达时**不判定**（`verified=None`）并**显式报「未能判定」**，退出码 1 —— 绝不把「查不到」写成「一致」（首版曾误报 ✓，已修）；
   - `--fix` 回写 `published`（**字节级读写**，避免 `read_text/write_text` 的通用换行转换把全文件 CRLF→LF 造成无关 diff；回写前先 `json.loads` 自校验）；`--json` 机器可读；`--only` / `--handle` / `--no-github`。
   - **实测结论（2026-09-10，零漂移）**：已上架 = `ct-registry` v0.10.0 / `ct-safety` v0.9.10 / `ct-literature` v1.0.2 / `ct-samplesize` v5.7.26 / `meta-analysis` v2.9.19 / `statsoft-cli` v2.8.2 / `statdata-transfer` v2.2.1（+ `ct-advisor` v0.9.110）；未上架 = 全部 B 档 12 个 + 元层（`ct-base` / `ct-update`）+ **A 档的 `ct-pipeline` / `ct-synthdata`**。即 **A 档 ⊅ 已发布**：档位（输入涉密性）与发布状态是**两个正交维度**。
3. **新增第 4 个门控状态 `unpublished_a`（A 档但尚未发布）** ——
   - `handle_need_tool.py`：门控 ②「`not published` → `unpublished_a`」，只说明「尚未公开发布（未在 SkillHub 上架）、当前无法安装」，**不给安装地址**、**不征询同意**（没有可同意的事），随后本地作答 + 标注未取数。
   - 🔴 **顺序修正（本轮踩到并修掉）**：该门**必须排在 `if not tool_cfg` 之前**。`ct-pipeline` 只登记在 `tiers` 里、**不在 `skills` 自动执行表**，若排在之后会落进「未在 tool_mapping.json 中找到技能映射: ct-pipeline」**硬错**——正是本次改造要消灭的行为。首版把该门写在 `if not _skill_installed(tool_cfg)` 内部，实测即落硬错，已上移到门控 ①（B 档）之后。
   - `refine_answer.py`：新增 `unpublished_a` 渲染分支；⚠️ **只渲染面向用户的字段**（`message` / `purpose` / `next_step`），`result.hint` 是给 agent 的处置指引，**不得混进用户可见正文**（首版把内部提示渲染进了正文，已修）。新增 `next_step` 字段（面向用户的可执行建议：先分别调用已上架的 `ct-registry` / `ct-safety` / `ct-literature`，由本技能就地缝合）。
   - `orchestrate.py`：新增 `_unpublished_payload()`；预判路径把 `unpublished_a` 并入「代码直接缝合包裹」组；**无预判**路径下 Coze 索要「B 档 **或** 未发布的 A 档」时一律**短路包裹**（不可安装，委托只是多一次无谓往返）。
   - **双语补齐（顺带修既有 i18n 缺陷）**：`payload.message` 由代码生成、恒为中文，英文答案会出现「英文骨架夹中文正文」。`unreleased_b` 与 `unpublished_a` 两分支改为**英文路径自带英文文案**，中文路径用 payload 文案。
4. **`ct-samplesize` 补装后续** —— 本机 `~/.workbuddy/skills/ct-samplesize` 已就位（symlink 至 skills 仓）。契约测试由 **SKIP → 实跑**：`--help rc=0`，**11 个契约 flag 全部命中**，契约 **4/4 = 100%**。其 `engine=coze`（远程 R 服务）不影响 `--help` 契约校验。
5. **`install_hint` 改为 SkillHub 优先** —— `install_required` 与 `check_deps.py` 的安装提示改为 `skillhub install <slug>`（SkillHub 已上架为权威口径），GitHub `git clone` 降为备用路径；`install_required` 的 `result` 新增 `skillhub` 字段。
6. **`tool_mapping.json` `tiers.note` / `authority` 重写**：明确「tier 由 §11 `input_sensitivity` 决定，`published` 与之正交，判据 = SkillHub 上架」；`ct-pipeline` 条目补 `note` 记录实测证据（空占位仓库 + 未上架）与「走 `unpublished_a`、不给安装地址」。
7. **`check_deps.py`**：文件头档位语义改写为「A 档 = 非涉密，**已发布才可安装**」；A 档未发布项提示语由「库内夹具」改为「尚未对外发布——不属于可安装项（给出安装地址只会得到空仓库）」，并注明命中时走 `unpublished_a`。
8. **测试** —— `run_tier_gate()` 由 9 条扩到 **13 条**：新增 `ct-pipeline` → `unpublished_a`（**断言不得为硬错、不得含 `install_hint`**）、`ct-synthdata` → `unpublished_a`、注册表自洽（已发布 A 档必须带 `github`；存在未发布 A 档且确为 `false`）。
9. **规则文档同步**：`SKILL.md`（A/B Tier Gate 表新增「A · NOT published」行；Step 3b / Requirements「Sibling skills」/「Only three cases」/「Boundaries」段补 `unpublished_a` 与 SkillHub 判据；`summary` / `description` 同步）；`knowledge/system_prompt.md`（降级段改为三分支：A 档已发布/A 档未发布/B 档，并声明「A 档 ⊅ 已发布」+ 两个工具脚本）；`README.md` / `README_zh-CN.md`（安装 FAQ 补「A 档未上架的怎么办」）。
10. **ct-base 连带修正**：`docs/05-version-build.md` §11 —— 「实测佐证」由 GitHub 200/404 口径**改为 SkillHub 上架口径**（含逐条版本号），并显式声明「**A 档 ⊅ 已发布**」；`ct-pipeline` 条目补「**尚未发布**、当前不可安装」；A 档 `publish: public` 条目补「仅表示允许并可发布，不代表已发布」。

#### 追加验证（全绿）
| 测试 | 结果 |
|---|---|
| `test_sibling_contract.py` | 契约 **4/4**（`ct-samplesize` 实跑，11 flag 全中）+ A/B 档门控 **13/13**，`exit=0` |
| 七分支真实 subprocess 实测 | ① A 档已发布未装 → `install_required`（hint = `skillhub install ct-registry`）② + `declined` → `local_fallback` ③ `ct-pipeline` → `unpublished_a`（无 install_hint）④ `ct-synthdata` → `unpublished_a` ⑤ B 档 → `unreleased_b` ⑥ 未登记 → `unreleased_b`（`registered=false`）⑦ `meta-analysis` → `referral` —— **7/7 正确** |
| `orchestrate.build_output` | 无预判 + Coze 要 `ct-pipeline` → **不委托**、含「尚未公开发布」；预判 `unpublished_a` → 包裹；回归：预判 `install_required` 仍委托且带 `install_request` —— **全部正确** |
| `refine_answer._merge_answer` | `unreleased_b`（注册/未注册）× `unpublished_a` × 中英双语 —— 渲染正确、无内部提示泄漏、无中英混杂 |
| `probe_publication.py` | 21 项全部判定、**零漂移**、`exit=0`；**注入漂移实测**：改 `ct-pipeline` → `published=true` → 检出 1 处漂移 + `exit=1`；`--fix` 自动回写为 `false`，**与原始文件 byte-identical**（换行风格保持），JSON 校验通过 |

#### 遗留
- `ct-pipeline` / `ct-synthdata` 完成 SkillHub 上架后，重跑 `probe_publication.py --fix` 即自动转回 `install_required` 路径，无需改代码。
- `test_seven_flows.py` 仍为环境性失败（缺 `adapters/coze/project_20260812_152011/`，按 §16.7 不随发布副本），与本次改动无关。

---

### 第三轮：安装通道实测修复（2026-09-10，回归最初目标复查时发现）

**动因**：复查「A 类：先检查是否安装 → 提示安装 → 同意则安装后调用」这一环。
门控四状态本身正确，但**「同意」之后那一步是断的** —— 交给用户的安装命令执行不了。

#### 实测抓到的三重坑（全部有据）
1. **裸命令不存在**：`skillhub install <slug>` 里的 `skillhub` **不在 PATH**
   （`which skillhub` 失败；`~/.local/bin/skillhub` 本机不存在；skill-publish 另记载该
   bash 启动器有 Windows 路径 bug）。此前 `install_hint` 与两份 README、`SKILL.md`、
   `system_prompt.md`、`check_deps.py` 都在教用户敲它。
2. **本机轻量版 CLI 装不了**：`~/.skillhub/skills_store_cli.py` 是 **v2026.3.6（44KB）精简版**，
   索引/下载端点指向**内网 LB**（`http://lb-*.clb.gz-tencentclb.com`），实测下载得到非 zip →
   `Downloaded file is not a valid zip archive`。而 filesrv 上的完整版是 **v2026.8.5（226KB）**。
3. **UNC 路径经 shell 会烂**：完整版 CLI 在网络盘，路径是 UNC。把 UNC 写进命令串经
   bash/Git-Bash 传递会被**二次拼接**（`\\filesrv\c$\filesrv\c$\...`）→
   `can't open file`。首次修复用 `os.path.abspath(__file__)` **无效** —— Windows 上
   `os.getcwd()` 返回的已是解析后真实路径，拼出来仍是 UNC。

#### 修复
1. **新增 `scripts/install_sibling.py`**（纯标准库）—— 把安装收敛成**一条由同解释器执行的命令**：
   ① 先查 SkillHub search API **精确核验上架**（未上架即拒装，退出码 3，防止把未发布/B 档技能装进来）；
   ② 下载 zip 并校验根含 `SKILL.md`；
   ③ 解压到 `<dir>/<slug>/`（先解到临时目录再改名，避免半成品被探测成「已安装」；含 zip 路径穿越防护）。
   路径以**参数列表**传给 subprocess（不经 shell）→ 天然规避 MSYS 路径转换与 UNC 拼接。
   另有 `--force` / `--dry-run` / `--json`，非法 slug → rc=2、已存在 → rc=4。
2. **`handle_need_tool.py`**：新增 `_helper_path()` / `_cli_has_flag()` / `_skillhub_id()`；
   `_install_command()` 改为首选自带安装器，CLI 降为后备；路径一律 `as_posix()`
   （正斜杠）且**拒绝出厂 UNC 形态**；`--dir` 亦转正斜杠（默认 `SKILLS_DIR` 在 Windows 上
   是 `C:\...` 形态，反斜杠嵌进 shell 命令会被当转义符吃掉）。
   `install_required` 载荷新增 `install_command` 字段，`skillhub` 字段由**拼出来的未验证 URL**
   改为 API 实测的 `canonicalName`（`@user_ff7413f5/<slug>`）。
3. **`refine_answer.py`**：渲染改用 `install_command`（并保留取包说明），不再渲染裸命令。
4. **`tool_mapping.json`**：`tiers` 新增 `install` 段（authority / namespace / cli_candidates /
   cli_note / command_template / command_note / verify_url），把上述三重坑与正确用法**固化进注册表**，
   避免后人再写回坏命令。
5. **文档同步**：`SKILL.md`（Tier Gate 表 install_required 行、Boundaries「Missing sibling skill」、
   「Only three cases」段）、`knowledge/system_prompt.md`（A 档安装段 ×3）、
   `README.md` / `README_zh-CN.md`（安装 FAQ）、`scripts/check_deps.py`（A 档安装提示）——
   全部由 `skillhub install` / `git clone` 改为 `python scripts/install_sibling.py <slug> --dir <skills-dir>`。
6. **测试**：`run_tier_gate()` 13 → **17 条**（新增 4 条：命令指向 `install_sibling.py` 而非裸
   `skillhub`、为绝对路径 + 显式 `--dir` 且目录值正确、**不含 UNC**、引用的安装器文件确实存在）；
   新增 `run_install_helper()` **7 条离线断言**（非法 slug ×4 → rc=2、已存在无 `--force` → rc=4
   且**早于联网核验**、`--help` 可解析）。联网路径由 e2e 手工验证，不进单元测试。

#### 第三轮验证
| 项 | 结果 |
|---|---|
| **端到端闭环**（本机真实联网） | 未装 → `install_required` → 执行 `install_command` → **`✓ 已安装 ct-registry v0.10.0`** → 重跑同卡 → **`status=ok`**（50 项试验，16.4s，含 `phase_mix` / `region_mix` 真实取值） |
| `install_sibling.py` 分支实测 | dry-run 报 v0.10.0；真装落位含 `SKILL.md` + `scripts/ct_registry.py`（即 `tool_mapping` 期望的入口）；重复安装 → rc=4；`ct-pipeline`（未上架）→ rc=3；`ct-protocol`（B 档）→ rc=3；`../evil` → rc=2 |
| `test_sibling_contract.py` | 契约 **4/4** + 门控 **17/17** + 安装器 **7/7**，`exit=0` |
| 其余回归 | `orchestrate --self-test` **8/8**；`route_tool --self-test` **22/22 + 6/6**；`test_modeB` **10/10**；`check_deps` 档位标注正确 |
| `SyntaxWarning` 全库扫描 | `scripts/*.py`（34 个）**零告警** —— 本轮两次因 docstring 里的 `\c` 触发告警并污染 stdout（导致下游 JSON 解析失败），已修 |

#### 第三轮遗留
- `install_sibling.py` 的**联网路径未进单元测试**（保持测试零网络），仅靠 e2e 手工验证 +
  离线拒绝分支回归保护。
- 本机 `~/.skillhub/skills_store_cli.py` 仍是精简版 v2026.3.6（下载端点走内网 LB）。
  自带安装器已不依赖它，故不影响功能；如需修复该 CLI，走 `skillhub self-upgrade` 或替换为完整版。

---

### 第四轮：安装姿态改为「建议安装」（2026-09-10，彤追加要求）

**要求原文**：「安装可能不能自动安装，会触发安全警告。改为建议安装，或者用户明确授权后再安装。」

**问题**：第三轮把安装命令修到「实测可执行」后，门控的默认语义仍是
「**征询同意 → agent 代办安装**」——只要用户点头，agent 就会去执行一条**下载 zip 并写入技能目录**
的命令。这类动作在本机会触发安全提示 / 权限询问（甚至被直接拦下），而文档与提示语把「同意」写得
过于轻（"是否安装？"），容易被理解成一次普通的确认。[^sec5]

[^sec5]: ct-base §5 只禁止「静默安装」（安装前须有人的审查节点），未规定**默认姿态**。本轮把默认
姿态收紧为「建议 / 明确授权」，是对该红线的**加强**而非放宽，并已回写 ct-base §5。

#### 改动（一个授权门 + 全套文案）
1. **`handle_need_tool.py`** —— 新增授权门：
   - 新增 `_APPROVE_WORDS`（approved / authorize(d) / consent / granted / yes / ok / agree / true …）；
   - `install_required` 载荷新增 **`install_mode`**（`"suggest"` 默认 / `"authorized"`）、
     `install_authorized`（布尔）、`install_note`（面向用户的「会写入本地技能目录、可能触发安全提示」说明）；
   - 只有 `install_consent` **明确命中授权词**才转 `authorized`；**缺省 / 含糊表态一律 `suggest`**；
   - `hint` 分两套：suggest → **「只建议、不执行」**（把命令原样给出，用户可自行执行；授权前不得代办）；
     authorized → 允许执行安装命令后带原卡重跑；
   - `install_hint` 去掉「由 agent 代为取包安装」式表述，改为「安装通道：SkillHub」。
   - 🔴 门控**状态集合不变**（`unreleased_b` / `unpublished_a` / `install_required` / `local_fallback` /
     `ok` …），故 `orchestrate.py` 的分流结构无需改动，只是在 `install_required` 分支内按
     `install_mode` 给出两种 `note`。
2. **`refine_answer.py`** —— 渲染分两态：suggest 版显式写出「**只建议、不执行**」「用户可自行执行」
   「在用户明确授权前，不得代为执行该命令」+ 安全提示 + `install_consent` 回执路径（中英双语）；
   authorized 版改为「用户**已明确授权**安装 → 执行上述安装命令」。标题行亦区分
   （`（**建议安装**）` vs `（用户已授权安装）`），authorized 版不再附「拒绝」分支文案。
3. **`tool_mapping.json`** —— `tiers.note` 内 `install_required` 的描述同步为「给安装建议（默认
   `install_mode=suggest`，不代办）」。
4. **文档同步** —— `SKILL.md`（frontmatter summary/description、Step 3b 行、Tier Gate 表
   `A · published, NOT installed` 行重写、Tier Gate 收尾红线段、「Only three cases」段、
   Boundaries 段、Tier split 段）、`knowledge/system_prompt.md`（新增「**Install posture**」红线条目，
   改写 A 档安装段 ×3 与 runner 状态说明）、`README.md` / `README_zh-CN.md`（安装 FAQ 改写为
   「建议安装 / 授权后代办」）、`scripts/check_deps.py`（A 档安装提示与汇总行）。
5. **`ct-base/docs/02-security-model.md` §5** —— 追加「**技能包安装（sibling skill）**」子条：
   经 SkillHub 安装兄弟技能包同样属「修改用户环境」且可能触发安全警告 → **建议优先、授权后执行**，
   检测侧代码只检测 + 上报，参考实现指向 ct-advisor `handle_need_tool.py` + `install_sibling.py`。

#### 验证（全绿，零网络）
| 项 | 结果 |
|---|---|
| `test_sibling_contract.py` | 契约 **4/4** + 门控 **32/32**（17 → 32：新增 15 条）+ 安装器 **7/7**，`exit=0` |
| 新增断言（门控） | 默认 `install_mode=suggest` 且 `install_authorized is False`；suggest 指引含「只建议」+「不得代为执行」+「明确授权」；**不含**「执行 install_command」；`install_note` 含安全提示；**5 个含糊取值**（`''`/`maybe`/`later`/`ask-me-tomorrow`/`sure?`）均不升级为已授权；`approved` → `install_mode=authorized`；authorized 指引允许执行命令；渲染层 suggest/authorized 措辞可区分（zh + en） |
| `orchestrate.py build_output` 实跑 | suggest → `note` 为「只建议、不执行」；authorized → `note` 为「用户已明确授权 → 执行其 install_command」；`install_request.install_mode` 透出正确 |
| 端到端渲染实跑 | 空技能目录 + `ct-registry` 卡：zh suggest 版含命令/安全提示/授权回执，authorized 版改为「已明确授权」并去掉拒绝分支 |
| 其余回归 | `orchestrate --self-test` **8/8**；`route_tool --self-test` **22/22 + 6/6**；`test_modeB` **10/10** |
| `SyntaxWarning` 全库扫描 | `scripts/*.py` **零告警**（本轮新增文案含 `"install_consent": "approved"` 转义，已确认不污染 stdout） |

#### 第四轮遗留
- 未改**授权词表**的国际化（`_APPROVE_WORDS` 为英文词 + `yes/ok`）；中文授权语（"授权安装"）
  由 agent 理解后落成 `install_consent="approved"`，不在代码里做中文匹配（避免歧义）。
- 仍未（也**刻意不**）实现「代码自动安装」：安装动作始终由 agent 在授权后执行，代码只检测 + 上报。

---

### 第五轮：README 示例逐条实测校对（2026-09-10）

**要求原文**：「实际跑一下技能 readme 中给出的示例，按照实际上的返回信息做 readme 内容的修改。」

**方法**：把 README 第 1 节的 8 个示例**原样实跑**（`orchestrate.py --payload-inline`，`difficulty/category`
按各自场景传入；数据类示例另跑 `refine_answer.py --card-inline` 补参重跑），逐条比对 README 的
「助手会这样回（示意）」与真实 stdout/stderr。原始输出留档在
`<session>/examples-run/ex1..ex8.{out,err}.txt`。

**实测结论（README 与真实行为不符之处，全部已改）**
| # | README 原说法 | 实测 |
|---|---|---|
| 1 | 直接给出估计目标要点 | Coze 单次调用；成功时是**分节长答**（五要素 + 三节延伸 + 依据 ICH E9(R1)/E3）；`refiner.timeout=60`，本轮实测 3–70 s，**超时回落本地草稿**（stderr `[coze] FALLBACK_TO_LOCAL_DRAFT 原因=ReadTimeout`） |
| 2 | 每条断言带「数据来源：ct-registry（<日期>）」 | 代码渲染的是分节标题 `## 补充信息（来源：ct-registry）`（**无日期**）+ 表格 + `./out
eport.xlsx`；Coze 叙事段可能自称「知识库未收录、需专项工具」 |
| 3 | 本地编排器**一次并行**调 ct-registry + ct-safety + ct-literature 并缝合战略简报 | 首轮返回 `<<<CT_TOOL_DELEGATE>>>`（`need_tool=ct-registry`、`need_tools=[ct-registry, ct-literature]`——**Coze 未列 ct-safety**、`missing_params=[cond]`）；**一张执行卡只跑一个技能**，多源需多轮 |
| 4 | Coze 拆解出完整方案 + 代码把 n 缝合回方案 | 返回委托块（`missing_params=[test, 效应量参数…]`）→ **先追问**；补参后追加的是 **JSON** `{"n_per_group":162,"total":324,"power":0.8,"solve_for":"n"}`，不是叙事改写 |
| 5 | 手写的「两个问题 + 六项菜单」 | `clarify_loop.py` 实测返回 2 个 `questions`（人群 / 终点）JSON；`menu.py` 分 3 条流程（methodology / data_intel / clarify），顶层能力选择 **4 项**；**若把 vague 直交编排器，仍会走 Coze**（实测 45 s） |
| 6 | 「Sure, I'll reply in English from now on.」 | 实测返回的是英文能力清单（7 类）+ 依据行「Language switching is a basic interaction function…」（约 42 s） |
| 7 | 直接给出带 DOI/PMID 的证据库 | 委托块缺 `topic` → 先追问；补参后答案正文是**检索日志 + 引文验证统计**（`{"total":20,"verified":19,"bot_blocked":1,…}`），证据清单落在 `out/lit_report.xlsx|html`、`out/evidence_log.json|md`；中文检索词提示改英文、无 Semantic Scholar key 跳过该源 |
| 8 | 两个转交并行完成 | 委托块 `need_tools=[ct-samplesize, ct-registry, ct-literature]` + 缺参 → **先追问**；补参后分轮执行 |

**改动**
1. `README_zh-CN.md` / `README.md` —— 8 个示例的「助手会这样回（示意）」全部换成「**实际返回（实测）**」
   （含真实数值、委托块字段、产物路径、追问参数）；📌 说明段同步改写（日期标签、一次一技能、
   need_params 先行、超时回退、样本量 JSON、文献产物、requests 运行前提）；示例 3 标题与第 2 节
   索引条目由「三源缝合」改为「多技能 · 逐轮」；版本号 v0.9.110 → **v0.9.111**（对齐 SKILL.md）。
   新增 FAQ 段：Coze 调用需要 `requests`，**不会自动安装**（缺失时打印 `python -m pip install
   "requests==2.32.3"` 并退出）；用缺库解释器运行时 `orchestrate.py` 返回 `⚠️ Coze 返回为空`。
2. `references/ADVANCED.md` —— 「Sibling skills」行由「GitHub clone 安装」改为 **SkillHub +
   `install_sibling.py`（建议安装 / 授权后执行）**；「Cloud analysis (Coze)」行的
   `requests`「auto-installed if missing」改为**不自动安装**（附实测两种降级表现）。
3. `knowledge/system_prompt.md` —— 宽口径需求由「一次调三源并缝合」改为「**先路由主技能、其余技能
   分轮执行**（runner 一张卡只跑一个技能）」；来源标签由 `"Data source: ct-xxx on <date>"`（代码并不
   渲染日期）改为与代码一致的 `## 补充信息（来源：ct-xxx）` 且**不得编造日期**。

**验证**
- 8 个示例全部真实跑通（`rc=0`；其中 2 次 Coze 60 s 超时按设计回落本地草稿，日志一致）。
- 补参重跑实测：ct-registry（20 项试验）、ct-samplesize（`n_per_group=162 / total=324`）、
  ct-literature（4 源并行、20 条引文、19 verified、产物落 `out/`）。
- 两份 README 行数一致（296 行 CRLF）、代码围栏配对（各 10 个）、**纯 CRLF 无混行**；
  `README.md` 与 `README_zh-CN.md` 的 8 处示例标题与 📌 段一一对应。

**遗留**
- README 第 2 节场景表里的「试试这样说」均为可直接照抄的问句，本轮**未逐条实跑**（只跑了第 1 节的 8 个示例）。
- 词表类差异（如 Coze 侧把 ct-safety 漏出候选）属上游 Coze 行为，本轮只如实记录，未改代码。

---

### 第六轮：串行回退消息的超时值改为真实有效超时（2026-09-10）

**要求原文**：「串行回退消息里把超时硬编码成 timeout=60，这个改一下。」

**问题**：`scripts/refine_answer.py` 串行（前台）路径在 Coze 调用失败/超时回退时，stderr 的
`FALLBACK_TO_LOCAL_DRAFT` 消息把超时**硬编码为 `timeout=60`**。但该路径的实际等待时长是**条件化**的
——长任务（`complex` 难度 / 模板类 category / 带对话历史的追问）走 `refiner.long_timeout=300s`，
其余走 `refiner.timeout=60s`。于是长任务超时也会误报「超时=60s」，与真实等待时长不符
（`adapters/refiner.py` 的 `_refine_serial` 内 `_log_fallback` 本就用真实值，只有串行回退消息这一处不一致）。

**改动**
1. `adapters/refiner.py` —— 新增公开方法 `CozeRefiner.resolve_timeout(req, timeout=None)`，作为
   `_resolve_timeout()` 的对外入口，供调用方复用同一套条件化判定（避免跨模块调用私有方法 / 二次实现）。
2. `scripts/refine_answer.py` —— 串行路径先 `build_refiner()` 拿到实例，再用 `refiner.resolve_timeout(req)`
   预解析本次有效超时（取不到则退回 `refiner.timeout`，再退回 60），回退消息改为
   `t("error.fallback_local", ..., timeout=eff_timeout)`；模块 docstring 同步写明「60s 默认 / 长任务 300s」口径。

**验证（端到端实测）**：用一版临时配置（`timeout=3 / long_timeout=7`，端点指向未监听的
`127.0.0.1:59999` 以强制快速失败）实跑串行回退：
- `difficulty=simple` 且**无对话历史** → stderr `… 超时=3.0s`（取 `timeout`）✅
- `difficulty=complex` → stderr `… 超时=7.0s`（取 `long_timeout`）✅

（改动前两者都会打印 `超时=60s`。）另 `refiner.resolve_timeout()` 单元验证：simple/middle → 60.0；
complex / 模板类 category / `is_followup` / 有对话历史 → 300.0；显式传入覆盖生效。`py_compile` 两文件通过。

**遗留**：其余调用路径（`orchestrate.py`、竞速 `--collect`、`--fire-only`）本就不打印该硬编码消息，
无需连带改动；`adapters/refiner.py` 自 2026-08-16 起已用真实值，仅串行回退消息此前不一致。

---

### 第七轮：默认 Coze 超时 60s → 90s（2026-09-10）

**要求原文**：「timeout=60，增加到 90。」

**改动**：`config.json` 的 `refiner.timeout` 由 `60` 提到 `90`（`long_timeout=300`、`race_window=30` 不变）。
连带同步所有把「60」当默认超时的地方（跨模块默认值、条件化判定注释、回退消息兜底、文档）：

| 位置 | 改动 |
|---|---|
| `config.json` | `refiner.timeout`: 60 → **90** |
| `adapters/__init__.py` | `rc.get("timeout", 60.0)` → **90.0** |
| `adapters/refiner.py` | `Refiner.refine` / `CozeRefiner.__init__` 形参默认 60.0 → **90.0**；类 docstring、`_resolve_timeout` / `_is_long_running` 及 fire-only 注释中的「默认 60s」→「90s」（共 13 处） |
| `scripts/refine_answer.py` | 串行回退兜底 `eff_timeout = 60` → **90**、`getattr(refiner,"timeout",60)` → **90**；模块 docstring |
| `README.md` / `README_zh-CN.md` | `refiner.timeout = 60` → **90**；回退示例 `超时=60.0s` → **90.0s** |
| `SKILL.md` / `references/ops.md` / `references/steps.md` | 表格/流程里「60s timeout」「60 s = 1 minute」「returns within 60s」→ **90s** |

**未改动（有意保留）**：`scripts/install_sibling.py` 的下载 `TIMEOUT=60`（安装器下载，与 Coze 无关）；
`scripts/tool_mapping.json` 中 ct-samplesize 的本地执行 `timeout: 60`（本地纯计算，非 Coze 调用）；
`adapters/coze/src/utils/file/file.py` 的 `requests.get(..., timeout=60)`（Coze 平台 vendored 代码）；
`adapters/refiner.py` 内的百分比示例 `40%~60%` 与「60 分钟缓存 TTL」（非超时语义）；
`adapters/coze/**` 的 refiner 契约快照（平台侧副本，不随发布副本）。

**验证**
- `config.json` 解析：`refiner = {timeout: 90, long_timeout: 300, race_window: 30}`。
- `build_refiner()` 实取 `timeout=90.0`；`resolve_timeout()`：simple/middle → **90.0**，complex / 追问 → **300.0**。
- `py_compile` 三个改动文件通过；`orchestrate.py --self-test` / 契约测试 / 门控门测无回归。

**版本**：v0.9.111 → **v0.9.112**（`SKILL.md` + 两份 README 同步）。

---

### 第八轮：README 案例改为「用户可见」表述（2026-09-10）

**要求原文**：「现在 readme 中案例的结果输出不对，非常的 IT 化，需要按照用户所见即所得的内容，给出对于用户而言能够理解的回答内容。」

**问题**：第 1 节 8 个示例的「助手实际返回」直接铺陈**内部协议**——`need_tool` / `need_tools` / `missing_params` 委托块、
`<<<CT_TOOL_DELEGATE>>>`、样本量 JSON `{"n_per_group":162,…}`、ct-literature 的 `[OK] source …` 检索日志与引文统计 JSON、
`./out/…` 产物路径、stderr 回退日志——这些是**编排层协议、用户在对话框里看不到**，读起来非常 IT 化。

**改动**（两份 README 同步，结构逐条对齐）
1. 每个示例的「助手实际返回」改为**用户可见的自然语言回答**（要点 / 表格化表述），保留真实实测数值
   （示例 2 的 50 项 / 分期·地域·申办方分布；示例 4 的每组 162 / 合计 324；示例 7 的 20 篇 / 19 篇核验通过）。
2. 末尾统一加**一行**内部机制注（📌 / 📌 Under the hood），替代原先冗长的技术说明段；
   删除示例内所有 fenced code block（委托块 / JSON / 检索日志），两份 README 代码围栏归零。
3. 多轮案例（示例 3 / 4 / 7 / 8）改为**两段**：「第 1 轮 · 追问」（用户收到的自然语言提问）+
   「补参后 · 最终答案」（可读结果），覆盖「先追问缺参再执行」的真实行为。
4. 第 1 节导语由「节选自真实运行输出」改为「展示你在对话框里实际看到的内容」。
5. 标题微调：示例 1「转发，不弹菜单」→「直接作答，不弹菜单」；示例 4「转发，由 Coze 拆解」→「先追问，再计算」。

**未改动**：示例 3 的候选技能来源（`need_tools` 含 ct-registry / ct-literature）、示例 1 / 4 / 7 的实测耗时等
仍与内部行为一致，只是不再以协议字段形式裸露；示例 3 / 8 补参后的最终答案为**结构示意**（该多轮路径未逐条实测到最终文本），
以概括性描述呈现、未编造具体数值。

**验证**
- 两份 README：各 **8 个示例**、结构一一对应；**纯 CRLF（319 行 / 0 bare-LF）**；代码围栏 **0**（无残留半截围栏）。
- 全库扫描：`示意` / `measured, excerpted` / 委托块字段 / 检索日志等旧表述仅剩 **CHANGELOG 历史条目**（保留为史实）。

**版本**：v0.9.112 → **v0.9.113**（`SKILL.md` + 两份 README 同步）。

---

### 第九轮：示例 1 换题 + 兄弟技能调用后提示「直接用该技能」（2026-09-10）

**要求原文（三条）**：
1. 「中文 readme 开头做了修改。」（用户已手改中文版开头 → 英文版需同步为同一口径）
2. 「示例 1 似乎空泛了一些，考虑换一个？」
3. 「调用其他技能的时候，需要确认真实的输出应该建议用户直接使用相关技能得到更详细的输出。」

**改动**
1. **示例 1 换题**：原题「优效设计、两平行组，主要估计目标该怎么设？」的答案是一份通用 E9(R1) 五要素清单，偏空泛。
   换为具体场景「III 期肿瘤试验，主要终点 OS，试验组进展后允许交叉使用对照药 —— 主要估计目标该怎么设？」，
   并按**实测**（`examples-run/run_examples.py ex1_methodology`，70.3s）改写答案：治疗政策策略 vs 假设策略（RPSFTM / IPCW）、
   ITT/FAS 与 PPS、样本量按交叉率放大、进展后治疗史采集、PFS/ORR 次要终点。
   ⚠️ 注：Coze 两次运行**侧重不同**（一次以治疗政策为「首选」、一次称假设策略为「主流」），故正文改为**中性并列**——
   「取哪一种取决于你要回答的临床问题」，不采信单次运行给出的主次排序。
2. **💡 建议行（代码改动）**：`refine_answer.py` 的 `_merge_answer()` 在缝合 `## 补充信息（来源：ct-xxx）` 时，
   追加一行「以上为该技能结果的可读摘要；如需核实或获取更详细的原始输出，建议直接使用 `ct-xxx` 技能。」
   （zh/en 随提问语言由 `_detect_lang` 切换）。实测 ex2（ct-registry，35.2s）已在 `<<<CT_ANSWER_END>>>` 前出现该行。
   两份 README 的示例 2 / 3 / 4 / 7 / 8 同步显示该行；§2 场景索引注 + §3 FAQ（来源标注条）补充说明；`SKILL.md` 增补该行为说明。
3. **英文开头同步**：删除与实测不符的「prefetch … **in parallel** with the Coze cloud workflow」表述，
   改为与中文一致的口径（本地编排器 / 需要时本地运行兄弟技能、代码内缝合）。
4. **中文版格式修复**（用户编辑器把该文件存成了 LF）：恢复 **CRLF**；清除 5 处 `\r>` 残字（示例 4 / 7 的追问行、`<div>` 图标块、FAQ 标题）
   与 3 处 HTML 实体（`&#x542B;`→含、`&#x4E0E;`→与、`&#x7684;`→的）。

**验证**
- `_merge_answer()` 单元验证：zh / en 两路均在来源小节后正确追加 💡 行。
- 两份 README：CRLF=374 / 335，**bare-LF=0、bare-CR=0**，HTML 实体 **0**，代码围栏 **0**；💡 各 7 处（5 个示例 + §2 索引注 + FAQ）。
- 端到端复测：ex1（70.3s）、ex2（35.2s）rc=0；`orchestrate.py --self-test` 与契约测试见下。

**版本**：v0.9.113 → **v0.9.114**（`SKILL.md` + 两份 README 同步）。

---

### 第十轮：答案长度失控——云端「作答契约」（2026-09-10）

**触发（彤）**：示例 1 的答案「讲得很细，反而最终没有回答这个问题。请全面评估应该如何修整技能。」

**诊断（端到端追查）**：`route.py` → Coze `validity_check` → 两个出答案节点 → 节点提示词原文 → 部署包。根因不在示例 1，而在**云端提示词**：

| # | 根因 | 证据 |
|---|---|---|
| 1 | 两个出答案节点都取消了字数上限 | `full_analysis_cfg.json` 的 sp：「本节点**不设置任何字数上限**」；`review_cfg.json` 的 up 同样写「不设置字数上限」，且两者都允许 `###` |
| 2 | 档位字数上限成死条文 | v1.5 的 simple ≤150 / middle ≤400 / complex ≤600 字只写在 `coze_system_prompt_v1.4.md`，该文件**全库零代码引用**；真正生效的是 `config/*.json` |
| 3 | 激励反向 | sp 明写「质量优先于标签……**绝不为迎合难度标签而压缩覆盖**」 |
| 4 | 「紧扣问题」被降级 | 埋在「废话约束」里，且只管润色措辞，管不住「多写整节未被问到的议题」 |
| 5 | 拆分放大 | `generate_organized_problems` 对 complex 拆 ≤7 条子问题 → 每条一小节 |
| 6 | 难度判偏 | `judge_difficulty` 把单点方法学问句判 complex，与本地 `steps.md`「纯方法学问句永远 simple/middle」冲突 |
| 7 | 对「该怎么设」不给推荐 | 无「决策型问题必须给一个推荐项」规则 → 并列两案并把选择推回用户 |
| 8 | 文档替缺陷背书 | 第九轮把实测输出「中性化」写进 README，等于把缺陷固化成文档 |

**实测证据（本轮新建，存 `examples-run/`）**
- `ex1_prefix_sprawl_alpha.out.txt`：问「III 期确证性试验计划做一次期中分析，怎么把总 I 类错误率控制在 0.05？」→ **5 节 / 4522 B**，含 **DSMB 角色与决策流程、信息时间选取、边界分配规则**等未被问到的整节（79s 返回，未超时）；
- `ex1_prefix_sprawl_crossover.out.txt`：交叉用药估计目标题 → 多节，且**被 `max_completion_tokens` 截断在「### 四」**；另一轮在治疗政策 / 假设策略间摇摆、不给推荐。

**修复（作答契约，写入 4 个真正生效的节点配置）**
- **C1 先答后展**：第一段必须独立完整回答字面问题；决策 / 构造型问题**必须先给一个明确的推荐答案**（要素填满），再 ≤3 句理由；禁止把答案拆散到多节、禁止把选择推回用户。
- **C2 边界锁定**：只答 original_question 问到的内容；未被问到的相邻议题**不得单独成节**，需要时折叠为末尾**一行**「如需，我可以进一步展开：①…②…③…」。
- **C3 难度即字数硬上限**：simple ≤150 / middle ≤400 / complex ≤600 字，禁用 `###`；明写「不得以完整覆盖为由超限或新增未问议题」。
- **C4 单一推荐**：并列方案最多一行。
- **落点**：`config/full_analysis_cfg.json`（sp+up）、`config/review_cfg.json`（sp+up）顶部 + 尾段 + 自检；`config/generate_organized_problems_cfg.json`（拆分只按问到的维度 + 自检一条）；`config/judge_difficulty_cfg.json`（收紧 complex）；`knowledge/methodology-core.md`（镜像）。
- **同步本地 brain**：`knowledge/system_prompt.md`、`knowledge/methodology_core.md`（同一 Answer contract + 反模式两条）；`SKILL.md`（硬门控清单加「作答契约」条，并明确 agent 是管道、**不得本地改写**长答案）；`references/steps.md`（Step 0 注明难度已驱动硬预算）。
- `coze_system_prompt_v1.4.md` 顶部加**「无代码引用、改动无效」横幅**，防同类失效重演。
- 示例 1 换成**单点有唯一正解**的题（期中分析 α 控制），并标注「修复后目标形态，待重部署后以实测替换」。

**交付**：Coze 部署包 **`ct-advisor_coze_v1.11_20260910.zip`**（99 文件，沿用「不含 refiner_contract*.md」红线）；`README_部署说明.md` 更新为 v1.11（含部署后探活验证点）；`coze_modification_guide.md` 新增「〇、作答契约」节。

**未完成 / 待办**
- **需重部署**：契约写在云端 `config/*.json`，**必须上传 zip + 重建镜像**才生效 —— 本地无法验证效果。
- README 示例 1 的答案目前是**目标形态**而非实测；重部署后应重跑一次并以实测文本替换。

**版本**：v0.9.114 → **v0.9.115**。

### 第十一轮：C3 由「字硬上限」校准为「预期量级 + 硬天花板」（2026-09-10）

**触发（彤）**：「C3 难度即字数硬上限，不过原先的上限是否过严，导致有时候太精简？以前的做法是参考而不是硬上限。」

**诊断**：第十轮把答案从「多节长报告」拉回正轨，但 C3 本身有两个反向缺陷：

| # | 问题 | 证据 |
|---|---|---|
| 1 | 只给上限、不给下限 | C3 表只有「≤150 / ≤400 / ≤600 字」。天花板是缩短的**许可**，不是说全的**义务** → 模型达标的唯一路径是删要素 |
| 2 | 明文压过完整性 | C3 写「不得以『完整覆盖 / 质量优先』为由突破字数上限」，即 **C3 战胜 C1**；而 C1 要求「把要素填满」。冲突时按 C3 执行 → 删要素 |
| 3 | 中英单位不一致（真 bug） | `config/*.json` 写 `字`，而 `knowledge/methodology_core.md` / `knowledge/system_prompt.md` / `references/steps.md` 写 **words**；400 words ≈ 600–700 中文字，两层预算差约 **1.6 倍**。且 `adapters/coze/src/kb/__init__.py` 确有 `get_knowledge("methodology-core")` → 该「words」版本**真的会喂给云端模型** |
| 4 | middle 是重灾区 | `judge_difficulty_cfg.json` 把单点方法学问句（「该怎么设估计目标」「怎么控 α」「A 与 B 哪个更合适」）**一律判 middle**，故最常见题型拿最紧预算；complex（600）反而不常触发 |

**历史反向证据**：`refiner_contract.md` 记载 CTDB (3).xlsx 41 条中 simple 题 ≤150 字达标率仅 **38%**（目标 80%）——说明 150 对模型自然输出偏紧、需主动压缩；但 simple 题压缩无信息损失，故痛点集中在 middle / complex。

**修复**
- **C3 改为「预期量级 + 硬天花板」**：simple ~100 / ≤200 · middle 300–500 / ≤700 · complex 500–800 / ≤1000（**中文字符**）。
- **新增最高优先条款：要素完整（C1）优先于字数（C3）**——字数只约束**冗余**，不约束**回答原问题所必需的要素**。
- **明确删除顺序**：天花板仅在超出预期量级且确有冗余时触发；触发后按 **① 跑题内容（C2）→ ② 重复 / 稀释 → ③ 表述压缩** 删减。
- **明写禁止**：不得为压字数删要素 / 依据 / `⚠️ 待核实` 标注；宁可靠近天花板也不得删要素；若填满要素仍逼近天花板，说明该题**被低估档位**。
- **单位统一为「字」**：英文知识层改为 `~100 chars` / `300–500 chars` / `≤200` / `≤700` / `≤1000 chars`，并加注与节点配置一致，从根上消除两层互相矛盾的预算。
- **落点**：`config/full_analysis_cfg.json`（sp+up+自检 20）、`config/review_cfg.json`（sp+up）、`config/judge_difficulty_cfg.json`（sp）；`knowledge/methodology_core.md` + 云端镜像 `adapters/coze/knowledge/methodology-core.md`（保持逐字节一致）、`knowledge/system_prompt.md`、`references/steps.md`、`SKILL.md`。

**交付**：Coze 部署包重出为 **`ct-advisor_coze_v1.12_20260910.zip`**（**累积包**：v1.10 + v1.11 作答契约 + v1.12 C3 校准，**取代尚未部署的 v1.11**）；`README_部署说明.md` 与 `coze_modification_guide.md` 增补本节。

**未完成 / 待办**
- **仍需重部署**（上传 zip + 重建镜像）后才生效；README 示例 1 的答案仍是**目标形态**、非实测，重部署后应重跑替换。
- 新数值（200 / 700 / 1000）为**设计取值**，非实测校准值；重部署后建议用 `examples-run/run_examples.py` 复跑 8 个示例，按真机长度回校。

**版本**：v0.9.115 → **v0.9.116**。

### 第十二轮：重部署后复跑 8 例 + 修复暴露出的「路由裸子串」缺陷（2026-09-10）

**触发（彤）**：「已更新，重跑一下。」——v1.12 已上传 zip 并重建镜像，复跑 README 8 例回校长度，并把示例 1 的占位答案换成实测文本。

**复跑结果（8 例，Coze 已重部署）**

| 示例 | 返回形态 | 结果 |
|---|---|---|
| 1（中文·方法学控 α） | 直接作答 | ✅ **373 字 / 262 汉字**（修复前 **1657 字 / 5 分节**且始终未回答「怎么控 α」）；3 次复跑 548 字，稳定直答 |
| 2（注册试验检索） | ct-registry 缝合 | ✅ 直答 + 50 项注册试验三张分布表 + `report.xlsx` + 兄弟技能提示 |
| 3（竞品情报） | 委托 | ✅ `need_tools=[ct-registry, ct-literature]` |
| 4（II 期设计 + 样本量） | 委托 | ✅ `ct-samplesize`，缺 `test` + 效应量参数，按预期追问 |
| 5（模糊需求） | 本地澄清 | ✅ 198 B 澄清话术 |
| 6（切英文） | 直接作答 | ✅ 496 B 英文确认 |
| 7（已发表安全证据） | 委托 | ✅ `need_tools=[ct-safety, ct-literature]` |
| 8（文献 + 样本量） | 委托 | ✅ `need_tools=[ct-samplesize, ct-registry, ct-literature]` |

**复跑暴露的问题**：英文版示例 1 未正常作答，而是委托 `ct-registry`。逐层定位后确认是**两层互不相关**的缺陷：

| # | 层 | 缺陷 | 证据 |
|---|---|---|---|
| 1 | **本地** `scripts/route_tool.py` | registry 触发词含**裸词** `\btrials?\b`：任何含英文 "trial" 的问句都判为检索注册试验；而 METHOD/DEF 兜底词**只有中文**，英文方法学问句直接穿透 | `predict()`：同问句 EN → `ct-registry`（缺 cond）；ZH → `None` |
| 2 | **云端** `src/graphs/nodes/tool_router_node.py` | 词表用**裸子串** `in` 匹配：`ror` 命中 `error`、`sign` 命中 `design` / `signals` | A/B 实测：同问句仅把 `error` 换成 `alpha` → 由 `need_tool=ct-safety` 变为正常作答 |

**修复（已自测 / 对照验证）**
- **本地**：registry 英文裸词改为「介词 / 逗号 / 句末」**锚定** —— `(?:clinical\s+|oncology\s+)?trials?\b(?=\s*(?:[,;]|\b(?:for|in|of|on|among|with|from)\b|$))`。`trials for/in/of`、`trials,` 等真实检索句式仍命中；`trial plans / trial design` 等方法学用法不再命中。新增 2 条 self-test 回归用例。
- **云端**：新增 `_kb_hit()` —— 纯 ASCII 词条改用**词边界**匹配（`(?<![a-z0-9])…(?![a-z0-9])`），中文词条仍按包含匹配；`TOOL_RULES` 与 `GUIDELINE_TERMS` / `GUIDELINE_SEARCH_INTENT` 均接入。新旧对照：`type I error rate` → `[ct-safety]` ⇒ `[]`；含 `design` / `safety signals` 的英文示例 3/4 由被 `GUIDELINE` 误拦恢复为正确多源命中。

**已知残留（未改，待决策）**
- 云端**没有**「咨询意图」护栏（本地有 `METHOD` / `DEF` / `DOC`），故裸词 `clinical trial` 仍会把**设计咨询题**判成检索。实测：`…structure for a clinical trial in an ultra-rare…` → `need_tool=ct-registry`；把 `clinical trial` 换成 `study` → 正常作答（3480 B）。
- 云端语义缓存（≥95% 相似即命中）会让**英文提问命中中文缓存**：英文示例 1 复跑时多次直接返回中文答案，且同一 payload 两次结果不同（一次作答、一次委托）——这解释了修复前的「时好时坏」。

**交付**
- **本轮不重出部署包**：云端修复**暂存于 `src/`**，等「残留项」定了方向再一次性出包，避免为一个未完成的修复让用户重复部署。
- 本地修复**即时生效**（无需重部署）。
- README 示例 1 答案由「目标形态」替换为 **2026-09-10 重部署后的实测输出**（中英双版同步；英文版为等义译文并如实标注）。

**验证**：`route_tool --self-test` 24/24 + 参数 6/6、`route.py --self-test` 29/29、`orchestrate --self-test` 8/8、`test_modeB` 10/10、`test_sibling_contract` 契约 4/4 + 门控 32/32 + 安装器 7/7、`test_seven_flows` 7/7；云端节点文件可加载执行。

**版本**：v0.9.116（未升版 —— 部署包未重出）。

### 第十三轮：README 示例改版（实操题上位）+ 修「在研」误命中与云端词表主循环补漏（2026-09-10）

**触发（彤）**：「建议前面的案例换成下面这种实操性的问题会更有代表性。」——给出两条角色实操题：
① 研究者／受试者补偿（SAE 提前退出是否该付全额 5000 元交通补贴，GCP 有何要求）；
② 药物警戒／预期性判断（IB 列「少见」但实测 15%，是否需更新 IB 与标签）。

**示例区改版（用户选「只换示例 1」，中英双语同步）**

| 新编号 | 主题 | 分类 | 来源 |
|---|---|---|---|
| 示例 1 | 受试者补偿怎么给（GCP 判断） | `methodology:D`（GCP & quality） | 本轮新增（用户提供） |
| 示例 2 | 预期性判断：要不要更新 IB 和标签 | `methodology:F`（Safety & DSUR） | 本轮新增（用户提供） |
| 示例 3 | 单一维度数据需求（ct-registry） | — | 原示例 2 |
| 示例 4 | 宽口径竞品情报（多技能 ⭐） | — | 原示例 3 |
| 示例 5 | 多部分设计任务（先追问再计算） | — | 原示例 4 |
| 示例 6 | 不确定要什么（模糊 → 本地澄清） | — | 原示例 5 |
| 示例 7 | 切换输出语言 | — | 原示例 6 |
| 示例 8 | 已发表安全性证据核查（ct-literature） | — | 原示例 7 |
| 示例 9 | 方案证据基础 + 样本量协同 | — | 原示例 8 |

- 原示例 1（方法学控 α）**移出示例区**；其「修复前 1657 字 / 5 分节 → 修复后 373 字」的对照证据保留在第十二轮小节。
- 多轮案例编号同步更正：示例 3 / 4 / 7 / 8 → **示例 4 / 5 / 8 / 9**；「下面 8 个示例」→「**9 个示例**」。
- 两条新答案均为 **2026-09-10 实测输出**（非目标形态）：
  - 示例 1 —— **383 字 / 313 汉字**：首句给结论（应付全额、不得扣减），随后两条执行要求，依据《药物临床试验质量管理规范》2020 年版。
  - 示例 2 —— **465 字 / 362 汉字**：首句给结论（默认需更新 IB），再分三步（数据校准 → 因果关联评估 → 更新动作落地），依据 ICH E2F + CDE RSI 指引。

**改版过程中暴露并修复的缺陷（同一类「裸词/裸子串过匹配」，第三次复发）**

| # | 层 | 缺陷 | 证据 / 影响 | 修复 |
|---|---|---|---|---|
| 1 | **本地** `scripts/route_tool.py` | registry 触发词含裸词 `在研`，命中「在研**究者**手册」 | 示例 2 实测被委托 `ct-registry` 且追问缺失参数 `cond`（`route_tool.predict` → `ct-registry`, confidence=high） | 改为 `在研(?!究)`：「在研究者」「在研究中」不再命中；「在研药物／在研项目／在研试验」仍命中。`REG_INTENT` 同步 |
| 2 | **云端** `src/graphs/nodes/tool_router_node.py` | 第十二轮新增的 `_kb_hit()` **只接上了 `GUIDELINE_TERMS` / `GUIDELINE_SEARCH_INTENT`**，`TOOL_RULES` 主循环仍是裸子串 `if any(kw in q for kw in keywords)` —— 即 `ror` ⊂ `error`、`sign` ⊂ `design` 的修复**从未真正生效** | 上一轮「已修」的记录与实际代码不符（本轮 grep 发现） | 主循环改用 `_kb_hit`；`DOC_WORDS` / `LIT_FIRST_WORDS` / `REG_INTENT_WORDS` 三处判定一并接入 |
| 3 | **云端** 同文件 | 边界写法 `(?!s?[a-z])` 会被正则回溯绕过（`s?` 可取空 → `[a-z]` 命中复数尾字母）→ **误伤全部复数形式召回** | 实测 `adverse events` / `sample sizes` / `systematic reviews` / `landscapes` 4 条全挂 | 改为 `(?<![a-z])<kw>s?(?![a-z])`：保留复数与「紧跟数字」（`NCT04512345`）召回，同时仍拦住 `sign` ⊂ `signals` |

**新增回归测试**：`scripts/test_tool_router.py` —— 云端词表命中语义 + 端到端主判，**39/39**。
用 stub 顶掉 langchain / langgraph / coze 运行时依赖后**直接加载真实节点文件**，不依赖 Coze 环境；
模块加载失败判为**失败**而非跳过（防「静默不测」）。词表的 `~<regex>` 转义约定亦由该测试锁定。

**已知残留（未改，仍待用户决策）**
- 云端**没有**「咨询意图」护栏（本地有 `METHOD` / `DEF` / `DOC`），故裸词 `clinical trial` 仍会把**设计咨询题**判成检索。
  实测：`…structure for a clinical trial in an ultra-rare…` → `ct-registry`；换成 `study` → 正常作答 3480 B。
- 云端 registry 词表缺 `竞品` / `适应症`（本地有），故纯中文竞品情报句在**云端**判 `ct-safety`；
  实际链路由**本地预判优先**兜住（判 `ct-registry`），端到端无影响。
- 代码注释中大量历史「README 示例 N」标注随本次改版**整体 +1**（原示例 1 已移除），本轮未逐条回改，已在 CHANGELOG 记录映射。

**交付**
- 部署包重出为 **`adapters/coze/ct-advisor_coze_v1.13_20260910.zip`**（累积包，取代 v1.12；v1.12 移入 `_archive/`）。**仍需上传 zip + 重建镜像**才生效。
- 本地修复（`route_tool.py`）**即时生效、无需重部署** —— 故 README 两条新示例在**当前部署**下即可正确作答。

**验证**：`route_tool --self-test` **27/27** + 参数 6/6、`route.py --self-test` 29/29、`orchestrate --self-test` 8/8、
`test_tool_router` **39/39**、`test_modeB` 10/10、`test_sibling_contract` 契约 4/4 + 门控 32/32 + 安装器 7/7、`test_seven_flows` 7/7。

**版本**：v0.9.116 → **v0.9.117**。

### 第十四轮：云端补英文咨询意图护栏 + 回答姿态改为「先自身作答、末尾建议」+ 调用门槛收紧（2026-09-10）

**触发（彤）**：「云端补英文咨询意图护栏，镜像本地的 METHOD/DEF/DOC 逻辑。因为有关键词误报的问题，技能的回答逻辑需要调整：需要调用 ct-系列技能的时候，advisor 首先基于自身能力回答，最后再建议是否安装兄弟技能。同时缩窄调用其他技能的关键词命中范围。只有需求关联非常明确的时候才进行调用。」

**口径确认（AskUserQuestion）**
- 已安装技能 + 需求「非常明确」→ **仍自动调用**取真实数据（保留 ct-advisor 取数核心价值）；
- 「非常明确」的阈值 = **仅强专有词 / 句式**（泛词不再单独触发）。

#### ① 云端补齐英文咨询意图护栏（镜像本地）
- **缺陷**：云端 `tool_router_node` **只有词表、没有任何咨询意图护栏**，且本地 `route_tool` 的 `METHOD` / `DEF` / `DOC` **只有中文**。
  于是英文方法学问句直接穿透：实测「A confirmatory Phase III trial plans one interim analysis — **how do I keep the overall type I error rate at 0.05?**」
  因含裸词 `trial` 被判 **ct-registry**（并弹 `cond` 追问）。
- **修复**：新增 `_CONSULT_DEF` / `_CONSULT_METHOD` / `_CONSULT_DOC`（中英并列）与 `_RETRIEVAL_INTENT` 例外，
  `_consultation_intent()` 在 `_match_tool` **最前置**调用：命中护栏且**无明确取数动作** → 原生作答、不委托。
  本地 `route_tool` 同步补齐英文等价词（两处同义、需同步改）。
- **踩坑**：护栏判断**必须用小写文本**——英文护栏词区分大小写，句首 `How do I…` 否则不命中（已加注释与回归）。

#### ② 调用门槛收紧：强触发词 vs 弱触发词
- **强触发词（`TOOL_TRIGGERS` / `TOOL_RULES`，自动调用）**：① 具名数据源（NCT / ClinicalTrials.gov / FAERS / PubMed / OpenAlex…）；
  ② 具名统计量或高特异性方法（PRR / ROR / EBGM / 去激发再激发 / 因果关系判定 / 具体 irAE / 病例报告 / meta 分析…）；
  ③「检索动词＋明确对象」完整句式（`检索…注册试验`、`Pull the registered trials for…`、`找…文献`）。
- **弱触发词（`WEAK_TRIGGERS`，只建议不调用）**：`信号` / `文献` / `试验` / `安全性` / `设计` / 裸 `注册` / `在研` 等——一律不再自动调用。
- 保留 `LIT_FIRST` / `REG_INTENT` 协同规则与「文献强意图上位」逻辑。

#### ③ 回答姿态：先自身作答 + 末尾建议
- **新增** `route_tool.suggest_footer(tools, lang)`：产出答案**末尾**的软建议（中英随提问语言），
  文案明确「以上已按本技能自身能力作答；如需真实数据或更深入分析，可安装 / 调用后再补充」。
- **接线**：`orchestrate.build_output` 新增 `suggest_tools` 形参与 `_wrapf()` 局部包装（9 处 `_wrap(` 改走 `_wrapf`）；
  `refine_answer --ship` 在 `_emit_wrapped` 前、且 `need_tool` 为空时追加软建议。
- **`install_required` 改为非阻断**：由「`<<<CT_TOOL_DELEGATE>>>` 委托补参 / 安装」改为
  「**答案在前、安装建议在后**」的包裹答案（复用 `_merge_answer` 的 install 渲染，安全姿态不变：只建议、不执行）。
- `predict()` 返回结构新增 `suggest_tools`；`need_tool` 仍为兼容字段。

#### 验证（全绿）
- `route_tool --self-test` **34/34** + 软建议 **6/6** + 参数 6/6（新增「泛词不触发」「软建议」断言）
- `test_tool_router`（云端，新增咨询护栏 + 软建议两组断言）**58/58**
- `route.py --self-test` 29/29、`orchestrate --self-test` **9/9**（新增软建议断言）、
  `test_seven_flows` **8/8**（F7 题干换为强触发词，新增 F8「弱命中 → 包裹 + 末尾软建议」）、`test_modeB` 10/10、
  `test_sibling_contract` 契约 4/4 + 门控 32/32 + 安装器 7/7。

**交付**
- 部署包重出为 **`adapters/coze/ct-advisor_coze_v1.14_20260910.zip`**（累积包，取代 v1.13；v1.13 移入 `_archive/`）。
  **仍需上传 zip + 重建镜像**才生效；本地改动（本地路由 / 编排 / 缝合）**即时生效**。

**版本**：v0.9.117 → **v0.9.118**。

### 第十五轮：交接口径更正（以代码为准）+ 修复「软建议溢出」（2026-09-10）

**触发（彤）**：接手第十四轮交接文件后复核，发现两处不一致 → 裁定「① 按代码文件改；② 修改」。

#### ① 交接口径更正（仅文档，无代码改动）
- 交接文件 §4.2-2 原把「查 XX 药的文献」列为「**无强触发**」的弱命中抽验句，**与代码 / 测试矛盾**：
  `route_tool.py` SELF_TEST 断言该句 → `ct-literature`（高置信）；`test_tool_router.py` 亦断言
  「帮我找 XX 药治疗肺癌的最新文献」→ `ct-literature`，并把该句列入护栏让位用例。按强触发规则③
  「检索动词＋明确对象」，**该句本就是强命中**。
- **以代码为准（用户裁定）**：更正 `docs/HANDOVER_20260910_round14.md` §4 抽验口径——弱命中抽验句改用
  「查 XX 药的安全性信号有哪些」；同一文件头部（版本 / 部署包 / 技能目录路径）与 §0 状态一并更正。

#### ② 修复「软建议溢出」（本地 + 云端同步）
- **缺陷**：第十四轮把误报从「阻断式自动调用」降级为「非阻断式末尾建议」，但**建议侧词表未同步收紧**——
  咨询意图护栏命中时仍回落到弱词表，于是裸弱词 `trials?`（ct-registry 词表项）会给**纯定义 / 方法论题**
  附一条题不对路的建议。即已消灭的误报换个位置继续出现。
  实测三句此前均建议 `ct-registry`：「…how do I keep the overall type I error rate at 0.05?」、
  「What is the difference between ITT and mITT in a confirmatory trial?」、「How do I design a Phase III clinical trial?」。
- **修复**：护栏命中时**只保留强命中的建议**（具名数据源 / 具名统计量 / 高特异性方法 / 完整检索句式）。
  - `scripts/route_tool.py`：护栏分支 `_none(strong + weak)` → **`_none(strong)`**。
  - `adapters/coze/src/graphs/nodes/tool_router_node.py`：`_suggest_tools(question, strong_only=False)`
    新增形参，`strong_only=True` 时跳过 `WEAK_TRIGGERS`；调用点传
    `strong_only=_consultation_intent(state.original_question)`。
- **设计边界**：护栏只压**弱词溢出**；问题中若确有**具名数据源 / 统计量**（如「什么是 FAERS 信号」），
  建议照留——那本就是真命中。

#### 验证（全绿）
- `route_tool --self-test`：工具命中 **34/34** + 软建议 **10/10**（新增 4 例）+ 参数 6/6。
- `test_tool_router`（云端）**63/63**（新增 5 例）；测试改按**生产调用形态**取值
  （`strong_only=_consultation_intent(q)`），避免默认参数掩盖回归。
- 其余 5 套：`route.py` 29/29、`orchestrate` 9/9、`test_seven_flows` 8/8、`test_modeB` 10/10、
  `test_sibling_contract` 契约 4/4 + 门控 32/32 + 安装器 7/7。

**交付**：部署包重出为 **`adapters/coze/ct-advisor_coze_v1.15_20260910.zip`**（累积包，取代 v1.14；
v1.14 移入 `_archive/`）。本地改动**即时生效**；云端需上传 zip + 重建镜像。

**云端验证（2026-09-10 部署 v1.15 后，端到端 3/3 通过）**：

| 问句 | 期望 | 实测 |
|:--|:--|:--|
| `A confirmatory Phase III trial plans one interim analysis — how do I keep the overall type I error rate at 0.05?` | 原生作答、末尾无软建议 | 中文方法论答案，无 💡 行、无 `need_tool` ✓ |
| `查 XX 药的安全性信号有哪些` | 自身作答 + 末尾建议 `ct-safety` | 三层检索框架 + 末尾 💡 `ct-safety`（非阻断）✓ |
| `什么是 FAERS 信号`（护栏 + 具名数据源） | 保留 `ct-safety` 建议 | 定义 + 不均衡性说明，末尾保留 ✓ |

判定依据为**包裹内真实输出**（非 HTTP 码）。遗留观察：英文问句云端仍返回中文正文，交付前**语言对齐**（只翻语言、不动数字/结构/专有名词）不可省 —— SKILL.md 规则 6。

**版本**：v0.9.118 → **v0.9.119**。

### 第十六轮：按 v1.15 线上实测重写 README 案例回答（2026-09-10）

**触发**：彤 —— 「根据现在的结果，重新修改 readme 中的案例回答」（v1.15 已完成云端部署）。

**依据**：当次端到端实测（`refine_answer.py --ship` 直连 `ct-advisor.coze.site/run`，判定取**包裹内真实输出**，不看 HTTP 码）。

**新增案例**（两份 README 各一条，编号 10 / Example 10）—— 首次把「**soft suggestion**」尾巴写进对外案例：

| 问句 | 实测尾巴 | 要点 |
|:--|:--|:--|
| `A confirmatory Phase III trial plans one interim analysis — how do I keep the overall type I error rate at 0.05?` | **无任何建议** | 纯方法学题由本技能内部作答；告别裸词 `trial` 的旧误报 |
| `查 XX 药的安全性信号有哪些` | 一行 `ct-safety` 建议 | 自身作答在前、建议在末尾；**不阻断、不索参、不强制安装** |

**文件**：`README.md` / `README_zh-CN.md` —— 案例区新增示例 10 + 对照块，引导句「9 → **10 examples**」并说明示例 10 的看点（两种尾巴的对照）。

**工程纪律**：两份 README 均为 **CRLF**，改动走 `str`-only 补丁脚本（**不混用 bytes anchor + str replacement**，见 ERR-20260910-001），改后校验 CRLF 保持、零 mojibake、案例编号无残留引用。

**如实标注**：英文问句云端仍返回**中文正文** → 案例注记写明「按问题语言对齐渲染」，不掩盖该事实。

**同日二次清理（彤：「下面这种一律不需要」）**：删除两份 README **案例区**中全部「实测输出 + 字数」注行
**共 8 处**（英文 4 / 中文 4）—— 即 `> Note: **measured output** from the 2026-09-10 run (383 characters / 313 CJK …)`
与 `> 💡 注：本答案为 2026-09-10 **实测输出**（383 字 / 313 汉字，落在 middle 档…）…` 这一类。
对外案例只保留**案例本身 + `📌 内部机制` 一行**。

- 匹配口径：引用块行（`>` 开头）且含 `measured output` / `实测输出`。注意**英文示例 1 / 2 的注不带 💡**，
  只按 💡 匹配会漏删（首轮实测确实漏了 2 行，第二轮补删）。
- **未动**：FAQ 与正文中描述产品行为的「实测」措辞（如「实测为分节标签」「实测单轮 3–72 秒」），
  性质不同，属产品事实陈述而非案例附注。

**版本**：v0.9.119 → **v0.9.120**。

### 第十七轮：删除示例 7「切换输出语言」+ 编号顺延（2026-09-10）

**触发**：彤 —— 「示例7删除」。

**改动**（`README.md` / `README_zh-CN.md` **两份同步**）：

| 动作 | 内容 |
|:--|:--|
| 删除 | 原示例 7「切换输出语言 / Switch the output language」（连同其后的 `---` 分隔行） |
| 顺延 | 原 **8**「已发表安全性证据核查」→ **7**；原 **9**「方案证据基础 + 样本量协同」→ **8**；原 **10**「只沾边兄弟技能的方法学题」→ **9** |
| 引导句 | 计数 **10 → 9**；多轮案例编号 **(4 / 5 / 8 / 9) → (4 / 5 / 7 / 8)**；尾巴对照例 **10 → 9** |

- 删除区间取「原 7 标题 → 原 8 标题之前」整块；写入前断言**块首为原 7 标题、块末非空行为 `---`**，删后交界为「📌 → 空行 → 下一示例标题」，与其余示例间隔风格一致（不残留孤立分隔线或连续空行）。
- **能力未消失**：语言切换仍在 FAQ 有说明（「中文系统下输出是中文吗？…随时一句话强制切换」），本轮删的只是一个展示案例。
- 工程纪律同前：CRLF-only 文件走 `str`-only 补丁脚本（见 ERR-20260910-001），改前备份 `%TEMP%\README*.bak3_20260910`。

**校验**：两文件编号 **1–9 连续**、CRLF-only（英文 366 / 中文 406 行）、零 mojibake、无旧计数与旧多轮编号引用残留。

**版本**：v0.9.120 → **v0.9.121**。

### 第十八轮：删除示例 9（末例）（2026-09-10）

**触发**：彤 —— 「示例9删除」。

**改动**（`README.md` / `README_zh-CN.md` **两份同步**）：

| 动作 | 内容 |
|:--|:--|
| 删除 | 现示例 9「只沾边兄弟技能的方法学题 / A methodology question that only *touches* a sibling skill」（第十六轮按 v1.15 实测新增的末例，含其后的 `---` 分隔行） |
| 引导句 | 计数 **9 → 8**；多轮案例编号 **(4 / 5 / 7 / 8) → (4 / 5 / 7)**；「两种尾巴对照」引导语**整句移除** |

- 末例删除 → 编号 **1–8 天然连续**，无需重排。
- 删除区间取「示例 9 标题 → 下一个 `## ` 章标题之前」；写入前断言**块首为示例 9 标题、块末非空行为 `---`、块尾与下一章之间恰为空行**，删后交界为「📌 → 空行 → `## 2.` 章标题」。
- **机制说明未受影响**：软建议行为在 §2「调用门槛（收紧）」与 §4「安全预览（关联明确才自动调用，其余先作答、末尾建议）」两处仍有完整用户可见说明 —— 删的只是一个展示案例，不是能力本身。
- 工程纪律同前：CRLF-only 文件走 `str`-only 补丁脚本（见 ERR-20260910-001），改前备份 `%TEMP%\README*.bak4_20260910`。

**校验**：两文件编号 **1–8 连续**、CRLF-only（英文 327 / 中文 363 行）、零 mojibake、无旧计数与旧多轮编号引用残留。

**版本**：v0.9.121 → **v0.9.122**。

## v0.9.111 前序 (2026-09-09) — 图形化解释策略 (SKILL.md) + README 案例对齐 + ct-bugreport 凭据修复

> 版本标注归位（2026-09-15，§16.8 CHANGELOG 闸门）：本条原标 `[Unreleased]`，但其内容随 v0.9.110 之后
> 的发布批次上线（早于 v0.9.111），故按时间序改为「前序」标注，不再使用 `[Unreleased]` 字样。

### SkillHub 发布 v0.9.110（2026-09-09，彤 授权）
- **平台**：SkillHub（skillhub.cn），`skillId=137567`，namespace `user_ff7413f5`。
- **版本**：0.9.110（覆盖线上旧 0.9.103）。
- **发布包构成**：`git archive` 副本（自动排除 `adapters/coze/` 大目录 + `**/refiner_contract.md` 接口文档 + `references/ops.md`），`scrub_copy.py --platform skillhub` 擦除 `.gitignore/.clawhubignore/LICENSE/workbench/*.css|js` 后 `RESULT: PASS`；`localize_frontmatter.py` 将 `displayName` 本地化为 `临床试验总顾问 (ct-advisor)`、`description` 去英文段（仅 SkillHub 副本，源目录 frontmatter 保持双语不变）。
- **本次增量**：缓存 TTL=6 个月（命中即查、过期强制重生成、存量无时间戳视同过期）；`message` 字段兼容性澄清（未赋值→不出参属正常）；本地镜像同步 Coze v2（4 cfg，doubao-seed-*-260215）；新增 `references/coze_cache_policy.md` + SKILL.md 规则 7；ct-base `coze_io_contract.md §5.5 / §20.15.8` 沉淀 message 兼容性契约。
- **状态**：`✓ Published`（服务端异步审核/索引刷新，搜索可能短暂滞后显示旧 0.9.103，非失败）。未同步 GitHub（仅发 SkillHub，红线：GitHub push / ClawHub 需分别授权）。

### 凭据集中收敛：删除 config/coze_token.py，bugreport token 迁入 coze_token_embedded.py（2026-09-09）
- **问题**：`ct-bugreport.coze.site/run` 此前返回 **403 Authentication failed**。根因：`config/coze_token.py::COZE_TOKEN` 装的是错误 token，且 `config/__pycache__/coze_token.cpython-313.pyc` 缓存残留旧错误 JWT，`bug_report.py`/`main.py` 经 `importlib` 加载时命中字节码缓存 → 实际读到旧错误 token。
- **修复（参考 ct-base §20.3.5 + `adapters/coze/src/endpoint_token.py`）**：将 bugreport 公共凭据以 XOR+base64 混淆 blob 迁入 `adapters/coze_token_embedded.py::EMBEDDED_SECRETS["ct_bugreport_coze"]`（复用同文件 `OBFUSCATION_KEY`，与 ct-base `endpoint_token.py` 同源同值），新增 `get_bugreport_token()`；重写 FILE ROLE 横幅说明本文件即全部 Coze 连接凭据唯一存放处。
- **进一步（彤 规范）**：连接 key 一律放入 `adapters/coze_token_embedded.py`，`config/coze_token.py` **不应保留**；workbench 前端「Bearer Token」是**用户私有 LLM key**（前端直连大模型时用），属私有凭据、**绝不随技能发布**——此前 `/api/config` 把 `config/coze_token.py` 里的 bugreport 项目凭据误下发到前端，属错误暴露。故**删除 `config/coze_token.py` 及 `config/__pycache__/coze_token*.pyc`**。
- **动作**：
  - `adapters/bug_report.py::_load_bugreport_token()` 改为加载 `adapters/coze_token_embedded.py` 并调用 `get_bugreport_token()`（异常回退空串）。
  - `adapters/coze/src/main.py::/api/config` 不再注入任何项目 Coze 凭据：返回 `token: ""`（可选经 `CT_WORKBENCH_LLM_KEY` 环境变量注入用户私有 key）；更新 docstring 说明前端 token 为用户私有 LLM key。
  - 清理引用：`workbench/workbench.config.json` `tokenFile` → `adapters/coze_token_embedded.py`；`workbench/index.html` 设置框标签由「Bearer Token（公开凭据）」改为「Bearer Token（私有 LLM key）」并改提示文案、更新两处注释；`adapters/bug_report.py` `send_to_endpoint` docstring 更正凭据来源。
- **验证**：经 `bug_report.py::send_to_endpoint()` 默认 loader（现读取 `adapters/coze_token_embedded.py::get_bugreport_token()`）真发 → **200 / report recorded (feishu)**；ct-advisor 计算端点（`coze_token_embedded.py` 未动）维持 **200**。两端点全绿。

### §20.15 Coze message 字段：置顶提示 + 用户可关闭（2026-09-09，对齐 ct-base §20.15 / coze_io_contract §5）
- **背景**：ct-base 新增规范——Coze 可在响应信封顶层多返回可选 `message` 字段；本地技能找到后**优先显示在给用户输出最前面**作为提示，且用户可用提示词要求关闭。此前 ct-advisor 完全未实现（`_call_coze` 解析响应时不取 `message`，`refine_answer.py` 也无置顶/关闭逻辑）。
- **Refiner（`adapters/refiner.py`）**：
  - `RefineResult` 新增 `message: Optional[dict]` 字段；
  - 新增 `_normalize_coze_message(raw)`：按 ct-base §5 契约归一化——`{level,text,dismissible}` / 裸字符串 / 多条合并；`level∈{tip,info,notice,warning}`（默认 notice，仅样式）；缺失/空/解析失败返回 None（向后兼容，不渲染）；
  - `_call_coze` 解析响应时 `result.message = _normalize_coze_message(data.get("message"))`。
  - `_call_coze` 答案解析**兼容新旧版信封**：新版工作流返回顶层 `final_answer`（优先），老版本返回 `answer`（兜底），任一命中即采用，都缺失才回退本地草稿（实测老信封样例 `{"answer":...,"message":...}` 与新版同款处理）。
- **渲染（`scripts/refine_answer.py`）**：
  - 新增 `_is_message_dismissed(q)`（中文「关闭提示/不显示提示/隐藏提示…」、英文 `no notice`/`hide message`/`disable tips`… 关键词本轮回退；仅抑显示、关闭意图不回传 coze、不误伤正常提问）；
  - 新增 `_format_message_banner(msg, lang)`（按 level 选前缀 emoji+标签，dismissible 时附「回复『关闭提示』可隐藏」提示）；
  - 主链路 `merged` 输出前：若 `result.message` 且未被关闭，则 Prepend banner 到答案最前（`banner\n\n---\n\n{merged}`）；
  - `--forward` 结构化 JSON 输出新增 `message` 字段，供消费端（如工作台）置顶渲染。
- **边界**：`message` 仅承载表面提示，不放关键结论/数值/溯源（那些走 `notes`/`warnings`）；与 §20.9 机器信号（契约漂移/端点回退）职责分离、可堆叠。

### Coze 镜像缓存质量闸：仅 accuracy=good 入缓存 + 读闸自愈（2026-09-09，彤 规范，镜像侧待部署）
- **背景**：后台真实提问「拉一下司美格鲁肽在 2 型糖尿病的注册试验，2021–2026」实跑命中陈旧低质缓存（"未收录，建议去 CDE/CT.gov 官网自行查询"），`need_tool=None`（图 cache_hit→END 先于 tool_router 短路），本应触发 ct-registry（tool_router 规则表「注册试验」+ 本地 route_tool.predict 均命中 ct-registry / cond=司美格鲁肽）。
- **写路径质量闸（根治）**：`cache_manager.py::set_cache_answer` 新增 `accuracy` 参数并**仅放行 `accuracy=="good"`**（normal/poor/未标注一律跳过，返回 False）——从源头杜绝低质/敷衍答案入库；`full_analysis_node`（自评 accuracy）与 `review_node`（取 query_meta 标注，默认 normal→默认不入缓存）两写点显式传参。单一强制点，未来新增写点自动继承。
- **读路径自愈闸（存量闭环）**：`cache_check_node` 命中后若文本命中极窄"敷衍非答案"特征（未收录/建议通过以下官方路径/请自行检索/这个我也不知道/not in the knowledge base 等）→ 视为未命中，走正常重生成（触发 tool_router→need_tool=ct-registry）。
- **验证**：`py_compile` 4 文件 OK；质量闸单测 normal/poor/NORMAL/空/None 全拦截。
- ⚠️ 属 Coze 端改动，**镜像侧已改、线上未部署**（红线：双侧同步待授权）。

### 缓存答案透明性：来源声明 + 质疑强制重生成（2026-09-09，彤 规范）
- **需求**：① 缓存答案须明确声明「来自云计算缓存」；② 用户明确质疑答案正确性 → 强制重新生成。
- **缓存来源声明（本地渲染层）**：
  - `scripts/refine_answer.py` 主链路：`result.cache_hit=True` 时在答案最前加 `> 📦 本答案来自云计算缓存（历史运行结果，非本次实时计算）…`（中英随提问语言）；
  - `workbench/index.html` `bubble()`：`meta.cached` 时在答案上方渲染同款金色声明条；`--forward` JSON 本就带 `cache_hit` 机器字段供消费端自渲染。
- **质疑强制重生成（Coze 图内，纯规则确定性）**：`graphs/nodes/cache_check_node.py` 新增 `_CHALLENGE_HINTS` + `_looks_like_challenge`——检测 `original_question` + 最近 3 条对话历史（质疑通常针对上一轮答案），命中即返回 cache_hit=False（缓存不服务质疑轮，走正常重生成 → review/full_analysis → tool_router）。中文：对吗/正确吗/确定吗/有误/错了吧/质疑/请复核/重新生成/重算…；英文：are you sure/is this correct/verify/double-check/recalculate/wrong/incorrect…
- **验证**：`py_compile`（cache_check_node / refine_answer）OK；challenge 匹配自检 10 例全过（7 命中质疑 / 3 正常提问不误伤）；工作台 JS 语法 OK。
- ⚠️ cache_check_node 属 Coze 端改动，**镜像侧已改、线上未部署**（红线：双侧同步待授权）；refine_answer / index.html 为本地改动。

### Coze 镜像：GraphOutput 预置 message 字段（§20.15 出参结构件，2026-09-09，彤 授权）
- **背景**：coze 图经 `output_schema=GraphOutput` 过滤出参——不声明 `message`，即使节点写入 state.message 也会在 ainvoke 出参边界被丢弃，本地 §20.15 渲染层永远收不到（实测 /run 顶层仅 final_answer/cache_hit/cached_answer/run_id 佐证）。
- **改动（`graphs/state.py`）**：`GlobalState`（state 通道）与 `GraphOutput`（出参契约）各新增 `message: Optional[Any] = None`；形态放宽 Any（{level,text,dismissible} 或裸字符串，ct-base §5），避免裸字符串被 pydantic 拒绝。
- **兼容**：缺省 None → 老本地/无提示场景不返回提示（§20.11 向后兼容）；老入参不带 message 不受影响（extra=ignore）；当前无节点写入 message，纯结构预置、不改变现有出参内容。
- **验证**：`py_compile` OK；pydantic 单测——默认 None、dict/裸串 message 均可构造、`model_dump()` 含 message 键。
- ⚠️ Coze 端改动，**镜像侧已改、线上未部署**（红线：双侧同步待授权）。

### Coze 镜像：advisorlog 表去 draft_answer → 固定字段异步写入（2026-09-09，彤 告知表架构变更）
- **背景**：飞书 advisorlog 表 schema 移除 `draft_answer` 列。原 `async_feishu_writer.py` 每次写入前都调用 `_get_table_fields()` 动态查询表格字段并过滤（每次多一次飞书 API）；且记录含已不存在的 `draft_answer`。
- **改动（`graphs/nodes/async_feishu_writer.py`）**：
  - 删除 `_get_table_fields()`（不再动态询问表格架构）；
  - 新增固定字段清单常量 `ADVISORLOG_FIELDS`（8 列：difficulty/category/original_question/organized_problems/accuracy/final_answer/query_origin/inittime，无 draft_answer）——表 schema 再变更只改常量一处；
  - 记录构造改为按固定清单取字段（去 all_fields/table_fields 过滤分支）；
  - `draft_answer` 函数参数保留（三个调用点兼容）但不再写入记录（docstring 注明）。
- **验证**：`py_compile` OK；静态断言 ADVISORLOG_FIELDS 8 列、无 draft_answer、`_get_table_fields` 已删除。
- ⚠️ Coze 端改动，**镜像侧已改、线上未部署**（红线：双侧同步待授权）。

### Coze 镜像：缓存有效期 TTL=6 个月，命中即查、过期强制重生成（2026-09-09，彤 规范）
- **背景**：原缓存无时间过期机制（仅 LFU 容量淘汰 + 手动清库），时效敏感问题（注册试验/指南等）的 good 答案也可能因数据过时而误用。
- **改动（`graphs/nodes/cache_manager.py`）**：
  - 新增常量 `CACHE_TTL_SECONDS = 6*30*24*3600`（6 个月 ≈180 天；0=关闭）；
  - schema 加 `created_at REAL`（建表 + 存量在线 ALTER 补列，与 history_fp 同模式）；
  - `set_cache_answer` 写入 `created_at=now`；**ON CONFLICT 更新不覆盖 created_at**——TTL 自首次生成起算，刷新不续期；
  - 读路径（`get_cached_answer` / `find_cache_match` Tier1+Tier2）**每次命中检查有效期**：过期 → 删除该条并视为未命中（强制重生成自愈）；存量无 `created_at` 条目视同过期（无法证明新鲜）；
  - 新增 `_delete_key` / `_is_entry_expired` / `_expire_and_purge`。
- **验证**：`py_compile` OK；内存后端 TTL 单测 7 项全过（新鲜命中 / 过期→None+删除 / 无时间戳视同过期 / Tier1 过期 miss / 常量 180 天）。
- ⚠️ Coze 端改动，**镜像侧已改、线上未部署**（红线：双侧同步待授权）。

### 文档校正：coze_cache_policy.md 对齐 v2 配置现状（2026-09-09，彤 要求）
- 本地镜像已同步 Coze 端 v2 代码包（`ct-advisor_coze_project_latest_v2.tar_ea00666b.gz`）；`references/coze_cache_policy.md` 同步更正：
  - 顶部注记：模型描述由"切到 `glm-4-7-251222`"更正为 v2 真相——`config/` 下 **4 个** `*_cfg.json`（full_analysis / generate_organized_problems / judge_difficulty / review），模型名均为 `doubao-seed-*-260215`（线上实测可跑）；**`cache_check` 节点已无独立 cfg**（v2 移除 `cache_check_cfg.json`）。
  - §9 速查表新增"模型配置（v2）"行，明确 4 个 cfg 清单 + cache_check 无独立配置 + 改模型只动这 4 个文件；部署包行注明镜像已同步 v2。
- 注：此前总结误记"§9 写有 5 处 config/cache_check_cfg"——实际旧文档该处仅顶部注记含模型名偏差，已一并修正。

### message 字段兼容性澄清（2026-09-09，彤 确认）
- **结论**：`message`（§20.15 表面提示）当前**全图无任何节点赋值** → LangGraph 将未赋值通道从最终 JSON 出参中丢弃 → 实际响应**不含 `message` 键**；这是预期且正常的行为（未赋值即不应出参），非 bug。
- **兼容性已就位（无需改代码）**：
  - `adapters/refiner.py`：`data.get("message")` 取字段 + `_normalize_coze_message` 对 `None/str/list/dict/数字/布尔` 全部安全降级（无效值→None）；
  - `scripts/refine_answer.py:600`：`getattr(result,"message",None)` + 真值守卫，None/空 → 跳过 banner、不中断主流程；
  - 单测 10 类输入全过（含缺失/畸形/非预期类型），`message=None` 正确跳过渲染。
- 文档 `references/coze_cache_policy.md` §7 由"已预置/必出参"更正为"可选保留字段，当前不出参属正常"；顶部注记更新为"已部署（glm-4-7 + 可写 /tmp 缓存持久）"。

### 文档化：新增 references/coze_cache_policy.md + SKILL.md 规则 7（2026-09-09）
- 新建 `references/coze_cache_policy.md`：把 2026-09-09 定稿的缓存治理与信封约定集中固化——① 缓存生命周期（写闸/内容读闸/质疑闸/TTL 四闸总览）；② 写路径 accuracy=good 质量闸；③ TTL=6 个月（命中即查、过期删条并强制重生成、存量无时间戳视同过期、刷新不续期）；④ punt 内容读闸特征词；⑤ 质疑强制重生成词表；⑥ 缓存来源声明（本地渲染层、不污染缓存文本）；⑦ 响应信封兼容（final_answer 正式/answer 备用/message §20.15 预置）；⑧ advisorlog 固定字段写（ADVISORLOG_FIELDS，无 draft_answer）；⑨ 配置/维护速查表；⑩ 新老终端双向兼容。
- `SKILL.md` Knowledge Map 新增规则 7：缓存命中自动带"来自云计算缓存"声明、用户质疑自动强制重生成——**全部自动化，agent 原样透传即可**，不得手动重生成/剥离声明；策略与词表见该文件。

### scripts/i18n.py：补齐语言持久化 API（2026-09-09）
- 问题：`scripts/switch_lang.py` 依赖 `i18n.set_lang_session()` / `i18n.set_lang_permanent()`，但 `scripts/i18n.py` 从未实现这两个函数（仅实现测试用 `set_lang()`），且 `_current_lang()` 只查进程级 override、未读 session 文件与 `config.json`；导致 `switch_lang.py` 一 import 即 `ImportError`，界面语言切换完全不可用。`system_prompt.md:17` 与 `AGENTS.md:51` 的契约早已声明此两函数存在——底座实现缺失。
- 修复：`scripts/i18n.py` 新增 `set_lang_session(locale)`（写 `data/.lang_session`）/`set_lang_permanent(locale)`（写 `config.json` `language`）/`_normalize_lang_code()`，并重写 `_current_lang()` 实现解析链 `process override → session file → config.json language → OS locale`（与 `switch_lang.py` docstring 一致）。同步 ct-base 共享底座 `scripts/i18n.py`（两副本逐字节相同，保持一致）。
- 验证：无损单元测试 9 项全过（含 zh-CN→zh 归一化、session/permanent 写入与回落、进程 override 优先级）；真实 CLI `switch_lang.py en` / `--permanent` 运行成功并即时还原，零副作用。
- **规范回写 ct-base**：`docs/02-security-model.md` §5 凭据段新增「连接凭据集中存放」「workbench 前端私有 LLM key 另行储存」两条（全库统一），并修正两处过期文件名 `adapters/coze_token.py` → `adapters/coze_token_embedded.py`；ct-base CHANGELOG 同步。
- **验证**：`py_compile` 三文件全过；`get_bugreport_token()` 与 `bug_report._load_bugreport_token()` 均返回 739 字符且与 ct-base 公共凭据逐字节同值；全目录 `.py` 无残留 `config/coze_token.py` 实际加载引用（仅说明性注释）。

### SKILL.md
- 新增 `Graphical explanation policy (answer visualization, 2026-09-09)` 节：A 层正式交付物（方案正文/审评/监管文件/计算书）默认不加图形，仅可做"独立附页"且须先问用户；B 层理解辅助（决策/流程/结构/对比/严重度）欢迎图形化；决策流 + 询问触发条件 + 低压力话术 + pipe 安全约束（图形只放 `<<<CT_ANSWER_START/END>>>` 之外）。

### README_zh-CN.md / README.md（双语同步）
- 示例计数修正：intro "6" → "8"。
- 方案评审/写作声明 ct-protocol 边界：Coze 侧仅基础版评审（逐条+严重度+建议）；深度多角色评审须显式 `@skill:ct-protocol`（示例5 选项1、示例8 说明、场景索引①、新增 FAQ）。
- 新增「图形化呈现约定」节（§4）与 FAQ：正式交付物保持纯文本，数据/解释类可视化以独立附页提供且需确认。
- 新增 FAQ：荟萃分析仅转介（须显式 `@skill:meta-analysis`，不自动触发）；改写类一次性、跨会话个性化语气记忆 DEFERRED。
- 附件清单补全 ppt（docx/pdf/ppt）。

---

## v0.9.110 (2026-09-04) — 同步 Coze 端修复（模型更换 + received_at 字段）+ 结构扁平化

### 同步 Coze 端修复

| 修复 | 文件 | 内容 |
|---|---|---|
| 模型停运 | `config/generate_organized_problems_cfg.json` | `doubao-seed-2-0-lite-260215` → `doubao-seed-2-0-mini-260215` |
| 缺少 received_at | `src/graphs/state.py` | `FullAnalysisInput` 添加 `received_at: Optional[float]` |
| 缺少 received_at | `src/graphs/state.py` | `CacheCheckInput` 添加 `received_at: Optional[float]` |
| 缺少 received_at | `src/graphs/nodes/review_node.py` | `ReviewInput` 添加 `received_at: Optional[float]`（同时补 `from typing import Optional`） |

### 结构扁平化

- `adapters/coze/project_20260812_152011/projects/` → `adapters/coze/`（移除两层多余嵌套，对齐 ct-base）
- 新打包：`ct-advisor_coze_v1.9_20260904.zip`（8.39 MB）
- `scripts/build_knowledge_index.py` 默认知识目录路径修正
- `coze_modification_guide.md` 基准路径更新

---

## v0.9.109 (2026-09-04) — Coze system prompt v1.7（引文触发 + 评审清单 + 收口标记）+ ct-safety 触发词扩展 + ICI 安全性知识模块

### 结构扁平化

- **改动**：`adapters/coze/project_20260812_152011/projects/` → `adapters/coze/`（移除两层多余嵌套）
- **新打包**：`ct-advisor_coze_v1.8_20260904.zip`（8.39 MB）
- **对齐 ct-base**：与 ct-base `adapters/coze/` 同级结构一致（assets/config/knowledge/scripts/src 平铺）
- **路径修正**：`scripts/build_knowledge_index.py` 默认知识目录改为 `../../knowledge`（原 `../../project_20260812_152011/projects/knowledge`）
- **文档更新**：`coze_modification_guide.md` 基准路径更新为 `adapters/coze/`

---

## v0.9.108 (2026-09-04) — Coze system prompt v1.6（超长Q结构化引导 + 场景规则）+ ct-safety 触发词扩展 + ICI 安全性知识模块

### Coze System Prompt v1.6（`adapters/coze/project_20260812_152011/projects/assets/coze_system_prompt_v1.4.md`）

- **版本号**：v1.5 → v1.6（long-Q + 场景规则 版本）
- **背景**：分析 CTDB_advisorlog.xlsx 中 9 个 original_question > 100 字的长问题（全部 complex，平均回答 2665 字），诊断出五类结构性问题：铺垫过多、数据幻觉、窄问宽答、模板复述、事实/推断混排。

#### 新增规则

| 编号 | 规则 | 适用场景 | 优先级 |
|---|---|---|---|
| 0a | **超长问题结构化引导**：保留全文不删减，在全文前附加「用户问题清单」和「关键参数表」，按问题清单逐点回答 | Q > 5000 字（如 TGFR 方案评审） | P0 |
| 10 | **成本/财务/市场数据禁幻觉**：必须标注假设条件；无来源不写精确值；无法估算写"需用户提供" | 成本测算、市场数据 | P0 |
| 11 | **窄问窄答**：直接回答主题，不前置通用框架；问"哪些"→列表，问"如何"→步骤 | 窄问题（如 RBM 措施） | P1 |
| 12 | **模板规范不复述**：只写"撰写要求/填写规范"，模板原有内容直接引用不重抄 | 模板→规范类 | P1 |
| 13 | **事实推断分离**：事实与推断分列，事实标注来源，推断明确标注，市场数据只给范围 | 行业研究/市场分析 | P2 |

#### 输出前自检新增项

- 通用：`数据有来源?→无则改定性` | `窄问无通用框架?→删` | `模板不复述?→删` | `事实推断分离?→分列`
- Complex：`逐点覆盖问题清单?→补漏`

#### 编号调整

- 原 Simple 10-12 → 14-16，Middle 13-15 → 17-19，Complex 16-20 → 20-24（顺延）

---

### ct-safety 触发词扩展

- **Coze 端**：`tool_router_node.py` 在 ct-safety 规则中新增 `irAE`、`免疫相关`、`因果关系`、`不良反应`、`带状疱疹`、`herpes`、`vzv` 等触发词
- **本地端**：`scripts/route_tool.py` 同步扩展
- **效果**：PD-1/VEGF 双抗+带状疱疹等含"不良反应/irAE/因果关系判定"关键词的临床问题可正确触发 ct-safety 工具

---

### ICI 安全性知识模块（`knowledge/ref-icae-safety.md`，新建）

- **覆盖内容**：ICI irAE 谱（PD-1/PD-L1/CTLA-4/双抗对比）、VZV/HSV 再激活机制与流行病学、间质性肺炎/心肌炎/肝炎/肾炎/甲状腺炎/垂体炎 irAE 速查、PD-1/VEGF 双抗 vs PD-1 单抗安全性对比、ICI 因果关系判定要点
- **来源标注**：NCCN、ASCO、JAMA Oncol、各产品说明书；发生率数据为文献范围值（非精确），引用时核对原始来源
- **配套更新**：`knowledge/reference-index.md` 新增索引条目

---

## v0.9.107 (2026-09-03) — 接口闭环（F1–F5 / test_seven_flows 漂移修复）+ 对齐 ct-base coze_io_contract §1/§2

- **背景**：按 ct-base `references/coze_io_contract.md` 统一契约，对所有 coze 调用强制补齐入参信封与飞书日志字段（与 ct-safety / ct-registry 同标准）。用户确认「coze 调用不分计算/检索端点，一律遵守」「飞书 searchlog 肯定存在」。
- **§1.2 `skill_version`（顶层信封，与 query_origin 同级）**：`adapters/refiner.py` 新增 `_skill_version()`（读 `SKILL.md` `version:`，失败回退 `"0.9.104"`），`RefineRequest.to_payload()` 在出站前把 `skill_version` 注入 `query_meta`（**与 `query_origin` 同级**——ct-advisor 的 `query_origin` 嵌套在 `query_meta` 内，故 `skill_version` 同位置，符合「与 query_origin 同级」字面要求；coze 服务端从 `query_meta` 读取）。
- **§1.1 `user_language`（备用语言提示，进 params）**：`to_payload()` 注入顶层 `params: {"user_language": resolve_user_language(original_question)}`，按用户输入文本做 zh/en 内容级判定（复用 `scripts/i18n.py`）；coze 端可忽略（备用提示）。
- **§2.1 `skill_version` → 飞书（特殊落点：并入 `final_answer` 列，不新增独立列）**：coze 服务端参考代码 `adapters/coze/project_20260812_152011/projects/src/graphs/nodes/async_feishu_writer.py` 从 `query_meta` 读 `skill_version`，与 §2.2 的 `runtime_sec` 一起并入既有 `final_answer` 列（见下「ct-advisor 专用落点」）。
- **§2.2 `runtime_sec` → 飞书（计算持续秒数，只进飞书、不出参）**：`main.py` 的 `/run` 与 `/stream_run` 入口收到 `request.json()` 即刻打 `payload["received_at"]`；`state.py` 的 `GlobalState` / `GraphInput` 新增 optional `received_at`；三处 `async_feishu_write` 调用（review / full_analysis / cache_check）透传 `received_at=state.received_at`；writer 内 `runtime_sec = round(time.time()-received_at, 3)` 与 `skill_version` 合并进 `final_answer` 列 JSON 对象 `{"answer": 原始 final_answer, "skill_version": ..., "runtime_sec": ...}`（见下），仅非空才包裹。`GraphOutput` 不出 `runtime_sec`（§2.2 红线不动）。
- **⚠️ ct-advisor 飞书落点（已决，用户 2026-09-03）**：ct-advisor 飞书表（`Pog0bGNMbaCWMIsGRNpckHcnn9f` / `tblA2mEaE7TJtI0u`）为描述性列（无统一 searchlog 的 `querystr`/`resultstr` 列）。用户明确：§2.1/§2.2 **不新增独立列**，直接并入既有 `final_answer` 列，与原始写入值组成 JSON 对象 `{"answer": 原始 final_answer, "skill_version": ..., "runtime_sec": ...}`（仅当契约元数据非空才包裹，向后兼容：无 `skill_version` 且无 `received_at` 时 `final_answer` 仍存原始文本）。故 writer 已移除 `skill_version`/`runtime_sec` 独立列写入，仅 `final_answer` 列承载二者。
- **⚠️ 待用户处理（部署）**：`adapters/coze/project_20260812_152011/` 是 coze 工作流部署源，以上 §2.1/§2.2 改动需**重新打包上传 Coze 控制台部署**才在线上生效（ct-advisor 既有「本地基准，待重新部署生效」惯例）。
- **验证**：客户端 `py_compile` + 行为测试（中文→`zh`/英文→`en`/`skill_version=0.9.104` 进 `query_meta`/幂等）；服务端 6 文件 `py_compile` + 飞书 writer 逻辑单测（有元数据时 `final_answer` 列为 `{"answer":"原始答案","skill_version":"0.9.104","runtime_sec":~1.237}` 的 JSON 对象、独立 `skill_version`/`runtime_sec` 列消失、写库键仅含真实表列；无元数据时 `final_answer` 保持原始文本、历史格式逐字节一致）。

- **背景（test_seven_flows.py 契约漂移修复）**：v0.9.106 修完 F3/F4/F5 后跑 `test_seven_flows.py` 仍崩——根因不在本次改动，而在 coze 节点 `tool_router_node._match_tool` 自 2026-08-23 起把返回从「首个命中即返回」改为「收集全部命中 + 按 `TOOL_PRIORITY` 选主判」，返回结构由 2 元组变 **3 元组** `(主判技能, 默认参数, 全部命中列表)`；测试脚本 `coze_tool, coze_defaults = coze_match(q) or (None, {})` 仍按旧 2 元组解包，命中即抛 `too many values to unpack`，整测试在首个流程就崩、后续 6 个流程从未执行（崩溃掩盖了 F4 的预期漂移）。按规矩**不碰 coze 部署源**（`adapters/coze/` 由用户人工打包部署），只在 ct-advisor 自己的测试脚本内对齐真实契约。
- **修复 1 · 解包对齐 3 元组**：`test_seven_flows.py` 改为 `matched = coze_match(q); (coze_tool, coze_defaults, coze_hits) = matched if matched else (None, {}, [])`，并打印 `hits` 提升多源可观测性（coze 节点 2026-08-23 的 `need_tools`/`deferred_tools` 机制正是依赖第 3 元组）。
- **修复 2 · F4 预期漂移重定点（保留真实异判覆盖）**：原 F4 问「查 PD-1 抑制剂三期临床试验并算一下样本量」期望 前端=samplesize / Coze=registry → 委托 registry；但现状下该问**只命中 samplesize**（coze `TOOL_PRIORITY` 中 samplesize 最高，且 registry 触发词刻意不含「三期临床试验」以防模板误触发），故 Coze 与前端同判 samplesize、编排器正确包裹——原期望在结构上已不可能成立。重定点为「前端=registry（经『三期』） / Coze=literature（该问只命中文献）→ 委托 literature」，仍为 **真实前端≠真实 Coze** 的异判场景，验证 orchestrator 把已执行的 registry 预判并入草稿、委托 Coze 主判 literature（与 `orchestrate.py` SELF_TEST 的 mock 异判互补，覆盖真实代码链路）。
- **非回归**：coze 节点 `_match_tool` 是只读引用（未改），编排器 `build_output` 的「`coze_tool != prefetch_tool` → 委托」路径本就正确（mock SELF_TEST 8/8 通过），本次仅修测试脚本的过时假设。
- **附带修复 · 契约测试解释器对齐环境规则（v0.9.107 同批）**：验证 #1 时发现 `test_sibling_contract.py` 在本沙箱掉到 2/4——根因是测试用 `cfg["cmd"]="python"` 解析到 managed 3.13.12 解释器，而 ct-safety / ct-literature 在模块顶层 `import xlsxwriter`、managed 环境未预装该包，`--help` 即 rc=1（属沙箱≠部署的环境缺口，非代码回归；Anaconda `C:\Tools\anaconda3\python.exe` 已装 xlsxwriter 3.2.9）。按用户环境规则（Python 必须用 Anaconda，不用 managed）新增 `_interpreter()`：优先 Anaconda、缺失回退运行测试的解释器；契约测试改用它对兄弟技能跑 `--help`。恢复 **4/4 = 100%**，且今后整套测试应在 Anaconda 下运行方与生产一致。
- **验证**：`python -m py_compile scripts/test_seven_flows.py` 通过；`test_seven_flows.py` 七大流程 **7/7 = 100%**（修复前崩溃 0 执行）；`route_tool.py --self-test` 22/22 + 参数 6/6；`orchestrate.py --self-test` 8/8；F4 单列确认真实异判 前端=ct-registry / Coze=('ct-literature', {'max':20}, ['ct-literature'])。

## v0.9.105 (2026-09-03) — 与兄弟技能接口两处修复（F1 referral-only / F2 margin 丢参）

- **F2 · `ct-samplesize` `--margin` 静默丢失（明确 bug，已修）**：`tool_mapping.json` 的 `effect_params` 长期列了 `margin`，但 `ct-samplesize.params` 字典从未定义 `margin` 键；`_build_cmd` 只遍历 params 键拼 flag，导致 Coze/用户传入的非劣效/等效（NI/equivalence）边际假设 `margin` **永远拼不出 `--margin`**（模型能收不能传）。新增 `"margin": {"flag": "--margin", "type": "float", "default": null, "required": false}` 到 params，与 `samplesize_power.py` 的 `--margin` 入参对齐；NI/equivalence 检验现在能正确透传边际效应量。
- **F1 · `meta-analysis` 接口不对称（降级为 referral-only，已修）**：此前 `SKILL.md` 把它标 tier-A 依赖、`AGENTS.md` 路由叙事也含它，但 `tool_mapping.json` 无条目、`route_tool.py` 无触发词——Coze 若返回 `need_tool:"meta-analysis"`，`handle_need_tool.py` 直接报硬错「未在 tool_mapping.json 中找到技能映射」，广告可路由、实际不可调（self-test 22/22 全绿且 meta-analysis 从不是目标，印证从未纳入路由）。改动：
  - `tool_mapping.json` 新增顶层 `referrals` 注册表（`meta-analysis` → `mention`/`reason`/`github`），作为 referral-only 单一数据源；
  - `handle_need_tool.py` 未映射分支：命中 referrals 时返回 `status:"referral"`（结构化 message/mention/github）而非硬错 `status:"error"`，不再卡死整条应答；`_build_deferred` 对 referral-only 技能生成清晰「请 @skill 调用」提示；
  - `refine_answer.py` `_merge_answer` 新增 `referral` 状态分支：把 Coze 原答案 + 显式调用引导一起透出（用户可见，而非当成错误）；
  - `SKILL.md`：`dependencies` 移除 meta-analysis 自动依赖（改注释说明 referral-only）、Requirements「Sibling skills」行与「Boundaries with Sibling Skills」段标注 meta-analysis 为 referral-only、引导 `@skill:meta-analysis`；
  - `orchestrate.py` 不受影响（meta-analysis 从不经 route_tool 预判，referral 经 `--ship` 路径的 `_merge_answer` 处理；其 error 兜底分支对未知状态安全降级）。
- **验证**：`python -m json.tool tool_mapping.json` 通过；`route_tool.py --self-test` 22/22 绿（meta-analysis 仍非目标，符合预期）；`handle_need_tool.py` 经 `--card '{"need_tool":"meta-analysis",...}'` 实测返回 `status:"referral"`（修复前为 `status:"error"` + 硬错文案）。
- **遗留（后续立项，不在本版）**：F3 `query_origin`/`locale` 不向兄弟技能透传；F4 缺真实兄弟技能集成测试（orchestrate/route_tool 自测全 mock 桩）；F5 coze 引擎技能（ct-samplesize v5 / meta-analysis）的 SAFE PREVIEW 语义需逐条对齐 ct-base §5。

## v0.9.106 (2026-09-03) — 兄弟技能接口一致性闭环（F3 语言透传 / F4 真实契约测试 / F5 SAFE PREVIEW 引擎对齐）

- **F3 · 调用方语言向兄弟技能透传（已修）**：新增 `handle_need_tool.detect_text_language` / `_resolve_call_locale`（与 ct-base `scripts/i18n.py` 同算法、本地自包含，避免跨技能 import）；`execute_card` 按【用户输入文本】内容级检测语言（中文系统 + 英文输入不被误判 zh），经环境变量 `CTSS_LOCALE` 注入子进程环境（兄弟技能 coze 计算端按 ct-base `language_policy.md` §"user_language 备用入参" 读此变量切报告/图表语言）。卡片若显式带 `locale` 则优先；否则回退中文默认。**端到端证明（零网络）**：`CTSS_LOCALE=en` → ct-samplesize v5 coze 信封 `user_language:"en"`，`=zh` → `"zh"`（实测 `--dry-run` 信封随变量切换）；`_resolve_call_locale` 单测 英文问→en / 中文问→zh / 显式 en→en 全过。注：`query_origin` 按 ct-base §8.6 由兄弟技能（客户端同机）自行生成 `sha256(hostname)`，归因一致，ct-advisor 不再重复透传（卡片若带 `query_origin` 仍经 `CT_QUERY_ORIGIN` 透传以备关联）。
- **F4 · 真实兄弟技能 CLI 契约测试（已修，最高 ROI 工程债）**：新增 `scripts/test_sibling_contract.py`——对 `tool_mapping.json` 每个自动执行技能真实 subprocess 跑 `<cmd> <args> --help`（argparse 解析即退出，零网络 / 零 coze），断言 ① 脚本存在且路径落在 `SKILLS_DIR` 内（防 `../` 逃逸）② rc==0 ③ 映射表声明的每个 flag（`params` / `extra_args` / `conditional_args`）都出现在兄弟 `--help` 文本里。**抓出 CLI 漂移**（兄弟改了 CLI 没同步映射表会立刻红）——正是此前 PREVIEW/KW-GATE 守卫踩坑的根因类型，过去 orchestrate/route_tool 自测 + `test_seven_flows.py` 全程 mock 桩完全侦测不到。实测 4/4 通过（ct-registry 12 / ct-safety 7 / ct-literature 7 / ct-samplesize 11 个契约 flag 全命中）。
- **F5 · SAFE PREVIEW 按引擎类型对齐 ct-base §5（已修）**：`tool_mapping.json` 为每个技能加 `engine` 字段（`ct-samplesize`=`coze`，其余三兄弟=`local`）；`ct-samplesize` 移除 `extra_args` 的 `--yes`（实证 v5 coze 后端 `requires_confirmation=False`，`--yes` 对 coze 是 no-op，且 §5 规定 coze 引擎 `--yes` 不适用——仅 legacy 本地引擎保留）；`handle_need_tool` 的两个「假成功」守卫（PREVIEW / KW-GATE）改为**引擎感知**：仅 `engine!="coze"`（本地引擎技能因缺 `--run`/`--yes` 停在交互确认门）才判假成功，coze 引擎无此闸门、请求信封由执行卡直接发送，不因 `[PREVIEW]`/`[KW-GATE]` 误判。
- **验证**：`python -m py_compile scripts/handle_need_tool.py scripts/test_sibling_contract.py` 通过；`test_sibling_contract.py` 4/4 绿；`route_tool.py --self-test` 22/22 绿；`handle_need_tool` referral 回归（`meta-analysis`→`status:"referral"`、未知技能→`status:"error"`）；`--margin` 拼参仍 OK；ct-samplesize `--dry-run` 信封 `user_language` 随 `CTSS_LOCALE` 切换。
- **未做 / 已知（v0.9.107 已修）**：`test_seven_flows.py` 原 `coze_match(q) or (None, {})` 2-unpack 报错（coze 节点 `_match_tool` 自 2026-08-23 起返回 3 元组 `(主判, 默认参数, 全部命中)`）——见 v0.9.107。

## v0.9.104 (2026-08-31) — 发布前检查整改（ct-base §16 闸门全绿）

- **§16.8 共享件一致性闸门解除（原 P0 阻断）**：以 ct-base 真源覆盖 `scripts/i18n.py`、`scripts/kw_localize.py`（纯增量，调用方无破坏）；`scripts/i18n_messages.json` 重组为 base 精确子集，ct-advisor 专属 102 键（`menu.*`/`ground.*`/`out.format.*`）迁至新增 `scripts/i18n_skill_messages.json`（消除 `publish_inject` 整体覆盖会抹掉专有条词的陷阱）；剔除 13 个 R/install 死键（`error.fallback_diagnose` 等活键保留）。重跑 `shared_sync_check` 退出码 0（剩余 2 项 WARN 为纯 Python 技能不需 `merge_spec`/`i18n_r_messages`，合法）。
- **§16.9 出站归位**：`scripts/check_coze.py` 硬编码 `ENDPOINT = "https://ct-advisor.coze.site/run"`（脚本层唯一 coze URL 副本）收口至 `adapters/http_probe.py`（`COZE_ENDPOINT`），`scripts/` 层不再持有硬编码 URL；实际网络调用本就在 `adapters/http_probe.py::probe_get`，符合 §16.9。
- **handle_need_tool.py 路径白名单（审计整改）**：建 `workdir` 前校验解析后落在 `CARDS_ROOT` 内，杜绝 `../` 逃逸；`_read_artifacts` 每次读取前校验 `hit` 仍解析在 `workdir` 之内，抵御 `result_files` 含 `../` 的路径逃逸。冒烟验证：正常工具落 `CARDS_ROOT` 内、`../EVIL.txt` 逃逸被跳过。
- **README 档位修正（§16.0 HIGH 闭环）**：中文 A 档补 `controlled-coze-opt-in` 子属性（与 `SKILL.md` frontmatter 一致，原误归类 `public-retrieval`）；英文 A 档"run fully locally"补同等说明；补"发布包内含未调用的 ct-base 共享模块"说明，澄清 `kw_localize` 在线翻译兜底在 ct-advisor 零调用、不产生实际出站，消除审计 HIGH 疑虑。
- **欠提交改动入库**：v0.9.103 的 6 个已改未提交文件（双 ignore 对齐 ct-base 基线、F07 双语顺序、§13.1 保密声明对齐、规范拆分后文档路径修正）随本次一并提交。
- **待人工验证**：§16.6 对话示例实测留痕需以 0.9.104 重跑（本机 Coze 往返），发布前补齐。

## v0.9.103 (2026-08-25) — 发布前对齐 ct-base §16 + Mode B 追问自包含化闭环（升版：SkillHub 预注册 0.9.102 占位导致需 bump）

- **发布前对齐 ct-base §16（逐项核对）**：
  - **kw_lexicon 同步修复（§16.8 共享件一致性闸门）**：从 ct-base 真源补齐 5 个缺失词典项（`佐妥昔单抗→Zolbetuximab`、`恶心呕吐→nausea/vomiting`、`恶心→nausea`、`呕吐→vomiting`、`止吐→antiemetic`），消除 `shared_sync_check` 的 drift 阻断；重跑全绿（叶子共享件与底座字节级一致）。
  - **Mode B 追问自包含化闭环（对齐 ct-base `references/continuity.md` §2）**：`scripts/context_stitch.py` 每次转发前**始终**导出有界 `conversation_history`（经 `pack_history_for_coze`）并随请求发往 Coze，相关性 / 继承由远端 LLM 判定；本地代码**不再**检测追问或改写问题（旧的 `is_followup()` 正则 + 自包含 stitch 已硬废弃）；`config/context_cache.json` 仅为 write-through 镜像（TTL 2h / ≤10 轮 + 24h 硬上限）。
  - **refiner 答案解析修正**：`refiner.py` 新增 `_purify_tilde_range`，对 `~` 区间记号（`40%~60%`）去除删除线渲染干扰，避免用户误读为「已删除内容」。
  - **超时上调**：追问类与 complex 类请求 `refiner.long_timeout` 上调至 300s（对齐 coze 实际 ~4 分钟返回），`config.json` 同步。
  - **发布前扫描结果**：`continuity_lint` COMPLIANT；`publish_secret_scan` 0 P0 / 0 P1（53 个 WARN 均为混淆公共 token 的变量 / 常量名误报，非真实密钥）；`shared_sync_check` 全一致；`clawhub_security_audit` 对当前发行版 25 findings 中 5 STILL_PRESENT 均属「架构设计如此且已在 README/SKILL 按 ct-base §5/§20.3 透明披露」（Coze 转发、代码编排器、query_origin 哈希、bug-report 端点），人工确认接受、留痕于此。
  - **删除 "zero outbound / 零出站 / 零出域" 绝对化措辞（消除 §16.0 误报根因）**：全库当前文档与代码注释（SKILL.md、`knowledge/system_prompt.md`、`references/tone_writing.md`、`references/ADVANCED.md`、`adapters/__init__.py`、`adapters/backend.py`、`scripts/clarify_loop.py`、`scripts/refine_answer.py`、`adapters/http_probe.py`）的 "zero outbound / 零出站 / 零出域" 一律改为事实性描述（"纯本地执行、不发起网络请求 / no network call"）；AGENTS.md §出站披露 治理规则同步收紧（全库禁用该绝对化表述，纯本地子模块改用事实性描述，避免暗示整个技能离线）。历史 CHANGELOG 条目保留原貌（记录当时状态，不改写历史）。
  - **[HIGH] Tp4 整改（§16.0 MCP Tool Poisoning：对外宣称过窄、低估敏感行为）**：原 README §5「数据仅在两种情况出域」框架把技能说得太"干净"，未披露 Tp4 点名的 5 类敏感行为。整改——(1) 两版 README 顶部新增「范围现实核对」横幅，开门见山说明本技能是**云端辅助而非纯本地**；(2) §5 重写为「离机 / 留本机但敏感」两段式：离机段补明兄弟 `ct-*` 技能会**独立**查询公开注册库/API（CT.gov/CDE/FAERS/OpenAlex/PubChem），且错误报告端点 `ct-bugreport.coze.site/run` 为独立出站；留本机段**首次公开披露**内嵌（公开）令牌、本地持久化（config.json 语言偏好 / `.runtime/` 上下文缓存 / 长期记忆提升）、本地连通性诊断、子进程编排四类动作；(3) **对齐 declared-purpose 措辞**：SKILL.md `summary`/`description` 由"总顾问"扩写为"云端辅助的临床试验总顾问"，显式写入"转发远程 Coze 引擎 / 本机运行兄弟技能 / 保留本地状态（语言偏好·上下文缓存·长期记忆）/ 可选脱敏错误报告"，使对外宣称与真实行为 1:1 对齐。目的：杜绝"窄顾问、实际做更多"的轻描淡写观感。重跑审计验证：run1→run2 已消解"Coze 是唯一出站路径"那条 MEDIUM 误配（证明模型读得到新披露）；Tp4 因锚定"头条定位"仍标 [HIGH]，故再以 declared-purpose 措辞对齐为第二刀。
  - **README 双语同步与机制说明清理（用户复核）**：(1) 英文版「Scope reality check」重写为与中文版「范围现实核对（请先读这段）」逐句对齐，去掉英文独有、中文版没有的「strictly offline → ct-protocol」句子，使两版口径一致；(2) 删除两版 README 示例 5 的「📌 说明（以下为机制说明，不展示给用户）」机制注释（ZH 原第 88 行 / EN 对应行）——该段为内部架构说明、不应面向用户展示，删除后两版示例区结构对称。

## v0.9.101 (2026-08-23) — F 难度偏置与延迟护栏可观测化（ct-update P1）

- **F 落地（ct-update 对标 P1：难度偏置与延迟护栏的可观测化）**：
  - `scripts/refine_answer.py` 新增可选度量开关：`--latency-report`（每次调用即一次 tool round-trip，按 `--round-id` 分组计数）、`--round-id`（默认 `default`）、`--latency-threshold`（默认 10）、`--latency-reset`（清计数器）。计数器落 `<ROOT>/.runtime/latency_<round_id>.json`（纯本地、零出域，已加入 `.gitignore`）；超阈值时 stderr 输出 `[WARN]`，提示 pre-fire 延迟复发（对应 #1 实测延迟失效模式）。
  - `references/steps.md` 新增「延迟护栏单测式检查表（F）」：L1–L6 不变量（middle 必须 fire-only 禁 pre-fire 读 knowledge / simple 必须跳过 Coze / fire 不得晚于本地读取 / complex 本地初步≤200字单次 / forward-only / vague 不得直发），供改完路由逻辑后逐条防回归断言。
- **附带加固（验证 F 时发现的既有 bug，与本项无关但对离线可观测化必要）**：`refine_answer.py` 串行兜底与 fire-only 分支在 refiner 返回 `RefineResult` 对象（而非字符串）时 `(final or "").strip()` 抛 `AttributeError` 崩溃；两处统一加 `if not isinstance(final, str): final = getattr(final, "final_answer", "") or ""` 防御，兼容两种返回形态，对生产 str 路径零影响。
- 验证：`py_compile` 通过；`--latency-report` 在 fire-only/collect/serial 三模式计数递增（q2: 1→2→3→4），阈值告警在 trips=11 触发；串行兜底不再崩（rc=0）；`.runtime/` 已 gitignore。

## v0.9.100 (2026-08-22) — 增加 bug report 功能（ct-base §20.3 接入完成）

- **发布前检查修正**：README 出站披露「three-stage confirmation」→「two-stage confirmation」（与 §20.3.3 同步，SKILL.md 已正确）。
- bugreport 接入点全绿（发布前检查无待确认项）：`adapters/bug_report.py`（内嵌公共 token + `DEFAULT_ENDPOINT` 统一端点 + 历史回执 `confirm_thanks`/`build_followup` 已就位）、SKILL.md Bug Report 段（双向触发 + 两阶段确认 + 脱敏铁律 + 历史回执）、`config.json` `auto_approve_endpoints` 已含 `https://ct-bugreport.coze.site/run`、README 出站披露均已就位。
- 三道发布闸门：publish_secret_scan（0 P0/0 P1）、shared_sync_check（无漂移）、clawhub_security_audit（仅预已发布技能的既有审计项，无新增阻断）。

## v0.9.72 (2026-08-22) — Bug Report 发送后历史回执约定（ct-base §20.3.7 同步）

- **SKILL.md Bug Report 段**：补充发送成功后回执流程——endpoint 返回 `history`（同 query_origin 上一次提交或 `""`），agent 用 `confirm_thanks(locale)` + `build_followup(history, locale)` 组织回复（双语自动切换：`history` 为空→结束；`resultstr=="done"`→展示 memo 修复详情；否则提示尚未修复）。所有用户提示 `_MSGS` 中英成对、按 `locale` 自动转换。
- 同步源：ct-base `docs/07-coze-engine.md` §20.3.7 + `adapters/bug_report.py`（confirm_thanks/build_followup/parse_history，v1.1.58）。
- 客户端落地（2026-08-22 cont.）：`adapters/bug_report.py` 副本补齐 `confirm_thanks`/`build_followup`/`parse_history` + `_MSGS` thank/done/pending 双语文案 + `send_to_endpoint` 透传 `history`（此前该副本缺这些函数，仅 SKILL.md 有回执约定）；docstring「三阶段确认」→「两阶段确认」。

## v0.9.71 (2026-08-21) — bugreport 两阶段确认简化（方案 A，ct-base §20.3.3 同步）

- **SKILL.md Bug Report 段**：Three-stage confirmation（propose → show → send）→ **Two-stage confirmation（propose-with-preview → send）**——提议时直接展示 `render_report_text` 脱敏报告全文，用户一次明确确认即发送（保留发送前内容检视与明确放行，去掉"提议→展示"间的一个来回）。
- 同步源：ct-base `docs/07-coze-engine.md` §20.3.3（三阶段→两阶段）+ `references/bug_report_endpoint.md` + `adapters/coze/coze_contract.md` + `AGENTS.md`；ct-samplesize SKILL.md/CHANGELOG 同步。
- 代码零改动：`bug_report.py` 的 `confirm_prompt`（一次性提议文案）与 `render_report_text`（全文渲染）照用，仅 agent 流程合并两步。

## v0.9.70 (2026-08-20) — 类型 B 追问自包含化 + README 示例实测闸门闭环

### bugreport 接入（ct-base §20.3，2026-08-21）
- 复制 `ct-base/adapters/bug_report.py` → `adapters/bug_report.py`，内嵌 ct-bugreport 公共凭据 blob（`EMBEDDED_SECRETS`，XOR+base64，与 ct-base 镜像同密钥同 blob），`DEFAULT_ENDPOINT` 已为统一端点 `https://ct-bugreport.coze.site/run`；新增 CLI（`--error-type/--test/--description/--send`）供 agent 调用。
- `config.json` `auto_approve_endpoints` 加入 `https://ct-bugreport.coze.site/run`（与 Coze 端点同待遇，永不弹确认）。
- SKILL.md 加 §20.3 触发规则（强信号 + 每会话 1 次；**新增「用户显式请求上报 bug」主动触发，每会话可多次**）；两份 README 出站披露补 bug-report 客户端条目；AGENTS.md 同步预置白名单。
- ct-base 同步：§5 预置白名单 + §20.3.5 声明 bug-report 端点为作者预置公共端点；§20.3.1 新增「用户主动要求报告 bug」触发条件。

### 实测留痕（2026-08-20）— §16.6 对话示例实测闸门：README ×2 共 16 示例逐一无损实测

- **触发**：按 ct-base §16.6（2026-08-20 新增，全库强制），对 `README.md`（EN 8 例）+ `README_zh-CN.md`（ZH 8 例）的每个对话示例按"你这样说"真实触发技能并留痕。触发方式：`route.py`（难度判定）/ `clarify_loop.py --payload-inline`（vague 澄清）/ `refine_answer.py --ship`（Coze 转发）/ `orchestrate.py`（本地编排器：Coze 直发 + route_tool 预判并行）。
- **实测矩阵（EN/ZH 同文，各 8 例）**：

| 示例 | README 声称 | 实测结果 | 判定 |
|---|---|---|---|
| Ex1 方法学 estimand | 转发 Coze 直接答 | `--ship` 返回完整 ICH E9(R1) 五要素答案（checksum cfee1b4d） | ✅ 通过 |
| Ex2 窄数据（注册试验） | 本地编排器自动分派 ct-registry，实时 landscape | Coze 回"知识库未收录+建议自行用 ct-registry"；route_tool 预判 `null`；**无任何检索发生** | ❌ P1 核心卖点失效 |
| Ex3 竞品情报三源 | 编排器自动分派 registry+safety+literature 拼接，无需确认 | Coze 知识综述五部分质量高；但委托块 `missing_params=[cond]` 追问后才执行，预判仅识别 registry 单源 | ⚠️ P2 部分 |
| Ex4 多部分设计+样本量 | 编排器并行 samplesize + Coze | Coze 完整五部分设计答复 + 委托追问 test/效应量参数（缺参合理） | ✅ 通过 |
| Ex5 vague 澄清 | route.py 判 vague → clarify_loop 追问"角色/阶段/材料" | route.py 判 `complex`（不进入澄清）；强入后 ZH 追问 PICO 维度（人群/结局），EN 直接 `decidable` | ❌ P0 README 与实现脱节 |
| Ex6 语言切换 | 一句话切换 | `--ship` 中/英文确认回复均正常 | ✅ 通过 |
| Ex7 PD-1 文献证据 | route to ct-literature --safety，带 DOI/PMID 引文 | Coze 知识综述（类效应五部分+证据摘要）质量高；预判判为 `ct-safety`（非文献检索）；**无 DOI/PMID 引文** | ❌ P1 路由错误+无引文 |
| Ex8 证据+样本量 | ct-literature + ct-samplesize 两段交接 | Coze 正确识别双技能并追问缺参（合理降级）；预判仅委托 samplesize | ⚠️ P2 部分 |

- **CLI 示例**：`check_deps.py` ✅ / `menu.py --all` ✅ / `menu.py --tier data_skill --human --lang zh` ⚠️（--lang zh 输出 i18n key `menu.ct_registry` 而非中文）。
- **已确认根因**：① route.py vague 语义规则未命中"我不确定要什么"（被 complex 覆盖）；② clarify_loop.py 追问维度为 PICO（与 README「角色/阶段/材料」脱节）；③ route_tool.py + Coze tool_router_node.py 触发词缺"注册试验/登记试验"模式（2026-08-15 修误触发删裸词后未补精确复合词）；④ route_tool.py safety/literature 区分不足（"检索文献/病例报告/综述"判成 ct-safety）；⑤ route.py 正则全中文，英文示例全部兜底 complex（EN 语义路由退化）；⑥ menu.py --lang zh 未接入 i18n。
- **修复闭环（2026-08-20 当日，用户拍板"保 PICO + 全部执行"后落地并逐一重测）**：
  - **D1（Ex5 P0）**：`route.py` 新增 `VAGUE_UNCERTAIN` 语义规则（`不…确定/不知道/没想好 + 需要什么/怎么办…`，支持"不太确定"被"太"隔断的形态；`VAGUE_UNCERTAIN_EXCL` 排除"不确定 X 是否/能不能"有明确对象的判断句）；README ×2 示例 5 描述改为实际 PICO 追问（人群/对照/终点）。重测：自测 29/29（+5 新用例），EN-5/ZH-5 均判 `vague` → clarify_loop 输出 PICO 问题，闭环成立。
  - **D2（Ex2 P1）**：`route_tool.py` + Coze `tool_router_node.py` 的 registry 触发词补「注册试验/登记试验/试验注册/试验登记/registered trial/trial registration」（精确复合词，不加裸词）；`_extract_params` SUFFIX 补「肽/抗体」+ 前导口语动词剥离（拉一下/帮我查 → cond 纯净）。重测：route_tool 自测 18/18+3/3；ZH-2/EN-2 预判 `ct-registry` 且 `cond=司美格鲁肽`（修复前 null）；Coze 规则表桩测 ZH-2→registry；文档类"分中心小结"防回归不触发；orchestrate 全链路从"未收录+建议"变为 `CT_TOOL_DELEGATE(ct-registry, missing=[cond])`——委托检索（线上 Coze 未部署新规则前，Coze 侧仍回"未收录"由委托补）。
  - **D4（Ex7 P1）**：`route_tool.py` ct-literature 触发词补「病例报告/个案报告/已发表/系统综述/meta分析/证据摘要」+ `LIT_FIRST` 优先规则（literature 与 safety 同命中且含检索意图词 → literature 优先）。重测：Ex7 预判 `ct-literature`（修复前 ct-safety）；FAERS 统计题仍判 ct-safety 防回归。
  - **D9（CLI P3）**：根因是 `i18n_messages.json` 缺 menu.json 全部 100 个 `menu.*`/`ground.*`/`out.*` key（menu.py 本身正确）——一次性补齐 100 个 key 双语翻译（352 keys）。重测：缺失 0；`menu.py --tier data_skill --human --lang zh` 输出中文（修复前 i18n key）；`--lang en` 正常。
  - **D10（EN 路由）**：EN vague 规则随 D1 落地（"not sure what I need"→vague）；EN 其余兜底 complex 转发为合理行为（英文正则覆盖收益低，不做过度工程）。
- **重测补充修复（16:07–16:35，用户"再测一下"触发，Ex2 链路 3 个新缺口）**：
  - **tool_mapping `--run` 缺失**：ct-registry 执行卡 `extra_args` 只有 `--auto-confirm`，停在 ct_registry PREVIEW 安全门（只提示 add --run、不发网络）→ `extra_args` 补 `--run`（对齐 ct-safety 的 run=true；编排器执行卡场景用户提问即检索指令，无条件联网）。
  - **term_map 术语缺口 + 共享件漂移**：ct-registry 无 GLP-1 类药物术语 → 中文"司美格鲁肽"检索英文库 0 条。按 §16.8 规范先把 6 个术语（司美格鲁肽/替尔泊肽/利拉鲁肽/瑞他鲁肽/度拉糖肽/艾塞那肽）加回 ct-base 真源，再同步 ct-advisor/ct-literature/ct-registry 三叶子（字节级一致 249 keys，shared_sync_check 全绿）；**ct-pipeline/ct-safety 历史 190-key 裁剪版（缺 59 key 既有漂移）随后一并从真源复制覆盖（249 keys，闸门全绿）**；KW 会话缓存 `config/kw_system_cache.json` 清空（旧缓存 en=[] 覆盖新术语）。
  - **ct_registry `--print-summary`（新增）**：cleanup 前把 landscape 摘要 JSON 打到 stdout（n_trials + phase_mix/region_mix/top_sponsors 分布），供编排器解析；tool_mapping extra_args 补 `--print-summary`。
  - **`handle_need_tool._extract_json` 嵌套 JSON 解析 bug**：旧实现 `rfind('{')` 取到嵌套内层 `{` 导致切片不完整、json.loads 失败退回全文 → 改为按行累积 + 括号深度闭合点逐段解析（单行/多行 JSON 均通过，纯文本兜底不变）。
  - **Ex2 最终端到端**：真实联网检索（CT.gov `total=569`）→ landscape 摘要完整输出（n_trials=50、phase_mix PHASE3×15/unknown×10/PHASE1×8/PHASE2×8/PHASE4×6、region_mix US×560 等、top_sponsors Novo Nordisk 居首）+ report.xlsx 产物——README 示例 2「自动分派返回归一化 landscape」完全兑现。
- **未发布**：本轮新增改动（tool_mapping.json / handle_need_tool.py / ct-base+3 叶子 term_map.json / ct-registry ct_registry.py+--print-summary / kw_system_cache 清空）均为本地改动；ct-registry 技能侧改动待其自身发布流程；未 commit 未 push。
- **未发布**：全部为本地改动（route.py / route_tool.py / menu.py / i18n_messages.json / README×2 / CHANGELOG）；Coze 端 tool_router_node.py 改动在本地 Coze 包，线上未部署；未 commit 未 push，待用户授权。

### 类型 B 追问自包含化（本地上下文摘要 + 拼接，代码级）

- **背景（真实链路实测）**：类型 B 追问（隐式承接、无回指词，如"若检验效能改用90%呢"/"如果HR是0.7呢"）被判 simple/middle/complex 直接转发 Coze，而 payload 只有 `original_question`、无上一题上下文 → Coze 重复追问已给参数（实测：用户已给 p1/p2 仍被追问），体验断裂。类型 A（显式回指"刚才说的…"）已由 route.py ANAPHORA → vague → clarify_loop 覆盖，不在本次范围。
- **方案①落地（Coze 契约零改动）**：
  - 新增 `scripts/context_stitch.py`（stdlib-only，无 LLM、无新增出域）：`is_followup()` 承接语气识别（强承接词 若/如果/那/改用/调整为/也适用/按…分配 + 短句；完整问题锚点 什么是/如何/样本量/检验… 不误伤）；`extract_summary()` 关键实体摘要（剥离"承接上一问…追问："前缀防多轮嵌套）；`stitch()` 拼接为自包含问题；`load_cache/save_cache` 会话缓存（`config/context_cache.json`，TTL 3 轮）。
  - `refine_answer.py --ship` 集成：转发前检测 follow-up → 读缓存 → 拼接 `承接上一问（<摘要>），追问：<原话>`；转发成功后用**原始问题**（非拼接后）更新缓存。
- **实测验证（真实 Coze 链路 3 轮）**：轮1 样本量问题（30%/45%/α=0.05/80%/1:1）→ 缓存写入；轮2 追问"若检验效能改用90%呢" → 自动拼接 → **Coze 返回具体数值（总样本量约 536 例 vs 80% 下约 394 例，+36%），不再 need_params 追问**；对比修复前同追问仅返回泛化方法论+追问参数。
- **回归**：route.py 24/24 不受影响；context_stitch 判定 10 例（5 追问 true + 5 独立问题 false）全对；py_compile 通过；多轮嵌套已防。
- **ignore**：`config/context_cache.json` 加入 .gitignore（运行态缓存不入库）。
- **未发布**：本地改动，待用户授权后发布（GitHub/SkillHub/ClawHub）。

## v0.9.69 (2026-08-15) — 七大流程端到端测试 + Coze 干净替换包 + 线上一致性检查（纯验证/打包，无逻辑改动）

- **新增 `scripts/test_seven_flows.py`（七大流程回归 harness，7/7 全绿）**：加载**真实本地 Coze 决策代码** `tool_router_node._match_tool()`（仅对其未安装的平台依赖 pydantic/langchain/langgraph/coze_coding_utils 做导入桩），驱动 7 个典型流程经真实 `route_tool.predict()` + `orchestrate.build_output()` + `_enrich_coze_params()`。覆盖：方法论包裹 / 同判包裹不重复调 / registry 参数富集（断言含 cond，实证 P0/P2）/ 跨工具委托 / Coze 兜底委托 / 缺参追问委托 / 执行失败重试委托。关键发现：前端与 Coze 规则集与顺序不同（前端 samplesize 优先、Coze registry 优先），编排器正确处理同判/异判/缺参/失败。
- **Coze 干净替换包**：`adapters/coze/project_20260812_152011_clean_20260815.zip`（76 文件 / ~422KB，结构 `project_20260812_152011/projects/...` 可整体替换上传）。剔除 4 项：`.coze/`（平台内部空目录）、`assets/refiner_contract*.md`（coze 接口契约文档，按发布规范不打包，且不在 KB 索引、非运行时加载）、`assets/2026-08-05 113007.004 0b543bb6.txt`（平台运行时日志垃圾）。
- **线上代码一致性检查**（用户提供 `Downloads/project_20260815_093047.tar.gz`）：线上 `projects/` 与本地源 **78/79 文件 MD5 一致**（含 tool_router_node 同步 docstring「真实必填参数由本地 route_tool.py 抽取」）；仅 3 处文档级差异（线上多 `coze_sync_guide_knowledge.md`、根缺 `NEED_TOOL_SCHEMA.md`（代码零引用、不影响运行）、category-reference 路径写法不同），无代码级问题。
- **飞书写入机制说明（文档化）**：`async_feishu_write` 在 5 个 review 节点（cache_check/simple/middle/complex/full_analysis）内部以后台 daemon 线程异步调用，**不是 graph 节点**（graph.py「移除 feishu_write 节点」）；令牌来自 Coze 平台集成凭据 `integration-feishu-base`（仅平台运行时存在），记录落在飞书多维表格（app/table 硬编码），成功/失败仅写平台日志；本地测试不执行 review 节点 → 看不到飞书记录属正常。
- **验证**：test_seven_flows 7/7；线上检查 MD5 全量对比 79 文件；zip 校验 76 文件无泄漏排除项、关键路径齐全。
- **§16 发布前检查 + STILL_PRESENT 6 项整改留痕**（基于 ct-base/BASE.md §16）：§16.1–§16.7/§16.9 通过；§16.6 两处 `zero-outbound` → `no outbound`（SKILL.md L111/L161，免疫 §16.6 grep 校验）；SKILL.md L63 `POSTs 3 variables` → `POSTs 3 top-level variables（query_meta / original_question / draft_answer…）` 消除歧义（审计 LOW Intent-Code Divergence）；ClawHub 审计 STILL_PRESENT 6 项逐项人工确认「设计如此/已披露/无实际风险」并留痕（`docs/clawhub_audit_trace_20260815.md`）：subprocess 白名单+无 shell / query_meta 口径已澄清 / 内嵌凭据公开性表述 用户授权+已披露 / original_question 出站已披露 / query_origin §8.6 规范 / mandatory 无害词汇命中无实际矛盾。UNVERIFIED 17 项人工核对 0 项需强制整改。**§16.8 遗留阻断已修复**：term_map 共享件同步（底座 53 key 补入叶子，243 keys 字节级一致，shared_sync rc=0）+ `scripts/test_seven_flows.py` 加入 `.clawhubignore`/`.gitignore`（git dry-run 泄漏计数 0）。
- **未发布**：纯本地改动（版本号 bump 仅 SKILL/README/README_zh-CN/CHANGELOG），未 push / 未发布三平台 / 未上传 Coze，待用户授权。


## v0.9.68 (2026-08-15) — 代码全自动编排器 `orchestrate.py`：预判预取 + 并行触发 + 决策全自动，ct 技能调用委托本地大模型

- **新增 `scripts/orchestrate.py`（代码全自动编排器，模式 B + 委托本地大模型）**：入口用 `route_tool.py` 高置信预判所需 ct 技能；在**代码内**以多线程**并行**触发 Coze 与预判的 ct 技能；合并两边结果并**由代码判定信息是否已足够**。
- **两类输出**（复用 `--ship` 同协议）：① 信息足够 → `<<<CT_ANSWER_START>>>`…`<<<CT_ANSWER_END>>>` 定界包裹答案（含 sha256 校验和），本地大模型只做原样透传（pipe）；② 仍需 ct 技能 → 输出 `<<<CT_TOOL_DELEGATE>>>` 结构化委托块（need_tool / params / draft_answer / original_question / missing_params）。
- **本地大模型定位（用户确认）**：**不是编排器**；收到委托块后只做两件事——① 向用户追问缺失参数（不编造）；② 把执行卡交给 `refine_answer.py --card-inline '<JSON>'`，由**代码**执行技能 + 确定性缝合 + 包裹答案。大模型**不**判定「信息是否足够」、**不**重写 Coze 文本。
- **新增 `scripts/route_tool.py`（模式 B 前端高置信预取，确定性、无 LLM）**：高置信才输出 `need_tool`（命中明确工具触发词 + 非 vague + 非定义/纯方法论）；漏判由 Coze 的 `need_tool` 兜底（不替代 Coze）。内置自测 15/15。
- **kw-gate 修复**：`tool_mapping.json` 的 `ct-registry` 新增 `extra_args: ["--auto-confirm"]`——translation miss 时直接用中文原文检索 CT.gov，避免 `sys.exit(2)` 卡死预判/编排流程。ct-safety / ct-literature 无确认门，不追加该参数（追加会触发 `unrecognized arguments` 错误）。
- **文档同步**：SKILL.md（新增 Code Orchestrator 段 + Routing 表 + Forward & stitch HARD GATES 加 orchestrate 项 + 执行卡协议改写）、knowledge/system_prompt.md（§0a 加编排器 + 委托协议）、references/ops.md（cookbook 加 orchestrate 调用 + `<<<CT_TOOL_DELOGATE>>>` 协议）、**两份 README 全量审计**——顶部/性能提示/概述改「非模糊问题经本地代码编排器 `orchestrate.py` 并行预取+合并+缝合、agent 只透传」；示例 3 改「本地代码编排器 dispatch+缝合（非 agent 手工）」；示例 4/5 改「走本地编排器 / vague 收敛后重跑难度判定再分流」；架构树补全 `route.py / route_tool.py / orchestrate.py / refine_answer.py / handle_need_tool.py / clarify_loop.py` 并修正注释；§2「five→four sibling skills」；版本号 → 0.9.68。
- 内置自测：orchestrate 决策 8/8、route_tool 预判 15/15，均 100%。

## v0.9.68 修复（2026-08-15，续上条）—— need_tool 场景参数链路纠偏（含 Coze 侧同步）

> 上一轮只读文档审计后，本轮从 Coze 代码包入手做了调用前后全链路 +「需要 ct 技能」各场景深度审计，发现并修复以下真实问题（全为本地代码 + Coze 契约同步，未动脚本外部行为红线）。

- **🔴 P0 REKEY 修复（`route_tool.py`）**：`ct-registry` 分支原抽到 `params["drug"]`，但 `tool_mapping.json` 的 `required_params` 是 `["cond"]`，键对不上 → 前端预判对 registry 永远满足不了必填项、必然 `need_params`，预判形同虚设。改为抽取 **`cond`**（覆盖 药/抑制剂/单抗/药物/化合物/制剂/类 等形态，并裁剪「检索/查/针对」等前导动词），并将 `cond` 正确填充进执行卡。自测新增 **参数键断言**（校验 REKEY 不回潮：registry 抽 `cond` 非 `drug`、samplesize 抽 `p1/p2`），route_tool 现 15/15 + 参数 3/3。
- **🟠 P1 `--ship` 参数富集（`refine_answer.py`）**：`--ship` 的 `need_tool` 分支原只拿 Coze 返回的默认参数（`max/top/alpha/power`）建卡，从不调 `route_tool.predict()`，导致纯 `--ship` 路径下任意 `need_tool` 100% 落 `need_params`，与「跳过大模型」目标在需要调技能时完全相悖。现合并本地 `route_tool.predict(original_question)` 抽到的真实参数（`cond/drug/topic/test/p1/p2`）覆盖 Coze 默认值（同工具才合并），使「代码跳过大模型」在 need_tool 场景也成立。**已确定性验证**：Coze `{'max':20}` + 前端 `{'cond':'PD-1抑制剂'}` → 合并卡含 `cond` → `handle_need_tool` 判定 `ok`（非 need_params）。
- **🟡 P2 编排器委托分支参数富集（`orchestrate.py`）**：「Coze 需不同工具」分支(2c)/无预判分支(2f)委托时原复用 `coze_params`（Coze 默认值），未对 Coze 工具重新抽参，大概率再弹一轮 `need_params`。现 `build_output` 入口对 `coze_params` 统一做 `route_tool` 富集（与 `--ship` 同策略）。
- **Coze 侧同步**：`tool_router_node.py` 设计约束段 + `NEED_TOOL_SCHEMA.md` 全面对齐——明确「Coze 仅判工具类别 + 可选默认值（max/top/alpha/power），**不抽取真实必填参数**（cond/drug/topic/test/p1/p2）；真实必填参数由本地 `route_tool.py` 抽取、缺失时本地 `need_params` 追问、代码执行器 `--card-inline` 缝合」；修正示例 `params`（去掉 Coze 不会返回的 `cond` 真实值）、`max` 默认 50→20、将「缝合由本地大模型完成」改为「代码缝合」。两端契约 now 一致。
- **⚪ P3（设计局限，已文档化）**：`ct-safety` / `ct-literature` 的真实 `drug/topic` 需语义抽取，正则能力天花板、前端不抽参，仍走 `need_params` 追问——属可接受限制，已在 NEED_TOOL_SCHEMA.md 与本条注明。
- **验证**：route_tool 15/15 + 参数 3/3、orchestrate 8/8、route 24/24；真实 `handle_need_tool` 执行验证 `cond`→`ok`、`drug`→`need_params(cond)`；真实 `--ship` 端到端跑通（定界包裹 + checksum）；P1 富集逻辑确定性单测通过。
- **未发布**：纯本地改动，未 push / 未发布三平台，待用户授权。

## v0.9.67 (2026-08-15) — 代码旁路主链路 `--ship`：答案组装移入代码，大模型退化为纯管道

- **新增 `scripts/refine_answer.py --ship`（代码旁路主链路）**：单次调用 Coze；若返回 `need_tool`，在**代码内**直接 subprocess 调 `handle_need_tool.py` 执行兄弟技能并做**确定性缝合**（Coze `final_answer` 为骨架 + `## 补充信息（来源：ct-xxx）` + 技能结果），最终答案以 `<<<CT_ANSWER_START>>>` … `<<<CT_ANSWER_END>>>` 定界包裹 + sha256 校验和输出。
- **新增 `--card-inline`**：`need_params` 重试路径——跳过 Coze 直发，直接用给定执行卡在代码内跑 `handle_need_tool` 并缝合（避免重复调用 Coze）。
- **核心目的**：根治「Coze 返回后本地大模型多余整合/重排」——agent 不再做答案组装，只做**原样透传（pipe-only）**。新增 🔴 Pipe-only HARD GATE（SKILL.md Forward & stitch 段 + ops.md cookbook + system_prompt.md §0a）。
- **文档同步**：SKILL.md（Forward & stitch HARD GATES 加 pipe-only 硬门、`--forward`→`--ship`、执行卡协议重写）、references/ops.md（cookbook 改 `--ship` + Behavior 段 + pipe HARD GATE）、knowledge/system_prompt.md（§0a 分流行加 pipe 硬门）、两份 README 版本号。
- 保留 `--forward` 仅作调试（返回原始 RefineResult JSON，禁止直接 ship）。
- **唯一无法消除的 LLM 环节**：① Coze 彻底失败时的本地兜底；② `need_params` 缺参需向用户追问（本质人在回路）。其余答案组装全部代码化。
- **未发布**：纯本地改动，未 push / 未发布三平台，待用户授权。

## v0.9.66 (2026-08-15) — route.py 入口难度判定：vague 优先且判断偏多

- **结构性修复（对齐"vague 必须准确、其余级别仅备用"）**：`route_question()` 判定顺序由
  `empty→is_simple→CPLX→is_vague→...` 改为 `empty→is_vague→is_simple→CPLX→is_middle→兜底`，
  **vague 提到第一优先（仅次空串）**。修复此前含代词的 vague 问题（如"这个样本量怎么算"、
  "那个试验设计要注意什么"）被 CPLX 词截走、误判为 complex 直接转发 Coze 的漏判。
- **vague 网放宽（判断偏多）**：代词上限 20→24；新增 `ANAPHORA` 回指/省略线索
  （前面/后面/上面/下面/前者/后者/之前提到/刚才说/上一条/您说的/…），覆盖"前面说的统计检验方法"类漏判；
  过短兜底保留术语/定义/标准操作精度护栏，避免"上报时限是多少"等清晰短句误判 vague。
- **自检回归**：内置自测 18→24 例（原 18 全保留 + 6 新增 vague + 1 精度护栏 simple），24/24 通过。
- 红线：仅本地改动，未 push / 未发布三平台；是否发布待用户授权。

## v0.9.65 (2026-08-15) — need_tool 执行卡接缝硬化（3b 强制硬门 + 骨架字段映射模板）

- **问题（实测风险）**：Coze 在 `need_tool` 分支下把缝合骨架放在响应 `final_answer` 字段；而 `handle_need_tool.py` 读卡时要用 `draft_answer` + `original_question`。原文档只说「读卡里的 need_tool/params/draft_answer」，但从未告诉本地大模型「`final_answer`（刚收到的）必须原样搬进 `--card` 的 `draft_answer`」，也漏了 `original_question`（ct-samplesize 检验类型自动推断依赖它）。缺这层映射，本地大模型容易①漏带骨架→丢 Coze 结构→自己重组（越界改写），或②图省事只交付 Coze `final_answer`、跳过兄弟技能执行。
- **修复（纯文档，不动脚本）**：
  - **3b 升级为 🔴 强制硬门**（SKILL.md 需求表 3b 行 + Skill-card execution protocol）：`need_tool` 非空 ⇒ **必须**跑 `handle_need_tool.py`；禁止只交付 Coze `final_answer`、禁止用本地 `knowledge/` 代答、禁止跳过调用。
  - **补执行卡组装模板**（SKILL.md + ops.md）：明确 `draft_answer := --forward 收到的 final_answer（骨架，原样复制）` / `need_tool` `params` 同值 / `original_question := 用户原话`，并给可直接套用的 JSON 示例。
  - **`refiner_contract.md` 响应 schema 补齐** `need_tool` / `params` / `run_id` 字段及「骨架」语义（仅本地维护文档，发布时被剔除，不影响线上）。
- **机制本体未动**：`refiner.py` 透传 `need_tool`/`params`、`handle_need_tool.py` 机械查表执行、`tool_mapping.json` 映射、缺参 `need_params` 追问均保持正确。
- **未发布**：以上均为本地改动，未推送任何平台（git push / ClawHub / SkillHub 仍待用户授权）。

## v0.9.64 (2026-08-14 晚) — 入口代码级难度门槛回滚激活（vague→本地澄清，其余 verbatim 转发）

- **架构微调（用户决策 2026-08-14 晚）**：在问题入口重新激活确定性难度分类器 `scripts/route.py`（代码级、无 LLM、stdlib-only），作为**唯一入口门槛**：
  - `vague` → 进入本地启发式澄清菜单 `scripts/clarify_loop.py`（有界 1–3 问/轮、硬上限 3 轮）进一步明确需求，澄清后带 `difficulty="vague"` 转发 Coze；
  - `simple`/`middle`/`complex` → **verbatim 转发 Coze（forward-only，不本地作答）**，并带 `query_meta.difficulty` 标签（Coze 端点内部再按自身判断路由）。
  - `route.py` 仅做难度判定，**不决定本地答 vs 发车**；全量直发（forward-only）主线保持不变。
- **文档同步**：SKILL.md（需求表 Refiner 行 / Answer Workflow Step 1 / 澄清触发段 / 硬门槛段 / 路由表 / "## 🔴 Code-based difficulty gate at entry"）+ steps.md（顶部 notice + Step 0 改写 + 路由分流注释 + Interaction strategy 段）+ ops.md（`difficulty` 字段 + §interaction-increment + 调用 cookbook 注释）+ AGENTS.md（§4 出站行 + §6 交互设计）+ units.md（UNIT-0 分流描述）+ README 两份（vague→Local Clarify Loop / 其余 verbatim 转发口径，含 §4 正文与扫描器误报段）+ **knowledge/system_prompt.md（§0a 分流块、§0 澄清质量门、Routing clarify 能力、§K 澄清模式：由 grill-me/本地作答/弹菜单 统一改写为 route.py 入口门槛 + vague→clarify_loop.py + 其余 verbatim 转发 Coze）+ knowledge/prompts.md（clarify.vague_invite 去 grill-me 措辞）**（§16.6 文档-行为一致性）。
- **Coze 端联动（上一轮已完成，本地未发布）**：`generate_organized_problems_node.py` 已增加空白 `difficulty` 的 LLM 判定与回写（`config/judge_difficulty_cfg.json`）。
- **未发布**：以上均为本地改动，未推送任何平台（git push / ClawHub / SkillHub 仍待用户授权）。

## v0.9.63 (2026-08-14) — 转发提示中立化 + 安全审计整改（发布前 §16 复核）

- **转发提示文案中立化**（commit 2e8a91e）：全量转发后所有问题不再预设"复杂/精校"难度，统一为"正在调用云端分析引擎，请稍候…"（SKILL.md + Coze 端 prompts.md 同步）。
- **ct-base §16 发布前安全审计整改**（commit 916afba，审计 `clawhub_security_audit.py` STILL_PRESENT 由 6 → 0）：
  - AGENTS.md 删除与"禁用 python -c"硬性禁令矛盾的陈旧 Option B 段落（文档自相矛盾消除）。
  - `adapters/refiner.py` `query_origin` 模块级 docstring 改为"主机派生稳定标识"（与 `compute_machine_id()`=sha256(hostname) 实现一致，消除 HIGH Intent-Code Divergence）。
  - README 两份出站披露补 `draft_answer` 一并外发云端精校（消除 Missing User Warnings 缺口）。
  - 密钥扫描 `publish_secret_scan.py` exit=0（47 WARN 均为 XOR+base64 混淆 blob + 变量名误报，无 P0/P1）。

## v0.9.62 (2026-08-14) — 全量直发架构 + need_tool 技能缝合 + 发布前合规整改

- **架构升级：全量直发（Forward）取代 race/serial/本地答三档分流**（用户决策 2026-08-14：本地大模型原则上不再回答问题，全部问题单次转发 Coze，仅作失败兜底）：
  1. `adapters/refiner.py`：新增 `RefineResult` 数据类（final_answer/cached_answer/cache_hit/need_tool/params）；`_call_coze` 改结构化返回（透出 need_tool 分支）；新增 `refine_forward()` 全量直发方法；`refine()` 兼容改道；`_refine_serial` 标记废弃。
  2. `scripts/refine_answer.py`：新增 `--forward` 主链路模式（单次调用 Coze，返回结构化 JSON，need_tool 分支透出执行卡，失败 FALLBACK 标记）；旧 fire-only/collect/serial 保留兼容。
  3. `scripts/handle_need_tool.py` + `scripts/tool_mapping.json`：本地技能执行器（4 技能映射 + `--yes` 自动确认）；新增 `_infer_missing_params` 缺参检查——`required_params` + samplesize `test_hints` 配置化推断 + 效应量缺失返回 `status: need_params`（由本地大模型追问用户、不编造）。
  4. **文档同步**：SKILL.md Answer Workflow 改为 forward 主链路（1 Forward → 2 收结果 → 3a 直接交付 / 3b need_tool 执行缝合 / 3c 失败本地兜底）；ops.md cookbook/behavior 改 forward；steps.md 顶部 mode-change notice + Step 0 改写（旧 race/serial 标 deprecated）；README 两份更新为全量转发描述（§16.6 文档-行为一致性）。
- **发布前合规整改（ct-base §16 检查清单，2026-08-14）**：
  - **【安全】config/keys.py 明文 JWT 移出发布**（§5 违反）：`adapters/refiner.py` / `scripts/check_coze.py` 凭据导入改走 `adapters/coze_token_embedded.py`（XOR+base64 混淆内嵌）；`config/keys.py` 加入 `.gitignore` / `.clawhubignore` 并 `git rm --cached`（本地保留作测试辅助，不再发布）。
  - **【架构】§16.9 出站收口**：`scripts/check_coze.py` 的 `requests.get` 抽到 `adapters/http_probe.py`（新增），scripts/ 层零出站。
  - **【对齐】README 两份**：保密声明口径 16+ → 20+（§13.1 定稿）；首屏 CLI 命令移入进阶参考（§13.3）；隐私/出站段更新为全量转发 + coze_token_embedded 描述。
  - **未发布**：以上均为本地改动，未推送任何平台（git push / ClawHub / SkillHub 仍待用户授权）。
- **目录整理**（2026-08-14）：`coze/` 云端部署项目（project_20260812_152011 等，1.9M）整体并入 `adapters/coze/`，技能顶层统一为 adapters/assets/config/knowledge/references/scripts 六目录；发布排除规则（`.gitignore`/`.clawhubignore`）同步为 `adapters/coze/` 整目录；`references/tone_writing.md` 去除 `coze/` 路径断链；清理历史 zip 与 `.ctbase_injected.json`。云端项目仍不随技能发布，本地运行时零依赖。

## v0.9.61 (2026-08-13) — 兄弟技能调用协议：披露 5 要素 + 确认门 + 回灌 advisor

- **SKILL.md Routing 段 + steps.md Step 3 新增「Sibling-skill call protocol (MUST)」**（实测复盘：PD-1 间质性肺炎文献检索暴露"路由静默切换 / preview 确认门被跳过 / 结果独立产出未回灌"）：
  1. **披露 5 要素**（调谁 + 原因 + 动作与外部数据源 + 预计耗时 + 结果如何回灌），示例模板内置；
  2. **执行计划 + 一次确认**（Quick Mode 例外：用户请求已明确关键参数可免确认，仍须展示计划）；
  3. **Return-to-advisor**：调用完毕后结构化结果回到本工作流——窄口径作为回答主体（标注数据源+溯源）/ 宽口径就地缝合战略 brief / 链式需求继续决策下一技能（如文献安全信号 → ct-safety FAERS 定量互证），不得在兄弟技能处终结线程。
- **README 协同调用示例（并入）**：README.md / README_zh-CN.md 各新增 2 个兄弟技能协同调用示例（现共 8 个）——示例 7 已发表安全性证据核查（ct-literature --safety + ct-safety 互补）、示例 8 方案写作证据基础 + 样本量协同（ct-literature + ct-samplesize 跨档协同）。
- **ct-base 联动**：§15 同步新增「路由披露 + 执行确认 + 结果回灌」全库统一规范（ct-base v1.1.33）。

## v0.9.60 (2026-08-13) — Coze 调用失败防护：死代理自动绕过 + fallback 诊断输出

- **根因（用户实测排查）**：Windows 系统代理残留（`HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:10808/` 无监听）→ requests 走死代理 → WinError 10061 → ProxyError → fallback；叠加"串行 payload 未带 draft_answer"→ fallback 输出为空（只有报错、没有答案）。
- **① 出站代理容错（`adapters/refiner.py` `_call_coze`）**：`requests.post` 捕获 `ProxyError`/`ConnectionError` 后**自动绕过系统代理直连重试一次**（`proxies={"http":None,"https":None}`）——死代理场景通常一次重试即恢复；直连也不可达才继续抛给上层 fallback。单测验证：2 次调用（ProxyError→直连成功）✓。
- **② fallback 诊断输出（`scripts/refine_answer.py`）**：serial 失败且 draft 为空时，stdout 输出友好询问 `Coze 云端服务暂时不可用（原因），本次回答可能不够完善。是否允许我自动进行问题诊断排查？`（i18n 键 `error.fallback_diagnose`，en/zh 成对；不再暴露脚本路径/技术细节）；fire-only 失败时 stderr 提示诊断入口。
- **③ 新增 `scripts/check_coze.py` 一键诊断**：四查（token 就位 / 环境代理变量与端口可达性 / 绕过代理直连 / 按代理请求）+ 修复指引（死代理→关系统代理或 NO_PROXY；断网→查网络；token→重装）。实测本机：token ✓ 无代理 ✓ 直连 HTTP 401（端点可达+鉴权生效）✓。
- **④ 诊断规则入档（user-friendly）**：SKILL.md（Call style 段）与 steps.md（Step 5）更新为——fallback 触发时**先友好询问用户"是否允许自动诊断排查"**，允许→自动跑 check_coze.py 定位根因并修复重试；拒绝→交付本地答案+**重提示**「无法连接 Coze 服务，答案未经过精校，请谨慎使用」。
- **未发布**：本地改动，未推送任何平台。

## v0.9.59 (2026-08-13) — ClawHub SkillSpector 审计修复（49 findings 处置）

- **compute_machine_id 文档诚实化（审计"主机派生标识与文档矛盾"命中）**：docstring 明确 `query_origin` 为 `sha256(hostname)` 主机派生稳定标识（同一机器跨请求一致，用于审计/归因/限流），承认低熵可猜测与跨请求设备关联属性；**实现保持稳定标识不变**（用户需求：每机器固定 sha256；0.9.52 曾改每进程随机后被回退，CHANGELOG 已留痕）。
- **to_payload 精简回 3 变量契约（审计"超过 3 变量契约"命中）**：外发仅 `query_meta` / `original_question` / `draft_answer`；`question_profile` / `confirmation` / `tone_profile` / `memory_context` 保留在 RefineRequest 内但**不再外发**（服务端 GraphInput 未实现，待 v1.6 字段补齐后恢复）。
- **prompts.md 去指令化（审计"prompt mirror 含运行时指令"命中）**：语言规则移除"顾问运行 `switch_lang.py`"可执行指令，仅保留纯 UI 语义（switch_lang 执行细节归 SKILL.md/steps.md）。
- **README 首屏隐私披露补强（审计"Missing User Warnings"）**：两份 README 隐私段明确 `query_origin` 为"同一设备每次请求一致的稳定标识"（stable per-device，用于审计/限流），安装前知情。
- **已披露的接受风险（SkillSpector 仍可能标 Medium）**：内嵌共享凭据（用户拍板允许发布）、稳定机器标识（用户需求）——属知情设计权衡，非隐藏行为。
- **SKILL.md 安全压缩（加载优化，198→174 行 / -12%）**：仅压缩说明性区块（Overview / Requirements / Knowledge Map 辅助条 / Auth Gate 确认模板 / Clarify Loop / Routing / Boundaries / China / Performance 句），**防回归红线全保留**（Step 0 跑 route.py、simple local-only、fire-only、HARD GATE、Knowledge Map 单检、输出纪律、SIMPLE_TOPICS、query_meta.difficulty 必传）；评估确认"核心规则下沉 references 靠 agent 按需读"方案有回归风险（历史 3–5min 循环根因），未采纳。回归：self-test 18/18、桌面库 78%、0 漏发车、markdown 完整。
- **未发布**：本地改动，未推送任何平台。

## v0.9.58 (2026-08-12) — 契约对齐服务端 v1.5 + tone/memory 暂不启用

- **以服务端为准（用户决策①）**：本地 `coze/coze_system_prompt_v1.4.md` 快照由 v1.6 覆盖为**服务端实际部署的 v1.5**（priority-flipped：original_question > organized_problems > draft_answer；organized_problems 由 Coze 端 generate_organized_problems 节点生成）。本地契约文档（refiner_contract.md）描述与服务端工作流核对一致（Coze 端自行构建 organized_problems、本地不再生成）。
- **tone/memory 暂不启用（用户决策②）**：服务端 GraphInput 无 `tone_profile` / `memory_context` 字段（注入被静默忽略）→ SKILL.md Personalization 小节改为 DEFERRED 声明；`references/tone_writing.md` 顶部标注暂不启用；`--tone` / `--memory` CLI 与脚本保留但禁止调用（服务端补齐 v1.6 字段后可重启用）。
- **race 保持无草稿（用户决策③）**：middle race 仍只发 `original_question`（draft 空）→ 服务端 validity_check 判无效 → full_analysis 全量生成；不改草稿。
- **difficulty 兜底修复（飞书收集空白根因）**：`adapters/refiner.py` normalize() 对缺失/非法 difficulty 由清空 `""` 改为默认 **`"complex"`**（宁保守：draft 非空必是 complex serial、draft 空走 full_analysis 值不影响；空白 difficulty 会让服务端分流异常 + 飞书收集空白）；steps.md fire-only/serial 调用示例补全 `query_meta`（含 difficulty），SKILL.md 补 payload 示例与 "MUST carry query_meta.difficulty" 提示。
- **已识别的服务端行为（知情）**：middle_review/simple_review 分支因本地调用方式实际闲置（仅 complex_review 生效）；服务端语义缓存（相似度>95% 命中直接返回）与飞书多维表格收集（目的②落地）为服务端既有行为。
- **未发布**：本地改动，未推送任何平台。

## v0.9.57 (2026-08-12) — 路由层定稿：route.py 四档 + SIMPLE_TOPICS 白名单（Mode B 落地）

- **`scripts/route.py` 新增 `SIMPLE_TOPICS` 白名单**：取自 `knowledge/reference-index.md` 覆盖主题的标准操作/定义类短语（ALCOA / SAE 报告时限 / 药物计数 / 急救揭盲 / 筛选日志 / 数据库锁定 / 知情同意撤回 / 怀孕 / 筛选失败 / CRF 填写等 40+ 词）。`is_simple` 判定增加"白名单命中 且 无 CPLX/EXCL 信号 → simple"，是确定性查找表（不受提问句式漂移影响）。四库联合验证：simple 召回 桌面 20→22 / 第二版 3→12 / 全新 11→12 / D库 7→12，**0 漏发车**（非 simple 题误判 simple = 漏发 Coze 收集，红线）。
- **迭代剔除 9 个过宽词**（跨库撞中等题）：方案 / 系统 / 应.*?记录 / 如何记录 / 需要满足哪些条件 / 需要完成哪些(收窄为核心|关键) / 裸"定义"(收窄为查询式) / 源数据 / 交通补贴 / 误工补偿 / 温度记录 / susar / icf / query / 方案偏离（桌面 Q62 中等题会漏发车）。
- **`references/steps.md` Step 0**：simple 行加"or knowledge whitelist hit (SIMPLE_TOPICS)"；新增白名单说明段（维护约定：加词须跑 self-test + 题库评测确认不漏发车）。
- **`SKILL.md` Answer Workflow 同步**：Step 0 Triage 改为"run `route.py` (deterministic, zero-LLM)；agent MUST NOT self-judge"；Performance HARD GATE 的 Step 0 描述同步；difficulty bias rule 的 simple 定义补白名单 + 明确"middle/complex 均发车，simple/非simple 是语义分水岭"。版本 0.9.56 → 0.9.57。
- **端到端实测（真调 Coze，三案例）**：middle（race）fire-only → collect 0.63s cache hit verbatim；complex（serial）本地初步 → Coze 精校 20.6s（Coze 纠正本地初步偏差）；simple 本地直答秒级。**3–5 min 循环根除，最慢 20.6s**。
- **未发布**：本次仅本地文件改动（本地升 0.9.57），未推送 SkillHub / ClawHub / GitHub，待确认后发布。

## 0.9.53 (2026-08-12) — P0-B 语气写作 + P1-D 本地用户记忆（ct-update 自动实施）

- **P0-B 语气写作（clarify_loop 增强版）**：新增 `scripts/tone_matcher.py`，从用户写作样本提取**仅表达风格**的 `tone_profile.json`（句式长度 / 正式度 / 人称 / 段落结构 / 修辞 / 连接词 / 术语风格 / emoji / 标点），经 `refine_answer.py --tone <profile>` 注入 Coze 精校契约的 `tone_profile` 字段。新增 `references/tone_writing.md` 说明文档。
- **🔴 风格硬闸（B）**：提取阶段正则识别并剔除日期 / 项目名 / 机构名 / 人名 / 指标数字，事实绝不进入 `features`；注入时附 `[HARD GATE]` 风格硬闸指令；Coze 契约（v1.6 输入 + 规则 6）明确仅沿用表达风格、不复用样本事实。理由：样本可能含过时信息。
- **P1-D 本地用户记忆**：新增 `scripts/memory_manager.py`，支持 `add/list/load/prune/clear`，写入 `~/.workbuddy/ct-advisor-memory.json`（**刻意避开** `MEMORY.md` 以免冲突）；默认 **TTL 90 天**（过期由 `prune` 清理）；`add` 非交互模式强制 `--confirm`、`clear` 强制 `--confirm`（用户确认机制）；`refine_answer.py --memory <path>` 注入契约的 `memory_context` 字段，Coze 仅作背景上下文（契约规则 7）。
- **契约增量（adapters/refiner.py）**：`RefineRequest` 新增 `tone_profile` / `memory_context` 两个 `dict` 字段（默认空），`normalize()` 容错归一、`to_payload()` 随契约外发；原三字段 + 澄清字段完全不变，下游兼容。
- **Coze 契约同步（coze/coze_system_prompt_v1.4.md）**：`## 输入` 新增 `tone_profile` / `memory_context` 两个可选字段说明；`## 核心作答规则` 新增规则 6（风格硬闸）/ 规则 7（记忆边界）。⚠️ 此文件为契约 doc 快照；线上 Coze Bot 的 prompt 需另行 redeploy 才会生效（发布动作，待确认）。
- **SKILL.md**：Answer Workflow 新增 `### Personalization（tone writing + local user memory）` 小节，给出两项的调用方式与硬闸提示。
- **未发布**：本次仅本地文件改动（本地升 0.9.53），未推送 SkillHub / ClawHub / GitHub，待确认后发布。

## 0.9.52 (2026-08-09) — 安全审计修复（ClawHub SkillSpector 重审）

- **承接 0.9.51（此前未发布）一并发布**：0.9.51 的 simple-local-only / 三流程重构、逻辑修正、英文化、README 同步全部随本版本首次上线。
- **清 2× Critical `suspicious.dynamic_code_execution`**：`adapters/refiner.py` 与 `scripts/refine_answer.py` 原用 `importlib.spec_from_file_location()` + `loader.exec_module()` 动态加载 `config/keys.py`；改为标准 `from config.keys import get_token`（ROOT 已在 sys.path），消除动态代码执行启发式命中。
- **清 1× Medium 凭据存储面**：移除 `refine_answer.py` 的 `--store-token` / `--token-path` CLI 参数及其 importlib 落盘块（token 已内嵌 `config/keys.py`，无需运行时写盘）；`keys.py` 的 `store_token()` 函数保留为惰性向后兼容、不再经 CLI 暴露。
- **降 1× Medium 主机归因**：`compute_machine_id()` 由 `sha256(hostname + salt)` 稳定主机标识改为**每进程随机 seed**（`sha256(os.urandom(16))`），去掉跨会话/设备的机器归因与关联，仍满足 `query_origin` 契约（sha256:64hex），Coze 侧仍可单请求级限流；同步移除 `import socket` 与 `MACHINE_SALT` 常量，更新 frontmatter `permissions.data` 描述与模块 docstring。
- **发布**：升 0.9.52 推送 GitHub + SkillHub + ClawHub，触发 ClawHub 重新跑 SkillSpector 安全审计。

## 0.9.51 (2026-08-09) — simple 拆分出 local-only 模式（不发送 Coze）

- **simple 独立 local 模式**：将 `simple` 从 race 拆分出独立列 `Local(simple)`。simple 难度问题**不 fire Coze**、**不做出站授权**、直接以本地 `knowledge/` 完整作答（Step 0 → Step 2 本地作答 → Step 6）。Step 2 的 Local(simple) 列由 `collect → 6` 修正为 `local answer → 6`；Step 6 同步标注 `from local answer (step 2)`。
- **全局描述同步**：frontmatter `network_note`、Requirements 的 Coze 行 / Network 行、Anti-shortcut、Performance HARD GATE 全部由"simple/middle 必须 fire / 无 local 模式"改为"simple 走 local-only、仅 middle/complex 走 Coze"，消除自相矛盾。
- **Difficulty bias 调整**：纯方法论问题由"总是判 middle"改为"总是判 simple 或 middle（绝不判 complex）"，并明确单一事实/定义/标准操作判 simple（local-only），解释/比较/多步推理判 middle（race），使 simple-local 真正可触发。
- **未发布**：本次仅本地文件改动（本地升 0.9.51），未推送 SkillHub / ClawHub / GitHub，待确认后发布。
- **同步 `references/steps.md`**：Step 0 难度表（simple 下游改为 → step 2→6 local-only）、Difficulty bias（纯方法论判 simple/middle）、Anti-shortcut、Interaction strategy（simple 不 fire）、Step 1 behavior 表（simple 标 skipped）、Step 2 拆分出 Local-only mode (simple) / Race mode (middle) / Serial mode (complex) 三段、Step 6 来源表与 Final pre-output check 表，全部对齐三流程新设想；文件 version 升 2026-08-09。
- **逻辑矛盾修正（规则 8 / 检索分工红线 vs complex Step 3）**：Knowledge Map 规则 8 与 Routing 检索分工红线新增 **complex Step 3/4 同胞出站豁免**——原"本地检索后严禁外部网络数据检索"字面会误中 complex 的 Step 3 设计内真实数据供给（complex 在 Step 2 做本地 Route 后 Step 3 出站）；明确该红线仅防 simple/middle 的"本地兜底 + 外部叠加"，complex 的同胞出站是 Coze 串行整合前的设计内主流程，不在禁止之列。
- **正文英文化（对齐 ct-base agent-facing 全英文规范）**：SKILL.md 残留中文正文——Knowledge Map 规则 3 / 7 / 8、Answer Workflow 表 Auth 行与 Step 5 行中文标注、出站授权门控整段（模板仅留英文）、检索分工红线——全部改为英文；`references/steps.md` 两处中文残留块（L65-68、L150 出站授权门控说明）同步英文化。frontmatter 规范中文（cn_name / summary / description 双语）、displayName、trigger_scope 双语、Serial-mode 双语用户通知予以保留；trigger_scope 英文翻译夹带的中文"主动"修正为 `does NOT proactively match`。
- **同步双语 README（用户向 walkthrough）**：`README.md` / `README_zh-CN.md` 全面同步三流程设想——性能提示（race 仅 middle、simple 本地零出站）、概述 Note、隐私提示（仅 middle/complex 出站、simple 零出站）、FAQ「纯方法学要联网吗」（按难度区分）、§4 出站与隐私（标题/正文改为仅 middle/complex 走 Coze、step 2/6 调用）、§5 Coze 模式行 / config.json 注释 / 扫描器误报说明均补 simple 例外（simple 本地零出站、不连 Coze），middle/complex 仍走 Coze；两份版本号由 v0.9.38 升 v0.9.51。

## 0.9.50 (2026-08-09) — 本地检索纪律红线（单检 + 禁外部叠加）

- **本地检索硬性上限**：每轮仅允许检索 1 次（原"≤2 knowledge reads"收紧为"1 次"），无论命中与否，检索后立即进入下一步流程，禁止第二次本地检索、多步本地 read 串联、把简单问题展开成复杂检索流水线（Knowledge Map 规则 3）。
- **未命中直走 Coze**：本地检索未命中时严禁继续读 `reference-index.md` 或再 Read 任何 `ref-*` 文件，直接把原始问题交给 Coze 远端处理（原"no-match escape hatch"多步本地兜底删除，规则 7）。
- **本地检索后严禁外部网络数据检索**：一旦本轮做了本地检索，禁止再触发任何外部网络数据检索（含 Skill 路由到 ct-registry / ct-safety / ct-literature 等兄弟技能出站），一切信息以 Coze 远端处理为主；本地兜底与同胞出站不得叠加为双检索流水线（新增规则 8 + 路由表红线注释）。
- **配套收敛**：Anti-shortcut HARD GATES 新增 local-retrieval discipline 条目；Performance discipline 的 search-backoff 改为"0 命中直走 Coze、不再链式本地 read"。

## 0.9.49 (2026-08-09) — 双语提示补全 + 死参清理 + 发布态健康检查

- **i18n 双语补全**：将 `refine_answer.py` / `run_refined.py` 顶层残留的硬编码中/英双显与纯中文提示（依赖缺失、回退本地、空问题描述、payload 解析/自愈、base64 解码失败）全部接入 `t()`；新增 `error.empty_question` / `error.payload_healed` / `error.payload_invalid` / `error.refine_fallback` / `error.base64_decode` / `error.dependency_fatal` 六个通用双语 key，沉淀至 ct-base 共享 `i18n_messages.json`（ct-advisor 包内快照同步）。
- **死参清理**：`CozeRefiner.__init__` 与 `build_refiner` 移除无效的 `cli_token` / `token_path` 形参（`get_token()` 现无参调用，token 统一走 `config/keys.py`）；同步删除 `refine_answer.py` / `run_refined.py` 中对应的死参传递与 `--token` / `--token-path` CLI 定义（`store_token` 仍使用 `--token-path`）。
- **发布态健康检查**：清理 `_stash_tmp/ct-advisor_pub`（含误打包的 `.workbuddy` 记忆残骸）与 `_pub_trash_ctadvisor_09047` 临时残留目录。

## 0.9.48 (2026-08-08) — 修复 refiner token 调用签名 + 出站鉴权告警

> 修复云端精校（Coze refine）因函数签名不匹配而永不触发的隐藏 bug，并将版本升格以在 SkillHub 覆盖已存在的 0.9.47。

- **修复 get_token 调用签名不匹配**：`adapters/refiner.py:431` 按旧 3 参签名 `get_token(cli_token, token_path, token_env)` 调用 `config/keys.py` 的无参 `get_token()`，抛 `TypeError` 后被 `refine_fire_only` 的 `except Exception: return ""` 静默吞掉 → POST 永不发出、云端精校恒降级本地。调用处改为无参 `get_token()`。
- **出站授权白名单**：`config.json` 的 `auto_approve_endpoints` 加入 `https://ct-advisor.coze.site/run`（用户已授权出站）。
- **HTTP 错误显式告警**：`adapters/refiner.py` 的 `_call_coze` 加 `raise_for_status()` + 401 `AUTH_REJECTED` 告警，防止 4xx/5xx 再被伪装成超时。
- **knowledge/ 修订**：多文件修订、去重与 `reference-index` 重建。

## 0.9.47 (2026-08-08) — 公共凭据统一 config/keys.py（SkillHub 文件过滤规避）

> 公共凭据从分散的 `adapters/coze_token_embedded.py` + `config/coze.dat` 统一迁移到 `config/keys.py`，解决 SkillHub 平台对非白名单后缀文件的静默剥离问题，并提供可扩展的公共凭据管理规范。

- **凭据集中存储**：新增 `config/keys.py`，所有公共凭据以 Python 常量形式声明（如 `COZE_TOKEN`）。后缀 `.py` 属于 SkillHub 白名单，不会被过滤删除。
- **统一引用方式**：`adapters/refiner.py`、`adapters/__init__.py`、`scripts/refine_answer.py` 全部改用 `importlib.util.spec_from_file_location("config.keys", "config/keys.py")` 动态加载，消除相对路径问题。
- **向后兼容**：`keys.py` 提供 `get_token()` / `default_token_path()` / `get_secret(name, fallback)` / `store_token(plain, path)` 等兼容函数，旧代码引用链保持可用。
- **文档同步**：`SKILL.md` 第 67 行 Refiner 凭据引用从 `adapters/coze_token_embedded.py` 更新为 `config/keys.py`。
- **规范固化**：`ct-base AGENTS.md` 新增 §7「公共凭据存储规范」，明确规则、命名、编码、引用方式、发布检查项。

## 0.9.46 (2026-08-08) — 出站授权门控（符合 SOUL.md 外部操作确认规范）

> 新增出站授权机制，首次调用 Coze 前自动提示用户确认，并支持白名单持久化。

- **出站授权门控（Auth Outbound Check）**：`scripts/refine_answer.py` 在 `--fire-only` 和串行调用出站前自动检查授权：
  - 端点在 `config.json` `auto_approve_endpoints` 白名单中 → 直接放行
  - 本会话已授权过（脚本进程内内存记忆）→ 直接放行
  - 未授权 → 脚本在 stderr 输出 `[AUTH-BLOCK]`，agent 提示用户确认
- **白名单配置**：新增 `config.json` `auto_approve_endpoints` 数组字段，存储已授权端点 URL
- **确认提示文案**：明确告知用户"本地参考资料有限，不发送将无法使用云端数据库做检索"
- **文档更新**：SKILL.md 新增"出站授权门控"段，steps.md Step 1/5 补充授权说明，ops.md 新增 §outbound-auth 权威定义
- **未阻断流程**：授权检查**不**阻断——未授权时脚本返回空串/本地草稿，agent 采用本地胜出方案

## 0.9.45 (2026-08-08) — 版本升格（三平台统一 0.9.45，确保 coze 接口文档不打包）

> 0.9.44 已先于 SkillHub 创建；SkillHub 不允许同版本重发，故升格 0.9.45 在三平台统一发布。内容同 0.9.44（见下），并借此次确认 SkillHub 发布包排除 coze 接口文档（refiner_contract / coze_system_prompt / subagent_prompt / ops）。

- **跨文件去重**：SKILL.md 作为入口摘要，删去与 `references/steps.md` 逐字重复的展开段，改为指针引用：

- **跨文件去重**：SKILL.md 作为入口摘要，删去与 `references/steps.md` 逐字重复的展开段，改为指针引用：
  - Anti-short-circuit + RACE-MODE VERBATIM 两条 HARD GATE 合并为单段摘要（详细禁止列表 / failure-mode 注 → steps.md Step 0 / Step 2）。
  - Encoding strategy 整段删除，改为单行 caveat + 指向 steps.md "Call-style summary"（表格与编码策略原样保留在 steps.md）。
  - Performance discipline 删冗余的 "Fire immediately" 展开（与 steps.md Step 1 重复），search backoff 指向 Knowledge Map rule 7（消除同文件内与 rule 7 的双写）。
  - Difficulty bias rule 删 "Why bias" + 典型误判例子（与 steps.md Step 0 逐字重复），保留规则本体 + 指针。
- **steps.md 内部合并**：Step 2 verbatim 表述在 Goal / HARD GATE / "jump to step 6" 三处同义堆叠，合并到一处 HARD GATE（post-collect zero-processing）权威定义，删冗余行。
- **净效果**：SKILL.md 删约 40 行、steps.md 删约 10 行；信息零丢失，维护时不再"改一处漏一处"。语义 / 流程 / Python 代码均不变。
- **补漏（同版本内）**：Answer Workflow 步骤表残留的中文单元格（Race 列 `fire-only 立即…`、Step 2 责任列 `collect 主轴…`、Serial 列 `写本地答案…`）补全为英文，落实 SKILL.md body English-only（agent-facing）规范；仅第 171 行 Serial 中文通知模板（配英文翻译）为有意保留的双语示例。
- **代码微调（同版本内）**：`adapters/refiner.py` 的 `normalize()` 自愈逻辑改为——`difficulty` / `category` / `accuracy` 缺失或非枚举合法值时统一补**空串 `""`**（原补 `"middle"` / `"general"` / `"normal"`）；同步放宽 `validate()` 对这三项的"必填非空"约束（仍校验非空时的枚举合法性）。效果：**race 模式 `--fire-only` 出站给 Coze 的 payload 中 category 等真实为空白**，不再由脚本强加占位默认值。相关注释（模块 docstring L8、normalize docstring、validate docstring、__init__ 注释）一并更新。
- **steps.md 回同步（中文版→英文版）**：用户改中文翻译稿后，把两处实质改动同步回 `references/steps.md` 英文原版：① 修正 0.9.43 重编号残留——预路由拦截里数据交接 `step 4→step 3`、样本量交接 `step 5→step 4`（与 L90/L118 对齐）；② AskUserQuestion 问题数 `1–3 / ≤3 → 1–5 / ≤5`（Step 0 表格与交互策略两处一致）。中文检查稿 `ct-advisor-steps-zh-CN.md` 不参与发布。
- **category 取值低成本对齐（同版本内，未拆字段）**：明确 `category` 两套编码的边界——Coze 语义枚举（6 值）与 A–J 工作流路由码靠 `:字母` 后缀连接。具体：① `refiner_contract.md` §1.1 取值表新增 `methodology:C`（统计/样本量），并加「字母映射 A–J」与「样本量须写 `methodology:C`、禁止 `sample_size:A`」两段约定；② 同步 `coze_system_prompt_v1.4.md` L7、`references/ops.md` L52+L65（示例 `methodology`→`methodology:B`）、`adapters/refiner.py` L19 注释。仍保留单字段承载（不动远程契约），仅对齐语义与字母映射（修掉样本量 B↔C 归属矛盾）。
- **AskUserQuestion 问题数定为 ≤4（同版本内修正）**：`vague` 澄清问题数从 `1–5 / ≤5` 收敛为 `≤ 4`，与工具硬约束 `maxItems=4 / minItems=2` 对齐（原 `1–5` 既触下限 `1<2` 又触上限 `5>4`）。`references/steps.md` L22 表格 + L48 交互策略两处，以及中文检查稿 `ct-advisor-steps-zh-CN.md` 对应两处，同步改为 `≤ 4 个问题`。
- **race 模式补传 difficulty（同版本内修正）**：上条 `normalize()` 把 `difficulty` 缺失补空串后，race `--fire-only` 出站 `difficulty` 恒为空串，丢失了 Step 0 Triage 已判定的 `simple`/`middle`。现修正 fire-only 调用指令——agent 在 `query_meta` 写入 Triage 实际判定的 `difficulty`（`simple`/`middle`），`category`/`accuracy` 仍留空、`draft_answer` 留空。改动仅文档层（`references/steps.md` L59 + `references/ops.md` L57 + 中文检查稿 L59），**Python 零改动**（`normalize()` 本就保留合法枚举值）。本地 to_payload 校验 + 真实远程 fire-only/collect 往返均确认 `difficulty=middle` 被传出、`category`/`accuracy` 仍空。顺带修掉 L59 里 `--payload-inline '{…}'` 误导（中文 `original_question` 下单引号必失败，规范为 stdin pipe）。

## 0.9.43 (2026-08-08) — 合并 Step 2/3 + 重编号（Steps 0–6）

- **Race 路径合并**：原 Step 2（Route，本地检索）与原 Step 3（Local Answer，collect + 兜底）合并为单一 **Step 2（Collect + Route + Local Answer）**。
- **核心机制修正**：合并步以 `--collect --wait=race_window` 为**主轴阻塞点**，本地 Route 检索降级为"collect 等待窗口内的可选副任务"——Coze（≈20s）命中即 verbatim 输出，本地检索仅在超时时兜底，**永不阻塞输出**。彻底消除"Step 2 本地检索耗时 2 分钟导致用户干等"的隐患。
- **重编号**（后续步骤自然前移）：原 Step 4→3、Step 5→4、Step 6→5、Step 7→6；流程变为 Steps 0–6。
  - Race (simple/middle)：`0→1→2→6`（Step 1 Fire 后直接进入合并步 collect）
  - Serial (complex)：`0→2→3→4→5→6`（Step 1 Fire 跳过，合并步做 Route + 写本地答案）
- **波及文档全部 step 引用同步**：`SKILL.md`（Step 表 / Anti-short-circuit / latency HARD GATE / Presentation rules / Serial notice）、`references/steps.md`（标题 Steps 0-6 / 路径表 / Anti-shortcut / Step 1+2 合并段 / Step 3-6 重编号 / Final / checklist）、`references/ops.md`（step 引用 + race_window default 2s→30s 修正）、`knowledge/system_prompt.md`（escalate to Coze step 引用）、`coze/subagent_prompt.md`（step 2/6 引用）。
- **未改**：Python 代码（refiner.py / refine_answer.py）零改动；`race_window=30s`（config.json）不变；`backend` 死配置不动。

## 0.9.42 (2026-08-08) — 步骤编号互换（Step 1 ↔ Step 2，让主路径数字连续）

### 改动
- **步骤编号互换**：Fire Gate（原 Step 2）升为 **Step 1**、Route（原 Step 1）降为 **Step 2**。逻辑不变（fire 始终在 Route 前、Triage 后第一网络动作），仅互换序号让 Race 主路径数字顺下来。
- **路径表达式更新**：
  - Race (simple/middle)：`0→2→1→3→7` → **`0→1→2→3→7`**（连续）
  - Serial (complex)：`0→1→2→3→4→5→6→7` → **`0→2→3→4→5→6→7`**（complex 不走 fire-only，跳过 Step 1）
- **波及文档全部 step 引用同步**：`SKILL.md`（Step 表 / Anti-short-circuit / latency HARD GATE）、`references/steps.md`（路径表 / Anti-shortcut / Step 标题与正文 / checklist）、`coze/subagent_prompt.md`（workflow 字段来源 step 1→step 2）、`references/ops.md`（fire 步骤 step 2→step 1）、`knowledge/system_prompt.md`（escalate to Coze 步骤 step 2→step 1）。

### 未改动
- 流程语义、Python 代码、HARD GATE 约束均不变；仅序号与引用文本调整。

## 0.9.41 (2026-08-08) — 速度优化（消除"几分钟才出结果"）

### 根因（实测修正，推翻 v1 误诊）
- 读透 `adapters/refiner.py` + `scripts/refine_answer.py` 确认 Python 代码层是轻量的（fire-only = 一次 POST + 写缓存；collect = 读缓存）；Coze 实测 ≈20s 返回，`race_window=30s` 本来就够接住——之前的"race_window 太短 / Coze 慢"判断是误诊。
- 真瓶颈在 **agent 本地前后处理**：① 发前 `Triage→Route` 串行（Route 可能读 `knowledge/`/`workflows.json`）导致 Coze 晚发；② 收后 `--collect` 命中后 agent 做 re-synthesis / 重排 / 加本地引用，不是 verbatim 输出。

### 改动（仅文档，零 Python 代码）
- **SKILL.md / steps.md**：Race 路径 `0→1→2→3→7` → `0→2→1→3→7`（fire 前置到 Route 前，Triage 后即发 Coze，T+0 起跑）；新增两条 HARD GATE：① 发前 ONLY 动作是 Triage（禁读 `knowledge/`/`search_refs.py`/`reference-index.md`），② `--collect` 命中后 **post-collect zero-processing**（原样输出 Coze stdout，禁 re-write/re-order/加本地引用/重格式化）。
- **预期效果**：用户总等待从几分钟 → ≈25s（Triage 秒级 + Coze 20s）。
- **实测验证**：真实触发 Coze 两次（冷 19.65s / 温 1.25s），collect 均在 30s 窗口内命中缓存并返回实质性答案；`test_race.py` 留存工作区可复跑。

### 未改动
- Python 代码零改动（路线 A 换模型 / 路线 C 异步两段式经实测证明不需要，避免过度工程）。
- `.clawhubignore` 新增排除 `.coze_race_cache/`（运行期生成的 race 缓存，防污染发布包）。

## 0.9.40 (2026-08-07) — coze 凭据内嵌 + SkillHub 发布修复

### coze 公开凭据内嵌（修复 SkillHub 连不上 coze）
- **问题**：原 coze token 落盘 `config/coze.dat`；SkillHub 窄白名单不含 `.dat`，发布时服务端静默剥离 → 安装环境读不到文件、连不上 coze。
- **修复**：token 改为明文（公共凭据）存进 `config/keys.py` 的 `COZE_TOKEN` 常量；`get_token()` 直接返回常量。新增通用 `get_secret(name, fallback)` / `store_token(plain, path)` 向后兼容。
- **清理**：`adapters/coze_token_embedded.py` 不再被任何代码引用（可保留作历史参考或删除）；`config.json` 移除失效 `token_file` 字段；`skill-publish/SKILL.md` 补 `.dat` 静默剥离说明；规范写入 `ct-base` §7。

## 0.9.37 (2026-08-07) — 难度判定偏置 + 编码策略修正

### 难度判定偏置规则（防误判为 complex）
- **问题**：纯 methodology 问答（如"纸质CRF→EDC 迁移如何保证完整性"）被误判为 `complex`，走 serial 流程（串行等待 Coze 完整返回），比 race 模式慢 30-60s。
- **规则**：当问题**不涉及外部数据拉取 / 样本量计算**时，优先判为 `middle`（race 模式），除非满足以下至少一项：≥2 路 sibling skill 数据 grounding / ct-samplesize 计算 n / 多方案对比推荐 / 跨 ≥3 workflow 复合判断。
- **落点**：`references/steps.md` Step 0 新增"难度判定偏置规则"段；`SKILL.md` Performance discipline 段后新增"难度判定偏置规则"摘要。

### 编码策略修正（消除 JSON 解析失败）
- **问题**：`--payload-inline` 模式下 JSON 字符串内部含中文弯引号/中文逗号时，破坏外层引号结构，导致 `JSONDecodeError`；首次调用失败后需二次重试，浪费一轮。
- **规则**：priority 1 改为 stdin 管道（`echo '{…}' | python refine_answer.py`），`--payload-inline` 降级为 priority 2（仅限纯英文 payload）；新增自检规则：调用前扫一眼 JSON，出现中文标点立刻切 stdin。
- **落点**：`SKILL.md` Coze 调用优先级表和编码策略段全面改写。

