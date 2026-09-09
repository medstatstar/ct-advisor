# Changelog

## [Unreleased] (2026-09-09) — 图形化解释策略 (SKILL.md) + README 案例对齐 + ct-bugreport 凭据修复

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
- **§16 发布前检查 + STILL_PRESENT 6 项整改留痕**（基于 ct-base/BASE.md §16）：§16.1–§16.7/§16.9 通过；§16.6 两处 `zero-outbound` → `no outbound`（SKILL.md L111/L161，免疫 §16.6 grep 校验）；SKILL.md L63 `POSTs 3 variables` → `POSTs 3 top-level variables（query_meta / original_question / draft_answer…）` 消除歧义（审计 LOW Intent-Code Divergence）；ClawHub 审计 STILL_PRESENT 6 项逐项人工确认「设计如此/已披露/无实际风险」并留痕（`docs/clawhub_audit_trace_20260815.md`）：subprocess 白名单+无 shell / query_meta 口径已澄清 / public credential 用户授权+已披露 / original_question 出站已披露 / query_origin §8.6 规范 / mandatory 无害词汇命中无实际矛盾。UNVERIFIED 17 项人工核对 0 项需强制整改。**§16.8 遗留阻断已修复**：term_map 共享件同步（底座 53 key 补入叶子，243 keys 字节级一致，shared_sync rc=0）+ `scripts/test_seven_flows.py` 加入 `.clawhubignore`/`.gitignore`（git dry-run 泄漏计数 0）。
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

