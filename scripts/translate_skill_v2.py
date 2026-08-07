"""Temporary script to translate remaining Chinese in SKILL.md to English."""
import os

SKILL_MD = os.path.join(os.path.dirname(__file__), '..', 'SKILL.md')

with open(SKILL_MD, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix rule 6 (External search fallback) - still Chinese
old_6 = '6. **External search fallback**：当 `knowledge/` 检索无命中且 Coze 精校后仍缺乏依据时，按 workflow 分类输出 `references/search-sites.md` 中的权威网站清单，引导用户自行查阅。**禁止**：代替用户访问网站、编造网站内容、输出无关网站。'
new_6 = '6. **External search fallback**: When `knowledge/` search yields no hits AND Coze refinement still lacks grounding, output the authoritative site list from `references/search-sites.md` categorized by workflow, directing the user to consult themselves. **Prohibited**: visiting sites on behalf of the user, fabricating site content, outputting irrelevant sites.'
content = content.replace(old_6, new_6)

# 2. Command template table headers and rows
content = content.replace(
    '| 优先级 | 方式 | 命令模板 | 何时用 |',
    '| Priority | Method | Command Template | When to Use |'
)
content = content.replace(
    '| **1（首选）** | `--payload-inline` | `python refine_answer.py --payload-inline \'{…}\'` | **所有** fire-only 与串行调用 |',
    '| **1 (preferred)** | `--payload-inline` | `python refine_answer.py --payload-inline \'{…}\'` | **All** fire-only & serial calls |'
)
content = content.replace(
    '| **2** | stdin 管道 | `echo \'{…}\' \\| python refine_answer.py` | 串行且 payload 较长时 |',
    '| **2** | stdin pipe | `echo \'{…}\' \\| python refine_answer.py` | Serial with longer payload |'
)
content = content.replace(
    '| **3（兜底）** | 文件路径 | `python refine_answer.py /path/to/file.json` | **仅** `--collect`（向后兼容） |',
    '| **3 (fallback)** | file path | `python refine_answer.py /path/to/file.json` | **Only** `--collect` (backward compat) |'
)

# 3. Prohibition section
content = content.replace(
    '**禁止**：\n- ❌ `Write`/`Bash cat >` 写临时 JSON 文件（编码风险：中文引号/BOM/换行）\n- ❌ `/tmp` 路径（Windows 下 Git Bash ↔ Python 路径不一致）\n- ❌ fire-only/串行时使用文件路径（完全没必要）',
    '**Prohibited**:\n- ❌ `Write`/`Bash cat >` temporary JSON files (encoding risk: Chinese quotes/BOM/newlines)\n- ❌ `/tmp` paths (Windows Git Bash ↔ Python path mismatch)\n- ❌ file path for fire-only/serial (unnecessary)'
)

# 4. Encoding strategy section
content = content.replace(
    '**编码策略（`--payload-inline` 时）**：\n- **Bash / Git Bash**：JSON 用**单引号**包裹（\'`{"key":"中文"}\'`），内部双引号**不转义**\n- **PowerShell**：JSON 用**双引号**包裹 + `"` 转义；或用 here-string `@\'…\'@`（无需转义）\n- **cmd.exe**：同 PowerShell',
    '**Encoding strategy (when using `--payload-inline`)**:\n- **Bash / Git Bash**: Wrap JSON in **single quotes** (`\'{"key":"中文"}\'`), inner double quotes **unescaped**\n- **PowerShell**: Wrap JSON in **double quotes** + escape `"`; or use here-string `@\'…\'@` (no escaping needed)\n- **cmd.exe**: Same as PowerShell'
)

# 5. Step 9 section
content = content.replace(
    '### Step 9 — 持久化（Persist，按需）\n**目标**：仅在用户明确要求记住某项偏好/决策时，调用 WorkBuddy memory 机制显式保存。不创建文件，不调用 `qa_store.py`。',
    '### Step 9 — Persist (on demand)\n**Goal**: Only when the user explicitly asks to remember a preference/decision, invoke the WorkBuddy memory mechanism to save. No file creation, no `qa_store.py` calls.'
)

# 6. Search backoff strategy
content = content.replace(
    '- **搜索退避策略**：`search_refs.py` 命中为 0 时，**禁止换词穷举**（历史实测 14 次搜索 12 次无结果，浪费 ~2 分钟）。正确退避路径：① 首次 no match → 换**语义等价词**（非近义词）重试 1 次；② 仍 no match → 立即转 Read `reference-index.md` 定位目标文件 → Read 目标文件（≤60行）。知识库大量使用"同词不同表述"（如"窗口期"在文件中写作"访视窗口"或仅描述性段落），行级精确匹配命中率有限，路由表 + 直接 Read 是更可靠的定位方式。',
    '- **Search backoff strategy**: When `search_refs.py` returns 0 hits, **prohibit word-switching exhaustion** (historical data: 14 searches with 12 no-results, wasting ~2 minutes). Correct backoff path: ① First no match → switch to **semantically equivalent term** (not near-synonym) and retry once; ② Still no match → immediately switch to Read `reference-index.md` to locate target file → Read target file (≤60 lines). The knowledge base has many "same-concept-different-expression" cases (e.g., "window period" appears in files as "visit window" or only in descriptive paragraphs), line-level exact match hit rate is limited; routing table + direct Read is a more reliable location method.'
)

with open(SKILL_MD, 'w', encoding='utf-8') as f:
    f.write(content)

print('done')
