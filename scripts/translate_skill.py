"""Temporary script to translate SKILL.md from Chinese to English."""
import os

SKILL_MD = os.path.join(os.path.dirname(__file__), '..', 'SKILL.md')

with open(SKILL_MD, 'r', encoding='utf-8') as f:
    content = f.read()

# Translate workflow principle
content = content.replace(
    '> **核心原则**：payload 全程走内存管道（`--payload-inline` 或 stdin），**禁止** Write/Bash 写临时 JSON 文件。',
    '> **Core principle**: payload stays in-memory pipeline throughout (`--payload-inline` or stdin), **prohibit** Write/Bash temporary JSON files.'
)

# Translate step table headers
content = content.replace('| Step | 职责 | Race(simple/middle) | Serial(complex/vague) |',
                          '| Step | Responsibility | Race(simple/middle) | Serial(complex/vague) |')

# Translate step 0
content = content.replace('| **0 分诊** | 判 difficulty + 前置拦截 | → 1→2→3→4→8 | → 1→2→3→4→5→6→7→8 |',
                          '| **0 Triage** | Judge difficulty + pre-intercept | → 1→2→3→4→8 | → 1→2→3→4→5→6→7→8 |')

# Translate step 1
content = content.replace('| **1 路由** | 匹配 workflow A–J | 同左 | 同左 |',
                          '| **1 Route** | Match workflow A–J | same | same |')

# Translate step 2
content = content.replace('| **2 拆解** | ≤7 子问题（simple/middle 不拆解） | 同左 | 同左 |',
                          '| **2 Disassemble** | ≤7 sub-questions (simple/middle skip) | same | same |')

# Translate step 3
content = content.replace('| **3 Fire Gate** | **🔴 HARD GATE: difficulty = simple/middle 时必须后台发射 Coze** | 立即 fire-only | 不发射，等 step 7 |',
                          '| **3 Fire Gate** | **🔴 HARD GATE: when difficulty = simple/middle, MUST fire Coze in background** | fire-only immediately | skip, wait for step 7 |')

# Translate step 4
content = content.replace('| **4 本地答案** | 写答案 + race 收集 | --collect 竞速 → 8 | 写答案 → 5/6→7 |',
                          '| **4 Local Answer** | Write answer + race collect | --collect race → 8 | Write answer → 5/6→7 |')

# Translate step 5
content = content.replace('| **5 外部取数1** | 读兄弟技能真实数据 | 按需 | 按需 |',
                          '| **5 External Data 1** | Read real data from sibling skills | as needed | as needed |')

# Translate step 6
content = content.replace('| **6 外部取数2** | 参数框架交 ct-samplesize | 按需 | 按需 |',
                          '| **6 External Data 2** | Hand off parameter framework to ct-samplesize | as needed | as needed |')

# Translate step 7
content = content.replace('| **7 串行精校** | Coze 精校（前台等待） | — | 前台等 Coze |',
                          '| **7 Serial Refine** | Coze refine (foreground wait) | — | foreground wait Coze |')

# Translate step 8
content = content.replace('| **8 最终答案** | 直接返回结果 | 来自 step 4 | 来自 step 7 |',
                          '| **8 Final Answer** | Return result directly | from step 4 | from step 7 |')

with open(SKILL_MD, 'w', encoding='utf-8') as f:
    f.write(content)

print('done')
