#!/usr/bin/env python3
"""Update adapters/refiner.py docstring references from old step numbers to new."""
import re

with open('adapters/refiner.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update module docstring (top-level)
old1 = '''不再有「local 精校模式」：答案精校经唯一的 `fast` 模式控制，按难度自动分流——
  simple/middle 走 **race 竞速（早发 / 速度优先）**：agent 在 step 2 后台调用
  `--fire-only`（仅发 difficulty/category/original_question，draft 留空、
  accuracy 空白→normal），Coze 用**完整 60s** HTTP 超时独立分析；成功后写入 race 缓存。
  agent 在 step 3 并行写本地草稿，step 6 用 `--collect` 收集：缓存命中（Coze 先回）→ 采用
  Coze（中断本地）；否则直接采用本地草稿（速度优先——本地秒级先出、Coze 实测 9~25s 慢、
  常态本地胜出）。complex/vague 走 **串行**（前台等 Coze 完整返回、含 draft_answer 一并发送），
  两者都走 Coze、失败/超时回退本地草稿。'''

new1 = '''不再有「local 精校模式」：答案精校经唯一的 `fast` 模式控制，按难度自动分流——
  simple/middle 走 **race 竞速（早发 / 速度优先）**：agent 在 step 3 后台调用
  `--fire-only`（仅发 difficulty/category/original_question，draft 留空、
  accuracy 空白→normal），Coze 用**完整 60s** HTTP 超时独立分析；成功后写入 race 缓存。
  agent 在 step 4 并行写本地草稿 + `--collect` 收集：缓存命中（Coze 先回）→ 采用
  Coze（中断本地）；否则直接采用本地草稿（速度优先——本地秒级先出、Coze 实测 9~25s 慢、
  常态本地胜出）。complex/vague 走 **串行**（step 7，前台等 Coze 完整返回、含 draft_answer 一并发送），
  两者都走 Coze、失败/超时回退本地草稿。'''

if old1 in content:
    content = content.replace(old1, new1)
    print('Updated module docstring')
else:
    print('WARNING: module docstring pattern not found')

# 2. Update build_refiner docstring
old2 = '''simple/middle 走 **race 竞速（速度优先）**——agent 在 step 2 后台调用
      ``--fire-only``（仅发 difficulty/category/original_question，
      ``draft_answer`` 留空）；Coze 用完整 60s 超时独立分析，成功后写 race 缓存。agent 在 step 3
      并行写本地草稿，step 6 用 ``--collect`` 收集：缓存命中（Coze 先回）→ 采用 Coze（中断本地）；
      否则直接采用本地草稿（速度优先：本地秒级先出、Coze 实测 9~25s 慢，常态本地胜出）。
      complex/vague 走 **串行**：前台等待 Coze 完整返回，且必须把本地已生成的 ``draft_answer``
      一并发送（作为 Coze 参考）。两者失败/超时都回退本地草稿。'''

new2 = '''simple/middle 走 **race 竞速（速度优先）**——agent 在 step 3 后台调用
      ``--fire-only``（仅发 difficulty/category/original_question，
      ``draft_answer`` 留空）；Coze 用完整 60s 超时独立分析，成功后写 race 缓存。agent 在 step 4
      并行写本地草稿 + 用 ``--collect`` 收集：缓存命中（Coze 先回）→ 采用 Coze（中断本地）；
      否则直接采用本地草稿（速度优先：本地秒级先出、Coze 实测 9~25s 慢，常态本地胜出）。
      complex/vague 走 **串行**（step 7）：前台等待 Coze 完整返回，且必须把本地已生成的
      ``draft_answer`` 一并发送（作为 Coze 参考）。两者失败/超时都回退本地草稿。'''

if old2 in content:
    content = content.replace(old2, new2)
    print('Updated build_refiner docstring')
else:
    print('WARNING: build_refiner docstring pattern not found')

# 3. Update refine_fire_only docstring
old3 = '''Race 早发模式（agent 在 step 2 调用，对应 SKILL.md step 6 / references/ops.md §step-7-cookbook）。'''
new3 = '''Race 早发模式（agent 在 step 3 调用，对应 SKILL.md step 3 Fire Gate）。'''
if old3 in content:
    content = content.replace(old3, new3)
    print('Updated refine_fire_only docstring')
else:
    print('WARNING: refine_fire_only pattern not found')

# 4. Update comments about step 2->step 6 race cache flow
old4 = '''agent 在 step 2 后台调用 --fire-only（draft_answer 留空、accuracy 空白→normal），
        #     成功后写入 race 缓存文件；agent 在 step 3 并行写本地草稿，step 6 调用 --collect'''
new4 = '''agent 在 step 3 后台调用 --fire-only（draft_answer 留空、accuracy 空白→normal），
        #     成功后写入 race 缓存文件；agent 在 step 4 并行写本地草稿 + 调用 --collect'''
if old4 in content:
    content = content.replace(old4, new4)
    print('Updated race cache comment 1')
else:
    print('WARNING: race cache comment 1 not found')

# 5. Update self.race_window comment
old5 = 'race 竞速：step 6 收集 Coze 后台结果的等待上限（秒）；超时即放弃、用本地'
new5 = 'race 竞速：step 4 收集 Coze 后台结果的等待上限（秒）；超时即放弃、用本地'
if old5 in content:
    content = content.replace(old5, new5)
    print('Updated race_window comment')
else:
    print('WARNING: race_window comment not found')

# 6. Update refine_fire_only success comment
old6 = '''成功后把 Coze 结果写入 race 缓存文件（供 step 6 ``--collect`` 读取）；'''
new6 = '''成功后把 Coze 结果写入 race 缓存文件（供 step 4 ``--collect`` 读取）；'''
if old6 in content:
    content = content.replace(old6, new6)
    print('Updated refine_fire_only success comment')
else:
    print('WARNING: refine_fire_only success comment not found')

# 7. Update fallback comment
old7 = '''真正的兜底由 agent 在 step 6 用自己的本地草稿完成（此处不回退 draft，'''
new7 = '''真正的兜底由 agent 在 step 4 用自己的本地草稿完成（此处不回退 draft，'''
if old7 in content:
    content = content.replace(old7, new7)
    print('Updated fallback comment')
else:
    print('WARNING: fallback comment not found')

# 8. Update step 2 -> step 6 reference
old8 = '''因为 step 2 时草稿为空，回退会得到空白答案）。'''
new8 = '''因为 step 3 时草稿为空，回退会得到空白答案）。'''
if old8 in content:
    content = content.replace(old8, new8)
    print('Updated empty draft reference')
else:
    print('WARNING: empty draft reference not found')

# 9. Update agent step reference
old9 = '''agent 在 step 2 后台调用此法（run_in_background），step 3 并行写本地草稿，
        step 6 用 ``--collect`` 读取缓存：命中则 Coze 胜出、中断本地；否则用本地草稿（速度优先）。'''
new9 = '''agent 在 step 3 后台调用此法（run_in_background），step 4 并行写本地草稿 + 
        用 ``--collect`` 读取缓存：命中则 Coze 胜出、中断本地；否则用本地草稿（速度优先）。'''
if old9 in content:
    content = content.replace(old9, new9)
    print('Updated agent step reference in fire_only')
else:
    print('WARNING: agent step reference in fire_only not found')

# 10. Update race cache comment
old10 = '''# race 缓存（step 2 写、step 6 读）——仅缓存 Coze 的「结果」，非 payload'''
new10 = '''# race 缓存（step 3 写、step 4 读）——仅缓存 Coze 的「结果」，非 payload'''
if old10 in content:
    content = content.replace(old10, new10)
    print('Updated race cache comment 2')
else:
    print('WARNING: race cache comment 2 not found')

# 11. Update collect_race docstring
old11 = '''Race 收集（agent 在 step 6 调用，对应 ``--collect``）。'''
new11 = '''Race 收集（agent 在 step 4 调用，对应 ``--collect``）。'''
if old11 in content:
    content = content.replace(old11, new11)
    print('Updated collect_race docstring')
else:
    print('WARNING: collect_race docstring not found')

# 12. Update collect_race cache hit reference
old12 = '''读取 step 2 ``refine_fire_only`` 写入的 race 缓存：
          - 缓存命中（Coze 已在 step 2→step 6 间返回）→ 返回 Coze 结果（Coze 胜出、中断本地）；'''
new12 = '''读取 step 3 ``refine_fire_only`` 写入的 race 缓存：
          - 缓存命中（Coze 已在 step 3→step 4 间返回）→ 返回 Coze 结果（Coze 胜出、中断本地）；'''
if old12 in content:
    content = content.replace(old12, new12)
    print('Updated collect_race cache hit reference')
else:
    print('WARNING: collect_race cache hit reference not found')

with open('adapters/refiner.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('DONE')
