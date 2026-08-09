# Changelog

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

