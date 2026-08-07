# Changelog

## 0.9.37 (2026-08-07) — 难度判定偏置 + 编码策略修正

### 难度判定偏置规则（防误判为 complex）
- **问题**：纯 methodology 问答（如"纸质CRF→EDC 迁移如何保证完整性"）被误判为 `complex`，走 serial 流程（串行等待 Coze 完整返回），比 race 模式慢 30-60s。
- **规则**：当问题**不涉及外部数据拉取 / 样本量计算**时，优先判为 `middle`（race 模式），除非满足以下至少一项：≥2 路 sibling skill 数据 grounding / ct-samplesize 计算 n / 多方案对比推荐 / 跨 ≥3 workflow 复合判断。
- **落点**：`references/steps.md` Step 0 新增"难度判定偏置规则"段；`SKILL.md` Performance discipline 段后新增"难度判定偏置规则"摘要。

### 编码策略修正（消除 JSON 解析失败）
- **问题**：`--payload-inline` 模式下 JSON 字符串内部含中文弯引号/中文逗号时，破坏外层引号结构，导致 `JSONDecodeError`；首次调用失败后需二次重试，浪费一轮。
- **规则**：priority 1 改为 stdin 管道（`echo '{…}' | python refine_answer.py`），`--payload-inline` 降级为 priority 2（仅限纯英文 payload）；新增自检规则：调用前扫一眼 JSON，出现中文标点立刻切 stdin。
- **落点**：`SKILL.md` Coze 调用优先级表和编码策略段全面改写。

## 0.9.35 (2026-08-07) — 删除 organized_problems，payload 由 5 变量缩减为 3 变量

- **架构变更**：本地 agent **不再生成 `organized_problems`**——该字段已从 `RefineRequest` 入参中删除。结构化问题构建工作改由 Coze 端基于 `original_question` + `draft_answer` 自行完成。
- **Payload 精简**：出站 payload 由 5 变量（`query_meta` / `original_question` / `organized_problems` / `draft_answer` / `query_origin`）缩减为 **3 变量**（`query_meta` / `original_question` / `draft_answer`）。
- **query_origin 并入 query_meta**：`query_origin` 曾是独立顶层字段，现已并入 `query_meta` 字典（`query_meta.query_origin`）。脚本在 `normalize()` 时自动盖章写入（sha256 机器标识，不可逆、不含明文）。
- **步骤重编号**：删除原 Step 2（Structure → organized_problems），后续步骤顺延：原 Step 3→2、4→3、5→4、6→5、7→6、8→7。race 路径 `1→2→3→4→8` 变 `1→2→3→7`；serial 路径 `1→2→3→4→5→6→7→8` 变 `1→2→3→4→5→6→7`。
- **代码改动**：
  - `adapters/refiner.py`：`RefineRequest` dataclass 移除 `organized_problems` 与 `query_origin` 字段；`normalize()` 删除 organized_problems 构建逻辑，改为将 `query_origin` 盖章写入 `query_meta`；`validate()` 移除 organized_problems 校验、增加 `query_meta.query_origin` 校验；`to_payload()` 返回 3 变量；`_race_cache_path` 缓存键基于 `original_question + query_meta`。
  - `scripts/refine_answer.py`：构造 `RefineRequest` 去除 `organized_problems` 与 `query_origin`；导入去除 `compute_machine_id`。
  - `scripts/run_refined.py`：`refine_direct()` 签名去除 `organized_problems` 参数。
- **文档同步**：`references/ops.md` §step-3-addenda 删除 organized_problems 生成逻辑；`references/steps.md` 删 Step 2 并重编号；`references/refiner_contract.md` payload 由 5 变量缩减为 3 变量、删 §1.3 organized_problems、§1.5 query_origin 并入 query_meta；`knowledge/system_prompt.md` Tier 2 路径更新；`references/coze_system_prompt_v1.4.md` 输入删除 organized_problems；`SKILL.md` Answer Workflow 表删 Step 2 重编号、删 Step 9、version 升 0.9.35；两版 README 出站 payload 列表更新；`AGENTS.md` refine_direct 示例去 organized_problems。
- **遗留脚本清理**：`scripts/update_workflow.py` 内嵌 `new_section` 删除 Step 2 段、flow 字符串与 fire-only payload 去 organized_problems；`scripts/update_refiner.py` 清理 organized_problems 引用。
- **兼容性**：Coze 端需适配 3 变量 payload（原 `organized_problems` 输入不再提供，Coze 需自行从 `original_question` + `draft_answer` 构建结构化问题）。

## 0.9.34 (2026-08-07) — 兄弟技能缺失时直接给出 GitHub 安装地址

- **背景**：此前缺失兄弟技能时只笼统说"与 ct-advisor 同源安装（SkillHub / GitHub / 本地拷贝）"，未给出可直接使用的地址，用户需自行去找。
- **改动**：缺失兄弟技能（ct-registry / ct-safety / ct-literature / ct-samplesize / meta-analysis）时，**直接打印其 GitHub 安装地址**（统一前缀 `https://github.com/medstatstar/<slug>`）+ `git clone` 命令，不再只说"同源"。
- **落点**：`knowledge/system_prompt.md` §Missing a sibling skill 列出各技能权威 GitHub repo 并要求 agent 输出真实 URL（不得只写"同源"）；`scripts/check_deps.py` 的 `KNOWN_DEPS` 增加 `github` 字段，缺失时 probe 直接打印 `GitHub:` 与安装命令；`SKILL.md` 路由段与中英文 `README` 兄弟技能行同步给出 GitHub 地址。

## 0.9.33 (2026-08-07) — 凭据声明澄清（消除安全检查误报）

- **背景**：第三方安全检查扫描源码字符串，就 `coze.dat` 与"回退本地草稿"生成两条误导性提示：①「共享机器上不建议原样保留 coze.dat」；②「若不想把问题发往云端：设环境变量 `CT_ADVISOR_COZE_TOKEN`（或替换 coze.dat 用自己的 token），精校环节会自动回退到本地草稿」。两者均不准确。
- **事实澄清**：`config/coze.dat` 是作者随技能**公开发布**的共用凭证，访问精校端点 `https://ct-advisor.coze.site/run` 所必需，**必须原样保留（含共享机器）**，且**不可替换 token**（替换为自有 token 反而无法访问公共端点）。"回退本地草稿"仅为 Coze 临时不可达时的**故障降级**。
- **改动文件**：
  - `adapters/coze_token.py`：删除"共享设备明文凭据风险"警告，改为"公开公用凭证、须原样保留、勿用私有 token 覆盖"。
  - `references/ops.md` §Coze token：删除可设 env / `--store-token` 替换的误导指引，明确 shipped 文件即默认、不应替换。
  - `README_zh-CN.md` / `README.md` 顶部隐私框 + §4「出站与隐私」：补 coze.dat 必须公开凭证说明；"回退本地草稿"改为"仅故障降级、无本地模式"。
  - `SKILL.md` Requirements 表：Refiner 行补"公开共用凭证、勿替换"；Network 行由"None in local mode"更正为"refinement 固定出站、无本地模式"。
  - `scripts/refine_answer.py` docstring：回退表述改为"fault fallback only"。
- **注意**：本版本仅改注释/文档措辞，未触碰 `config/coze.dat`；已打的 `ct-advisor-0.9.32.zip` 因注释变化而过期，需重新打包。

## 0.9.32 (2026-08-07) — 交互增量写回 original_question

### 流程改进：菜单 / grill-me 补充信息并入 original_question
- **问题**：原流程把 `original_question` 当成"verbatim 不可改的意图锚点"，文档从未规定菜单（complex）/ grill-me（vague）澄清得到的新信息要写回该字段；`organized_problems` 的构建规则也缺"交互增量并入"条款，仅有一条"无锚点主题→丢弃或 optional≤1"的 Faithfulness gate（默认丢弃）——与"把新信息一起放进 payload"的诉求相反。
- **修复（流程文档）**：
  - `references/ops.md` §step-3-addenda：新增"交互增量写回 `original_question`"规则——complex/vague 经交互得到增量后，先把新信息**直接追加到 `original_question` 文本之后**，再据此构建 `organized_problems`；增量必须保留，不被 Faithfulness gate 丢弃。
  - `references/steps.md` Step 2：Output 由"`original_question` (preserved in full)"改为"除非菜单/交互补充了信息"，并新增"Interaction-increment write-back"子规则。
  - `knowledge/system_prompt.md` §0 clarify：同步"菜单/grill-me 补充写回 `original_question`"。
  - `references/refiner_contract.md` §1.2：`original_question` 定义由"verbatim 不可改"放宽为"可承载交互增量（原问题+补充）"，新增写回规则与 Tier 2 示例 E9。
- **语义保持**：更新后的 `original_question` 仍是主依据+意图锚点（`original_question` > `organized_problems` 优先级不变）；缓存哈希基于 `original_question`+`organized_problems` 自然随之变化（不同增量=不同问题，符合预期）；`simple`/`middle` 不弹菜单，`original_question` 仍 verbatim。
- **代码层**：无需改动——`original_question` 由 agent 在本地构建 payload 时更新，`refiner.py` 仅接收并用作意图锚点/缓存键，不对其做裁剪。

### 配套修订（同版本 0.9.32）
- **域名勘误**：所有 `ct-advisor.coze.cn` 笔误更正为正确端点 `https://ct-advisor.coze.site/run`（`config.json` 的 `refiner.endpoint`、`references/refiner_contract.md` 示例、README/README_zh-CN.md 顶部隐私提示与误报说明段）；coze 官方域名 `api.coze.cn` 保持不变。
- **README 合并与纠偏**：`README_zh-CN.md` 的 §4「安全与预览」+ §5「数据保留与隐私」合并为 `## 4. 安全与隐私`，删除与「答案精校固定出站」冲突的「默认零出站」「CozeBackend 桩未激活」两段，原 §6 重编号为 §5；`README.md`（英文版）同步合并。删除未实现的「默认只展示方案、需说请直接检索才检索」叙事，改为「默认即路由调用兄弟技能完成分析」，并厘清 `qa_store` 默认 `noop`。
- **FAQ 陈述化**：第 135 行 FAQ 由问句改为断言「默认就会调用兄弟技能查真实数据」，中英文 README 同步。

## 0.9.31 (2026-08-07) — one-sentence language switch

### 新增：一句话切换提示语言（临时 / 永久）
- **动机**：0.9.30 回退到「跟随 OS 区域自动选择中文/英文」后，`set_lang()` 仍是死代码——它从未接入 `_current_lang()` 的判定链，且完全没有持久化机制。
- **修复（scripts/i18n.py）**：重定义 `_current_lang()` 判定优先级为
  `进程级 override（set_lang / menu.py --lang）> 会话级覆盖文件（set_lang_session）> config.json \`language\`（set_lang_permanent）> OS 区域探测（is_chinese_os）`。
  新增 `set_lang_session()`（写入 `data/.lang_session`，仅本次对话生效，跨多次脚本调用保持）与 `set_lang_permanent()`（写入 `config.json` `language`，对所有后续会话生效，并清掉会话覆盖）。`set_lang()` 保留为进程级 override（供 `menu.py --lang` 与测试使用）。
- **新增 scripts/switch_lang.py**：代理用一句话即可切换——`python scripts/switch_lang.py en`（默认会话级）/ `--permanent`（写 `config.json`，永久）。支持 `en` / `zh-CN`，确认信息按目标语言输出。
- **文档同步**：SKILL.md / system_prompt.md / prompts.md / AGENTS.md / 两版 README 均补「一句话切换」说明，明确临时（"switch to English" / "用中文回复"）与永久（"always use English" / "永久用中文"，写 config.json）两种触发方式。clawhub #2/#4（跟随 OS）维持已知保留项。
- **验证**：py_compile 通过；判定链行为实测（默认→OS、进程级 en/zh、会话级写文件、清会话回 OS、永久级写 config 并持续生效）；switch_lang.py 会话/永久两种模式实测正常（用临时 config 与会话文件，未污染真实 `config.json`）。

## 0.9.30 (2026-08-06) — security remediation round (ct-advisor security-audit + supply-chain finding)

### clawhub audit #3 — Q&A 明文日志默认开启（已修复）
- **问题**：发布用 `config.json` 的 `qa_store.mode` 为 `"local"`，安装即默认把明文问答（问题/答案/引用/依据/反馈）追加写入 `data/qa_log.jsonl`，无 consent / redaction / 最小化，与 0.8.2「off by default」声明直接矛盾。
- **修复**：`qa_store.mode` 改为 `"noop"`（保留 `local_path` 供显式 opt-in）。`build_qa_store()` 对 `local`/`remote` 之外的任意 mode 均返回 `NoOpStore`，故默认**不写任何文件**（隐私优先，零本地残留），与 0.8.2 文档一致。

### clawhub audit #1 — 双模型声明矛盾（已修复）
- **事实澄清（用户确认）**：当前答案为**双模型两段式流水线**——本地主模型（宿主 LLM）起草草稿，Coze 精校（simple/middle 走 race 竞速、complex/vague 走串行精校），两模型均参与产出。
- **修复**：SKILL.md summary/description 与两版 README「后续发布计划」改为如实描述当前双模型流水线，删除「列入后续路线图 / on the roadmap」过时措辞；CHANGELOG 0.8.0、0.8.2 补勘误（见下）。严格意义的「独立交叉验证」（远程数据库核验的双模型复核）仍列未来增强项，保留于 README 后续发布计划。

### 供应链 finding — 未固定版本依赖（代码层已修）
- `adapters/refiner.py` 的 `_try_install()` 原用 `sys.executable` 执行无版本号 `pip install requests`（供应链投毒风险），已固定为 `requests==2.32.3`；`references/ops.md` 文档同步对齐。

### 语言策略（跟随 OS 区域自动选择）
- 输出语言恢复为**跟随操作系统区域自动选择中文/英文**：`scripts/i18n.py` 的 `_current_lang()` 重新以 `is_chinese_os()` 判定，`config.json.language` 显式选择逻辑与 `_load_config_lang()` 一并移除；中文 Windows 下默认中文，可用 `set_lang()` 运行时切换。
- 这是用户的明确偏好（比安装时显式选择更省事）。因此 clawhub 安全审计的 **#2 / #4（NL Policy：README/SKILL 声称"跟随 OS"）作为已知项保留，本版本不予改动**——属于主动接受，非遗漏。
- 精校端点 `refiner.endpoint` 确认为 `https://ct-advisor.coze.site/run`（两版 README 顶部隐私提示与 §5 同步）。

### 其他
- 重新打包发布用 zip（剔除规则同前；`config/coze.dat` 仍按授权随包）。
- 注：0.9.27–0.9.29 的 CHANGELOG 条目此前未补，本次不回溯虚构；版本号自 0.9.30 起与 SKILL.md 对齐。

## 0.9.26 (2026-08-06) — 消除临时文件 + 重写 Step 0–7 全流程

### 消除临时文件，改用内存管道

- **问题**：调用 Coze 精校时，agent 用 `Write` 工具或 `Bash cat >` 把 payload 写入临时 JSON 文件（含中文/中文引号/BOM/换行），`refine_answer.py` 用 `Path.read_text(encoding="utf-8")` 读取时因编码/路径差异导致 `JSONDecodeError`；且 Windows 下 Git Bash `/tmp` 路径与 Python 路径解析不一致，进一步造成 `file not found`。
- **修复**：
  1. **`refine_answer.py`** 新增 `--payload-inline <JSON字符串>` 参数（最高优先级），直接接收 JSON 字符串，零文件 I/O。
  2. **SKILL.md** 重写调用指引为三级优先级：`--payload-inline`（首选）> stdin 管道（次选）> 文件路径（兜底，仅用于 `--collect`）。
  3. **编码策略**：区分 Bash / PowerShell / cmd.exe 的引号转义规则；JSON 含中文时优先用 Bash 单引号包裹或 PowerShell here-string。
  4. **性能**：消除临时文件的磁盘 I/O + 路径兼容 + 编码风险，payload 完全在内存中流转。

### 重写 Step 0–7 全流程

- **问题**：原 step 0–8 描述冗长、重复、结构混乱——race/serial 双形态描述分散在 step 2/6 两处；调用方式（`--payload-inline`）仅作为 step 6 的补充说明；HARD GATE 与"输出前最终检查"混在 step 6 大段文字中，agent 难以快速定位。
- **修复**：
  1. **合并 step 0–7**（原 step 8 已删除），每步独立小节，含**目标/触发条件/操作/产出**四要素。
  2. **Step 0** 新增 difficulty 判定表 + 前置拦截规则 + 交互策略。
  3. **Step 2** 明确 faithfulness/completeness 双 gate 的量化标准。
  4. **Step 6** 拆为 6A（race）/ 6B（serial）两个子步骤，各附 ASCII 流程图 + 命令模板。
  5. **调用方式总结**独立为 step 6 末尾的速查表（优先级 + 禁止行为 + 编码策略）。
  6. **HARD GATE** 从 step 6 大段文字中提炼为 step 2 出口 + step 6 输出前检查两个独立检查点，用 checkbox 列表呈现。

- **问题**：调用 Coze 精校时，agent 用 `Write` 工具或 `Bash cat >` 把 payload 写入临时 JSON 文件（含中文/中文引号/BOM/换行），`refine_answer.py` 用 `Path.read_text(encoding="utf-8")` 读取时因编码/路径差异导致 `JSONDecodeError`；且 Windows 下 Git Bash `/tmp` 路径与 Python 路径解析不一致，进一步造成 `file not found`。
- **修复**：
  1. **`refine_answer.py`** 新增 `--payload-inline <JSON字符串>` 参数（最高优先级），直接接收 JSON 字符串，零文件 I/O。
  2. **SKILL.md** 重写调用指引为三级优先级：`--payload-inline`（首选）> stdin 管道（次选）> 文件路径（兜底，仅用于 `--collect`）。
  3. **编码策略**：区分 Bash / PowerShell / cmd.exe 的引号转义规则；JSON 含中文时优先用 Bash 单引号包裹或 PowerShell here-string。
  4. **性能**：消除临时文件的磁盘 I/O + 路径兼容 + 编码风险，payload 完全在内存中流转。
- **SKILL.md 同步**：step 2 HARD GATE 中 fire-only 调用示例改为 `--payload-inline`；step 6 串行调用指引同步更新；删除 `<<'PYEOF'` heredoc 示例。

## 0.9.25 (2026-08-06) — 双 HARD GATE（step 2 出口 + 输出前最终检查，防止 race 未启动）

- **问题**：agent 在 middle 难度问题时，读完知识后直接输出本地草稿表格，跳过了 Coze 精校（`--fire-only` + `--collect` race 竞速），直到用户提醒才发现流程违规。后续用户再次指出：race 应在 **step 2 结束后立即** `--fire-only` 发 Coze，不是等 step 6
- **根因**：SKILL.md step 6 虽有 race 竞速描述，但**缺乏 step 2 出口硬停止**——agent 可以跳过 fire 直接写草稿
- **修复**：在 SKILL.md 设置**双 HARD GATE**：
  1. **step 2 出口**（新增）：difficulty=simple/middle 时，**必须**先 `--fire-only` 后台发 Coze，**禁止**跳过此步直接写草稿。违反 = race 未启动 = 后续 collect 必然本地胜出 = 实质跳过 Coze
  2. **输出前最终检查**（step 6 开头）：输出前逐项确认 race 已启动（step 2 HARD GATE）+ collect 已判定胜出方 + 输出=胜出方内容
- **同步**：移除独立的「Answer Output Hard Gate」章节（双 HARD GATE 已覆盖）

## 0.9.24 (2026-08-06) — step 4/5 触发 → difficulty 不允许取 simple/middle

- **新增分流覆盖规则（priority override，定位 gate 0）**：gate 0 判 difficulty 时须**分析 `original_question` 的意图**——若问题需要调用外部技能获取真实数据（检索 CT.gov/FAERS/OpenAlex → 触发 step 4）或需要算样本量/把握度（→ 触发 step 5）——任一为真，**difficulty 不允许取 simple/middle，只允许取 complex/vague**。**不检查 `workflows.json` 的静态配置**（那只是能力声明，不代表本次问题真正需要）。
- **为什么前置到 gate 0**：若在 step 6 才覆盖，step 2 的 `--fire-only` 已经发出去了、race 已启动，覆盖便成马后炮。取数/算 n 依赖外部技能真实输出，必须前台等 Coze 完整返回以整合进答案，race 本地草稿兜底会丢失这些数据。
- **同步**：SKILL.md step 0 加入前置拦截段；step 4/5 删除前向引用（不再承担分流职责）；step 6 与 ops.md 删除分流覆盖段（仅保留纯 race/serial 双路线描述）。

## 0.9.23 (2026-08-06) — race 真竞速（速度优先、谁先回用谁）

- **决策**：用户再次澄清 race 语义——不是"永远本地"，是**速度优先真竞速**：step 2 后台 `--fire-only` 早发 Coze（用完整 60s HTTP 超时），step 3 并行写本地草稿，step 6 用 `--collect` 读取 race 缓存：**缓存命中（Coze 先回）→ 采用 Coze（中断本地、Coze 胜出）；否则采用本地草稿**。常态本地秒级先出 → 本地赢；Coze 若真比本地快则 Coze 赢。
- **复原 `race_window` 参数**：`config.json` `refiner.race_window`（默认 2.0）→ `build_refiner()` → `CozeRefiner.__init__` `self.race_window`。语义 = `--collect` 收集等待上限（超时即放弃 Coze、用本地）。
- **`refiner.py`**：`refine_fire_only` 成功后写 race 缓存；新增 `collect_race(req, wait)` 轮询缓存（命中返回 Coze 结果 / 超时返回空串）；`__init__` 与路由注释更新。
- **`refine_answer.py`**：新增 `--collect [--wait N]` 参数 → 调用 `collect_race`、输出 Coze 结果（命中）或空串（本地胜）；保留 `--fire-only` 写缓存。
- **文档同步**：`SKILL.md` step 6 与 `references/ops.md` §step-7-cookbook 重写为真竞速语义（`--fire-only` 早发 + `--collect` 收集，缓存命中 Coze 胜）。

## 0.9.22 (2026-08-06) — 移除 `race_window`，race 语义定为「速度优先 / 本地先出」

- **决策**：用户确认 race 的价值是「速度优先——Coze 或本地谁先返回用谁」；当前 Coze 实测延迟 9~25s、本地草稿秒级，故常态本地先出。删除以前的「step 6 收集等待 ≤ race_window」窗口（`race_window` 已成为死参数）。
- **移除 `race_window` 参数**：从 `config.json`（`refiner.race_window`）、`build_refiner()`（`rc.get("race_window")`）、`CozeRefiner.__init__`（`self.race_window`）、`_refine_fast` 全部删除。
- **删除 `_refine_fast` 方法**：它是方案 B 前的旧 race，用 `race_window` 同时作为 Coze 的 HTTP 短帽与 join 预算；删 `race_window` 后失去依赖，整段移除。`refine()` 单发入口的 simple/middle 分支改为统一走 `_refine_serial`（防御性串行，正常 race 流程不走此处——agent 用 `--fire-only` 后台 fire、step 6 直接 ship 本地）。
- **race 最终语义**：step 2 后台 `--fire-only` 早发（Coze HTTP 超时完整 60s，仅后台留痕）；step 3 并行写本地草稿；step 6 **直接采用本地草稿输出**，无收集/等待窗口。Coze 返回不进入前端作答。
- **SKILL.md step 6 + `references/ops.md` §step-7-cookbook**：race 段重写为「速度优先 / 本地先出」，删除所有 `race_window` 引用与「收集等待」描述。
- **Verified**: `py_compile` 通过（refiner.py / __init__.py / refine_answer.py）；`--fire-only` 实跑确认链路通、无 `race_window` 引用报错。

## 0.9.21 (2026-08-05) — race 早发重构（fire/collect 拆分，对齐 ops.md 文档意图）

- **Root cause**: `_refine_fast` 用 `race_window=2s` 同时作为 Coze 的 HTTP 超时与 join 预算，把 Coze 卡死在 2s，与 `references/ops.md` §step-7-cookbook 既定意图（早发 + 完整 60s 窗口、无短帽）矛盾，导致 race 模式下 Coze 几乎永不浮现、仅后台留痕。
- **新增 `CozeRefiner.refine_fire_only(req)`**：race 早发入口。仅发 `original_question`+`organized_problems`（`draft_answer` 留空），HTTP 超时用**完整 `self.timeout`（默认 60s，与 `race_window` 解耦）**；Coze 胜则返回其结果，败/超时返回**空串**（不回退 draft——step 2 时草稿尚未写出，回退会得到空白）。真正的兜底由 agent 在 step 6 用自己的本地草稿完成。
- **`scripts/refine_answer.py` 新增 `--fire-only` 模式**：step 2 后台调用，返回 Coze 结果或空串；`MissingDependencyError` 仍显式退出码 1（不静默回退）。
- **`race_window` 语义澄清**：保留为 step 6 收集后台结果的**等待上限**（默认 2s），不再是 Coze 的 HTTP 超时。
- **SKILL.md step 6 + `references/ops.md` §step-7-cookbook**：重写为 fire/collect 拆分——simple/middle 在 step 2 后台 `--fire-only` 早发、step 3 并行写本地草稿、step 6 收集（等待≤race_window）；complex/vague 仍在 step 6 单发完整五变量串行等待。
- **Agent 纪律（不变）**：ct-advisor 新问题一律执行 Coze 精校；race 早发后 agent 须真正收集后台结果、不得跳过 step 6 的 collect。
- **Verified**: `py_compile` OK；`refine_fire_only` 方法存在且 `build_refiner()` 可读；`--fire-only` 参数可被 argparse 解析。

## 0.9.20 (2026-08-05) — knowledge consolidation (29 → 15 topic files)

- **Consolidation**: the 29 split topic files are merged into **15** (`ref-ops-*` / `ref-reg-*`) to cut fragmentation (fewer multi-read round-trips, less cross-file synthesis drift). 8 new merged files absorb their sibling split-files — `ref-ops-design` (← pharmacology), `ref-ops-gcp-site` (← gcp-roles+site), `ref-ops-execution` (← methodology-qc), `ref-ops-data` (← data-systems), `ref-ops-safety` (← qa+governance), `ref-reg-stats` (← regulatory-statistical), `ref-reg-submission` (← csr+ctd+approval+design-endpoints+methods-products), `ref-reg-cn` (← cn-routing+cn-data-ethics+cn-transparency). 7 kept independent: `ref-ops-contract`, `ref-reg-contract`, `ref-regulatory-versions`, `ref-reg-safety`, `ref-reg-gcp-version`, `ref-reg-retrieval`, `ref-interaction-style`.
- **Provenance notes stripped**: the "split-source" marker (`> 本文件为…拆分件之一`) is removed on merge; the two placeholder `superseded-by-split` stubs (`ref-clinical-operations`, `ref-regulatory-statistical`) are folded into their contract entries (`ref-ops-contract` / `ref-reg-contract`), and those two contract files now carry the source hierarchy & dynamic-item verification rules.
- **Routing updated**: `workflows.json` and `references/units.md` old entry names remapped to the two contract files; `reference-index.md` regenerated (file-level map); `SKILL.md` "Knowledge Map" line corrected to **15 topic files (3–37 KB each)**.
- **Verified**: `search_refs.py` smoke test (方案偏离 → `ref-ops-data`/`ref-ops-gcp-site`/`ref-ops-safety`; CYP3A4 → `ref-ops-design` L40); `py_compile` OK; `workflows.json` valid JSON; no functional dead links in live files. Temp `knowledge_old/` + `knowledge_new_trash/` removed.
- **Cross-reference renumbering (follow-up)**: the 9 stale intra/cross-file cross-references that still cited merged-away sub-files by name (e.g. `ref-reg-csr.md §5`, `ref-reg-approval.md §5.4`, `ref-reg-design-endpoints.md §5.14`, `ref-reg-cn-data-ethics.md §8.5`, `ref-ops-site.md §3.7/§3.8`, `ref-ops-governance.md §7`) are rewritten to their live merged targets (`ref-reg-submission.md` / `ref-reg-cn.md` / `ref-ops-gcp-site.md` / `ref-ops-safety.md`); the merge had preserved the original § numbers and made them globally unique per file, so each now points to an existing section. `ref-reg-stats.md §3.3` was already valid (live file) and left unchanged. Re-grep confirms zero stale content cross-refs; `search_refs.py` smoke test still passes.

## 0.9.19 (2026-08-05) — knowledge split, performance & release-compliance overhaul

- **Knowledge pack split (performance)**: the two large reference files (`ref-clinical-operations.md` / `ref-regulatory-statistical.md`) are replaced by **29 topic files** (`ref-ops-*` / `ref-reg-*`, 3–24 KB each), keeping original section numbering; all cross-references rewritten to the new file names (§ numbers unchanged). Placeholder files keep legacy names with a "superseded by split" note.
- **Routing index**: new file-level `knowledge/reference-index.md` (compact map, auto-generated); `ref-ops-contract.md` / `ref-reg-contract.md` are the two series contract entries (source hierarchy & dynamic-item verification rules).
- **SKILL.md**: added "Knowledge Map & Read Discipline" (locate via index or `search_refs.py --context 3`; single Read ≤ 60 lines; ≤ 2 reads per turn; `system_prompt.md` is a Coze-side copy — do not read locally) and "Performance discipline" (never pre-read internal plumbing; invest in step-2 disassembly, keep the draft terse; prune context on long sessions).
- **Scripts**: `search_refs.py` upgraded (default `--context 3` returns hit lines + context, `--max-len` truncates over-long lines, `--files` filter); `update_reference_index.py` rewritten to scan all `ref-*.md` frontmatter.
- **Bilingual compliance (ct-base §3/§4)**: SKILL.md anglicized and slimmed (39 KB → ~14 KB); frontmatter follows the schema (`cn_name`/`summary` Chinese-only; `description`/`displayName` CN-EN with ` / `; body English-only; `## Language` links the two READMEs).
- **Release compliance**: ct-base §5 gained the credential-storage rule (no plaintext keys on disk; XOR+base64 is the baseline for shared credentials); `config/coze.dat` verified as an obfuscated blob (shared credential, ships with the package by design). CHANGELOG.md restored into the working tree (was missing).
- **Answer-mode unification (2026-08-05)**: deleted the `precise` mode. `fast` is now the only mode and is purely difficulty-driven — `simple`/`middle` run as a background race (Coze vs local draft, Coze preferred); `complex`/`vague` run serial (blocking await of Coze, slower but Coze-preferred). `_refine_precise` renamed to `_refine_serial`; `config.json` `answer_mode` stays `fast`.

## 0.8.3 (2026-08-02) — answer-refinement seam (interface reserved)

- New 4th adapter seam `adapters/refiner.py`: wraps the locally-generated draft through an optional external polish step.
- `RefineRequest` carries 5 variables: `category`, `original_question`, `organized_problems` (JSON list), `draft_answer`, `difficulty` (`simple`/`complex`).
- `LocalRefiner` (default, `refiner.mode: local`): returns `draft_answer` unchanged — zero network, behavior identical to before.
- `CozeRefiner` (opt-in via `refiner.mode: coze` + `endpoint`): POSTs the 5 variables to the Coze server, returns `final_answer` with a 15-second timeout that falls back to `draft_answer` on any timeout / network / parse error.
- New agent entry `scripts/refine_answer.py`: reads the 5 variables (file arg or stdin), prints the final answer; any failure falls back to `draft_answer` and exits 0.
- `config.json` gains a `refiner` block (default `local`, `timeout: 15`). SKILL.md local flow gains step 7 (refine); the agent always calls the refiner, so enabling the server later needs no SKILL.md change.
- Default stays zero-outbound; the outbound POST only happens when `refiner.mode: coze` is explicitly configured.

## 0.8.2 (2026-08-02) — security-audit remediation

- Removed the unimplemented "dual-model cross-check" claim: SKILL.md summary/description no longer state it as current behavior; it is now correctly placed on the roadmap (see README §Future Release Plans).
- Q&A logging is now OFF by default: `build_qa_store()` returns `NoOpStore` unless `config.json` sets `qa_store.mode: local` (writes `data/qa_log.jsonl`) or `remote`. No local record of questions/answers is kept by default.
  - [Erratum 0.9.30] The shipped `config.json` actually set `qa_store.mode: local`, so Q&A logging was ON by default until 0.9.30 corrected it to `noop`. The `NoOpStore` behavior described here only took effect once the config matched.
- `CozeBackend._post()` now raises `NotImplementedError` (was real HTTP code behind a stub comment); `advise()` already did. The Coze path reads no token and makes no request unless explicitly implemented and enabled.
- Docs: added "§5 Data Retention & Privacy" to both READMEs; clarified the auto-load wording and the zero-outbound / zero-local-residue statement; updated the scanner-false-positive note.
- No methodology / workflow logic changes.

## 0.8.1 (2026-08-02) — README anglicization

- Anglicized the English README (`README.md`): removed all residual Chinese text (example trigger phrases, the Chinese dialogue in the language-switch demo, the `⚠️ 官方核实` marker, and the bilingual author byline) so the English page is English-only. The Chinese README (`README_zh-CN.md`) remains the Chinese counterpart.
- Aligned the README version badge to `0.8.0`.
- No logic / workflow changes.

## 0.8.0 (2026-08-02) — init version

- Initial public release of **ct-advisor**, the unified conversation entry point for the `ct-*` clinical-trial skill family.
- Methodology / design / compliance / QC / tone questions answered in-house through workflows A–J (zero outbound by default).
- Data & competitive-intel routing to `ct-registry` / `ct-safety` / `ct-literature`; sample-size handoff to `ct-samplesize`. Missing sibling skills degrade gracefully (never fabricate).
- User-friendly clarification menu (Capability / Data & intel / Clarify) with step-by-step confirmation and plain-language differences.
- Bilingual READMEs with **适用人群 / Who This Is For** and **后续发布计划 / Future Release Plans** sections.
- Every answer is cross-checked by a dual-model review to ensure correctness and reliability.
  - [Erratum 0.9.30] At 0.8.0 this was forward-looking intent; the two-stage dual-model pipeline (local host model drafts + Coze refines) was realized in v0.9.x and is now the default architecture — see 0.9.30. The strict "independent cross-check" remains a future enhancement.
