#!/usr/bin/env python3
"""Update SKILL.md Answer Workflow section from steps 0-7 to steps 0-8."""
import re

with open('SKILL.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the Answer Workflow section boundaries
start_marker = '## Answer Workflow (steps 0–7)'
end_marker = '### Step 7 — 持久化（Persist，按需）'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx < 0:
    print('ERROR: start marker not found')
    exit(1)
if end_idx < 0:
    print('ERROR: end marker not found')
    exit(1)

# Find the end of the Step 7 section (next ## or ### heading or EOF)
rest = content[end_idx + len(end_marker):]
next_section = re.search(r'\n## |\n### ', rest)
if next_section:
    end_of_step7 = end_idx + len(end_marker) + next_section.start()
else:
    end_of_step7 = len(content)

old_section = content[start_idx:end_of_step7]
print(f'Found old section: {start_idx} to {end_of_step7} ({len(old_section)} chars)')

new_section = '''## Answer Workflow (steps 0–8)

> **核心原则**：payload 全程走内存管道（`--payload-inline` 或 stdin），**禁止** Write/Bash 写临时 JSON 文件。

---

### Step 0 — 分诊（Gate 0）
**目标**：判定 difficulty + 前置路由拦截，决定后续路径。

| difficulty | 判定条件 | 后续路径 |
|---|---|---|
| `simple` | 单一事实/定义/标准操作，无需取数/算 n | → step 1→2→3→7（race 竞速） |
| `middle` | 需要解释/对比/多步推理，但无需外部数据 | → step 1→2→3→7（race 竞速） |
| `complex` | 需要多角度拆解、外部数据整合、或方案选择 | → step 1→2→3→4→5→6→7（**串行**，等 Coze 完整返回） |
| `vague` | 问题不完整、有歧义、缺少关键参数 | → AskUserQuestion（1–3 题）→ 回 step 0 |

**⚠️ 前置拦截（强制执行）**：判 difficulty 时须分析 `original_question` 意图——若需调用外部技能取数（ct-registry / ct-safety / ct-literature）或需算样本量/把握度（→ step 6 handoff），**difficulty 不允许取 simple/middle，只允许取 complex/vague**。原因：取数/算 n 依赖外部真实输出，必须前台等 Coze 完整返回以整合进答案；race 本地草稿兜底会丢失这些数据。

**交互策略**：
- `simple` → 直接答，不菜单
- `complex` → 展示澄清菜单（`scripts/menu.json` via `scripts/i18n.py`）
- `vague` → grill-me 式 `AskUserQuestion`（≤ 3 题）
- simple/complex 拿不准时 → 简短直答 + 可选深入菜单

---

### Step 1 — 路由（Route）
**目标**：从 `scripts/workflows.json` 匹配工作流 A–J（或复合路由）。

- 方法论/设计/GCP/合规/QC/统计 → 本地 `knowledge/` 工作流
- 样本量/把握度 → 标记 step 6 handoff 触发
- 注册试验格局/安全性信号/文献 → 标记 step 5 取数触发

---

### Step 2 — 判断发送 Coze（Fire Gate）
**目标**：根据 difficulty 决定是否需要立即后台发射 Coze 精校请求，启动 race 竞速。

| difficulty | 行为 |
|---|---|
| `simple`/`middle` | 🔴 **HARD GATE**：**立即**后台 `run_in_background` 调用 `refine_answer.py --fire-only --payload-inline '{…}'`（仅含 `original_question`（`draft_answer` 留空））。**禁止写临时文件**；**禁止跳过此步直接写草稿**。 |
| `complex`/`vague` | 不发射，等 step 6 串行调用。 |

> **关键**：此步骤是 race 模式的起点。simple/middle 必须在此步发射 fire-only，确保 step 3 写本地草稿时 Coze 已在后台并行运行。

---

### Step 4 — 本地草稿 + Race 收集（Draft & Race Collect）
**目标**：写本地兜底答案，同时收集 Coze 精校结果，竞速胜出方作为本步骤输出。

**Race 模式（simple/middle）**：

```
step 2 已发射 fire-only → Coze 后台运行中
step 3 开始  →  写本地草稿（结论先行 + 法规引用，3-5 行）
               + --collect [--wait N] 读 race 缓存
                ├─ 缓存命中（Coze 先回）→ 采用 Coze（Coze 胜出）→ 跳 step 7
                └─ 超时未回             → 采用本地草稿（本地胜出）→ 跳 step 7
```

- Coze HTTP 超时 = 完整 60s（`refiner.timeout`）
- 收集等待上限 = `refiner.race_window`（默认 2s），超时即放弃 Coze
- **常态**：本地秒级先出 → 本地胜出；Coze 若真比本地快 → Coze 胜出
- **胜出方确定后 → 直接跳 step 7 输出最终答案**

**Serial 模式（complex/vague）**：
- 写本地简洁草稿（结论先行 + 法规引用），不调用 `--collect`
- 草稿将作为 step 6 串行精校的输入

**query_meta 自评**：`accuracy` = `good`（法规引用精确）或 `normal`（泛化回答）。

---

### Step 5 — 外部取数 1（Data Grounding，按需）
**目标**：从外部技能获取真实数据，支撑答案。

**触发条件**：仅当 step 1 标记了取数路由（ct-registry / ct-safety / ct-literature）时执行。

**操作**：
1. 读 sibling-skill 输出（`workflows.json` 中 `integration.data_grounding` 配置）
2. 标注 "Data source: ct-xxx on <date>"
3. 纯方法论问题可跳过（标注 "no data grounding performed"）

**注意**：保持轻量，Coze 会负责扩展和整合。

---

### Step 6 — 外部取数 2 / 样本量交接（Handoff，按需）
**目标**：把完整的参数框架交给 `ct-samplesize`，本技能不算 n。

**触发条件**：step 1 标记了 workflow C 参数就绪。

**Payload**：design type, comparator, test (α/power), effect size, dropout rate.

---

### Step 7 — 外发 Coze 精校（Serial Refine）
**目标**：草稿发送给 Coze 出最终答案（仅 complex/vague 串行执行，step 6）。

**触发条件**：`complex`/`vague` 难度，或 `simple`/`middle` 在 step 4 中 Coze 胜出但需要进一步整合外部数据。

```
step 4 草稿 + step 5/6 外部数据 → 前台串行调用 refine_answer.py（含 draft_answer）
              ├─ Coze 60s 内返回 → 采用 Coze 结果
              └─ Coze 失败/超时  → 回退本地草稿 + 外部数据（FALLBACK_TO_LOCAL_DRAFT）
```

**串行调用方式**（`--payload-inline` 优先）：

```bash
# Bash / Git Bash（JSON 用单引号包裹，内部双引号不转义）
python scripts/refine_answer.py --payload-inline '{"original_question":"…","draft_answer":"…"}'

# PowerShell（JSON 用双引号包裹，内部 \" 转义）
python scripts/refine_answer.py --payload-inline '{\"original_question\":\"…\",\"draft_answer\":\"…\"}'

# PowerShell here-string（推荐，无需转义）
@'
{"original_question":"…","draft_answer":"…"}
'@ | python scripts/refine_answer.py
```

---

### Step 7 — 最终答案（Final Output）
**目标**：将最终答案返回用户。

| 模式 | 来源 |
|---|---|
| Race（simple/middle） | step 3 中先完成的结果（本地草稿 或 Coze 精校） |
| Serial（complex/vague） | step 6 中 Coze 返回结果 或 超时回退本地草稿 |

#### 🔴 **输出前最终检查（HARD GATE）**
输出**任何**答案内容前，逐项确认：

| difficulty | 检查项 |
|---|---|
| `simple`/`middle` | ☐ step 2 已 fire-only → ☐ step 3 已 collect → ☐ 已判定胜出方 → 输出 = 胜出方内容 |
| `complex`/`vague` | ☐ step 6 已前台串行调用 Coze（含 draft_answer）或已超时回退 → 输出 = 胜出方内容 |
| `simple`（会话内澄清） | ☐ step 0 判定 simple + 非新问题 → 直接输出草稿 |

**任一项未勾选 → 禁止输出内容，必须回退补走。**

---

### 🔴 调用方式总结（零临时文件 · 跨平台安全）

| 优先级 | 方式 | 命令模板 | 何时用 |
|---|---|---|---|
| **1（首选）** | `--payload-inline` | `python refine_answer.py --payload-inline '{…}'` | **所有** fire-only 与串行调用 |
| **2** | stdin 管道 | `echo '{…}' \| python refine_answer.py` | 串行且 payload 较长时 |
| **3（兜底）** | 文件路径 | `python refine_answer.py /path/to/file.json` | **仅** `--collect`（向后兼容） |

**禁止**：
- ❌ `Write`/`Bash cat >` 写临时 JSON 文件（编码风险：中文引号/BOM/换行）
- ❌ `/tmp` 路径（Windows 下 Git Bash ↔ Python 路径不一致）
- ❌ fire-only/串行时使用文件路径（完全没必要）

**编码策略（`--payload-inline` 时）**：
- **Bash / Git Bash**：JSON 用**单引号**包裹（`'{"key":"中文"}'`），内部双引号**不转义**
- **PowerShell**：JSON 用**双引号**包裹 + `\"` 转义；或用 here-string `@'…'@`（无需转义）
- **cmd.exe**：同 PowerShell


'''

content = content[:start_idx] + new_section + content[end_of_step7:]

with open('SKILL.md', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'SUCCESS: SKILL.md updated ({len(content)} chars)')
