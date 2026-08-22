#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ct-advisor — 确定性难度分类器（代码级，无 LLM）

设计目标（治本，不依赖 LLM 纪律）：
  - 把「是否发 Coze / 判难度」的决策从主 Agent（本地 LLM）收归成**代码确定性分类**。
  - 主 Agent 永远不自己判断难度，只运行本脚本拿标签，从根上消除
    「本地模型先理解问题→顺手答题→抢答/3-5min 循环」的旧故障。

用法：
  python scripts/route.py "用户问题原文"
        → 打印一个标签：simple | vague | middle | complex
  python scripts/route.py --json "用户问题原文"
        → 打印 {"route": "...", "signals": {...}}
  python scripts/route.py --self-test
        → 跑内置分类自测，输出每例命中/预期与准确率

【route.py 的核心职责（2026-08-17 明确）】
  本地代码**最主要用途是拆分出 vague**——指代不明/过短/回指省略的问题在本地拦截、
  进入 clarify_loop 澄清，绝不转发 Coze。
  simple / middle / complex 仅作为转发时附带的【提示标签】，Coze 服务端会【一律用 LLM
  重新估计】difficulty 并写回（见 generate_organized_problems_node._resolve_difficulty），
  因此本地判定结果不决定最终难度档位，也不作为 Coze 侧硬性路由键。

分类优先级（确定性，瞬时，stdlib-only）：
  1. 空串                       → vague
  2. 🔴 is_vague（指代不明/过短/回指省略，判断**可偏多**）→ vague
                               （进入 clarify_loop 启发式菜单；宁可多澄清也不漏发 Coze）
  3. is_simple（定义/标准操作） → simple        （附提示标签转发 Coze）
  4. 命中 complex 强信号        → complex        （含预路由拦截：外部数据/样本量强制 complex）
  5. is_middle（显式解释/比较）  → middle         （附提示标签转发 Coze）
  6. 兜底                       → complex        （未命中任何信号一律 complex，绝漏发车）

入口分流（2026-08-14 晚，与 SKILL.md 对齐）：
  - 🔴 **vague 最先判定（判断可偏多）**：发现 vague 立即进入本地澄清循环
    scripts/clarify_loop.py（启发式菜单）明确需求，收敛后再转发 Coze；绝不漏发 Coze。
  - simple / middle / complex → 一律 verbatim 转发 Coze（forward-only），并随 payload 带上
    query_meta.difficulty 提示标签（Coze 会重新估计，仅作参考）。
"""

import argparse
import json
import re
import sys

# ---------------------------------------------------------------------------
# 信号词典（与 references/steps.md 的 difficulty 定义对齐，确定性、可单测）
# ---------------------------------------------------------------------------

# 受控术语（CDISC / 临床试验领域），仅作 simple 的辅助证据 + vague 排除
TERM = re.compile(
    r"(SDTM|ADaM|AE|SAE|CE|CM|DS|VS|LB|EG|RS|SV|SE|TA|TI|TV|"
    r"CSR|TLF|CRF|EDC|eCRF|SAP|ICH[- ]?GCP|GCP|CDISC|ADSL|BDS|OCCDS|ADTTE|"
    r"PK|PD|MedDRA|WHODrug|IB|SUSAR|DSUR|ICF|RBM|QbD|ALCOA)"
)

# 定义意图（仅查询式："X 的定义/定义是/精确定义"；裸「定义」过宽，
# "如何定义 X 的标准"这类方法论句式会误判 simple → 已排除）
DEF = re.compile(
    r"(什么是|什么意思|的定义|定义是|定义是什么|精确定义|含义|全称|英文缩写|英文全称|英文是|"
    r"\bmeans\b|\bdefine\b|definition)"
)

# 标准操作 / 本地 SOP（有明确标准答案，本地可答 → simple）
# 注意：不含裸「应如何处理 / 如何评估」（这些也出现在 middle/complex，会漏判到 simple）
STOP = re.compile(
    r"(是否符合|正确做法|记录和处理|"
    r"需要完成哪些核心|需要完成哪些关键|哪些关键任务|哪些核心步骤|需要在何时|应在何时|"
    r"需要保留哪些|需要具备哪些资质|如何溯源|如何进行.*?核查|溯源|核对|"
    r"上报时限|报告时限|时限|规范|流程|步骤|"
    r"如何提交|如何上报|如何填写|填写.*?规范|"
    r"属于.*?还是|有何要求|有何规定|资质|"
    r"如何使用|如何回收|补填|翻译后签署|锁定.*?步骤|关闭.*?任务|"
    r"评估哪些|如何确定.*?频率|"
    r"谁必须参加|保存要求|签署.*?要求|如何管理|"
    r"需要提交哪些核心文件|提交哪些核心文件|年度报告|快速审查|"
    r"破盲|是否应退出|是否构成重大|"
    r"保存多久|保留多久|是否属于|算不算|是否算|什么手续|正式退出)"
)

# simple 排除信号（命中任一 → 不是 simple）。聚焦「设计/协调/框架/体系/变更/
# 前沿/灰色/跨学科/机制/因果/特定主题词」。注意：裸「方案」「系统」过宽（基础题常
# 提方案偏离/方案规定、HIS系统/EDC系统），已移除，仅用 方案设计/试验设计 等特异性词。
EXCL = re.compile(
    r"(设计|规划|策略|计划|区别|差异|对比|\bvs\b|哪个好|哪个更|"
    r"竞品|文献|为什么|如何保证|这个|那个|它|它们|"
    r"所有|全面|完整|汇总|综合|多工作流|端到端|最佳|推荐|优劣|利弊|"
    r"协调|框架|体系|变更|多重|动态|跨学科|前沿|灰色|合并|转移|转至|培训|"
    r"机制|因果关系|障碍|应急|外推|角色|义务|价值|证据|"
    r"豁免|弱势|胁迫|利益冲突|保险|稽查|供应链|网络|区块链|联邦|"
    r"AI|基因|放射性|CMC|附条件|同情|儿科|跨境|数据保护|同时|联合|"
    r"如何设计|试验设计|随机化设计|体系设计|方案设计)"
)

# complex 强信号（命中任一 → 强制 complex）。已剔除仅在基础/中等题出现的
# 注册/应急/附条件/利益冲突（保留 监管/统计/样本量/设计… 等真正复杂专属信号）。
# 2026-08-12 补跨库稳定复杂主题词（监管设计/前沿/机制/数据完整性，两题库联合验证）。
CPLX = re.compile(
    r"(设计终点|试验设计|随机化设计|体系设计|方案设计|如何设计|"
    r"工艺变更|CMC变更|生产变更|变更评估|"
    r"框架|体系|多重比较|动态|同时测试|主方案|篮子|平台试验|适应性|贝叶斯|"
    r"代际|灰色|前沿|跨学科|基因编辑|基因治疗|生殖系|放射性|CAR-T|CMC|同情用药|"
    r"儿科外推|区块链|联邦学习|AI聊天|AI辅助|AI算法|iRECIST|BICR|网络安全|欺诈|结构性胁迫|"
    r"弱势群体|豁免|紧急使用|供应链|跨境|数据保护|外推|"
    r"NDA|CDE|Pre-IND|CIOMS|AESI|敏感性分析|因果关系|突破性治疗|DSMB|"
    r"勒索软件|地震|RPSFT|交叉调整|继续治疗|维持治疗|退出条件|eCOA|ePRO|PRO数据|PRO终点|"
    r"统计|假设检验|检验效能|估算|计算|样本量|n\s*=|"
    r"文献|安全性信号|靶点|适应症|剂量)"
)

# middle 显式信号（仅在无 complex 信号时生效；放宽以接住中等题，避免坠入兜底→complex）
MID = re.compile(
    r"(解释|说明|区别|差异|对比|比较|\bvs\b|为什么|如何|怎么|步骤|流程|"
    r"如何处理|如何评估|哪些因素|需要考虑|如何协调|如何确定|如何解读|"
    r"是否允许|需要哪些审批|解读|分析|评估|"
    r"应启动哪些|是否可接受|如何管理|优先遵循|还需要哪些|还需要完成|"
    r"是否需要将|是否需要持有|应在多长时间)"
)

# vague 指代信号（显性代词 + 短句）
VAGUE_PRON = re.compile(r"(这个|那个|它|它们|这|那)")

# 回指 / 省略线索（指向前文未明说的对象）。偏宽松：用复合形式（如"之前提到"）
# 避免误伤"之前的药物"这类清晰短句；纯方位词（前面/后面/上面/下面/前者/后者）
# 几乎总是语篇指代，直接纳入。
ANAPHORA = re.compile(
    r"(前面|后面|上面|下面|前者|后者|前边|后边|前述|前述的|上述的|"
    r"之前提到|之前说|之前讨论|刚才说|刚才提到|刚才问|刚才讨论|"
    r"上一条|上一个问题|上轮|上一次|您说的|你说的|您讲的|我说的|"
    r"前面那个|后面那个|上面那个|下面那个)"
)

# 语义 vague（2026-08-20 修复：README 示例 5 实测判 complex 的根因）：
# 用户明说「不确定/不知道需要什么」且无明确对象 → 进入本地澄清。
# 仅命中「不确定 X 是否/能不能…」这类**有明确对象的具体判断**时不判 vague
# （由 is_vague 内的排除检查处理，避免把「不确定这样做是否合规」误拉进澄清）。
VAGUE_UNCERTAIN = re.compile(
    r"(?:不.{0,2}(?:确定|清楚|知道|了解)|没想好|拿不准|没有头绪|毫无头绪)"
    r".{0,10}(需要什么|要什么|做什么|怎么办|怎么弄|该做什么|该问什么|问什么|"
    r"怎么开始|从哪(?:里)?开始|什么需求|需求是什么|怎么用|怎么提问)|"
    r"\b(not sure|not certain|unsure|don'?t know|no idea|not clear|no clue)"
    r".{0,24}\b(what|how|which|where)\b|"
    r"\bwhat (?:do|should|can) i (?:need|ask|do|get|want)\b",
    re.IGNORECASE,
)
# 有明确对象的判断句式（命中 → 不算语义 vague）
VAGUE_UNCERTAIN_EXCL = re.compile(
    r"(不确定|不清楚|不知道|not sure|not certain|unsure).{0,14}"
    r"(是否|能不能|可不可以|对不对|合理|合规|正确|appropriate|valid|acceptable|\bif\b)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# simple 白名单：knowledge 知识包确定覆盖的「标准操作 / 定义类」主题短语
# （来源：knowledge/reference-index.md 覆盖主题 + 四题库联合验证；命中即本地直答）
# 使用约束：仅当 未命中 CPLX（设计/统计/外部数据）且未命中 EXCL 时才生效，
# 确保白名单不会把「设计/监管/灰色地带」类问题误拉进 simple（漏发车红线）。
# 2026-08-12 四库验证：0 漏发车，simple 召回 桌面 22/40、第二版 12/40、全新 12/40、D库 12/20。
# ---------------------------------------------------------------------------
SIMPLE_TOPICS = re.compile(
    r"(alcoa|sdv|isf\b|siv\b|"
    r"上报时限|报告时限|sa[e]?\s*报告|sae 报告|"
    r"药物计数|药物清点|药物回收|药物发放|"
    r"温度超标|温度偏离|温控|"
    r"急救揭盲|紧急揭盲|破盲|"
    r"快速审查|年度报告|跟踪审查|修正案|"
    r"受试者补偿|"
    r"妊娠报告|妊娠结局|怀孕|哺乳|"
    r"筛选日志|筛选失败|中心关闭|监查报告|启动会|"
    r"随机化分层|分层随机化|区组|"
    r"代扣代缴|进口药品注册证|进口药品批件|"
    r"会议法定人数|保存要求|签署要求|"
    r"知情同意撤回|撤回知情同意|"
    r"退药|退回药物|"
    r"数据质疑|crf\s*填写|"
    r"筛选号|随机号|药物编号)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# 分类函数
# ---------------------------------------------------------------------------

def is_simple(q: str) -> bool:
    """单点定义 / 标准操作 → simple。"""
    if len(q) > 140:
        return False
    if DEF.search(q) or STOP.search(q):
        return not EXCL.search(q)
    # 白名单：knowledge 标准操作主题，命中且无 complex/排除信号 → simple 本地直答
    if SIMPLE_TOPICS.search(q) and not CPLX.search(q) and not EXCL.search(q):
        return True
    # 纯术语裸词（≤12 字，无排除信号）→ 当定义查，本地快答
    if TERM.search(q) and len(q) <= 12:
        return not EXCL.search(q)
    return False


def is_vague(q: str) -> bool:
    """指代不明 / 过短无实体 / 回指省略 → vague。
    🔴 入口最高优先级（仅次空串）：vague 是唯一「不转发 Coze」的分支，必须最先判定；
    判断**可偏多**——宁可进本地澄清菜单，也不漏发 Coze。simple/middle/complex
    仅是 verbatim 转发的备用标签。"""
    # 1) 显性指代代词 + 短句（上限放宽到 24，覆盖"这个样本量计算要考虑什么"）
    if VAGUE_PRON.search(q) and len(q) <= 24:
        return True
    # 2) 回指 / 省略线索（无具体动作信号时按 vague；上限 30）
    if ANAPHORA.search(q) and len(q) <= 30:
        return True
    # 3) 过短且无术语 / 定义 / 标准操作锚点 → 视为 vague（偏多：含糊短句进菜单）
    if len(q) <= 10 and not TERM.search(q) and not DEF.search(q) \
       and not STOP.search(q) and not SIMPLE_TOPICS.search(q):
        return True
    # 4) 语义 vague（2026-08-20 补）：明说「不确定/不知道需要什么」→ 进入澄清。
    #    排除「不确定 X 是否/能不能…」这类有明确对象的具体判断（不判 vague）。
    if VAGUE_UNCERTAIN.search(q) and not VAGUE_UNCERTAIN_EXCL.search(q):
        return True
    return False


def is_middle(q: str) -> bool:
    """显式解释 / 比较 / 单步推理，且无 complex 信号 → middle。"""
    if CPLX.search(q):
        return False
    return bool(MID.search(q))


def route_question(q: str) -> str:
    """返回 simple | vague | middle | complex。
    🔴 vague 优先：入口唯一不转发 Coze 的分支，必须最先判定（判断可偏多）；
    simple/middle/complex 仅作 verbatim 转发的备用标签。"""
    q = (q or "").strip()
    if not q:
        return "vague"
    if is_vague(q):            # 🔴 最高优先级：vague 必须先于 simple/complex 判定
        return "vague"
    if is_simple(q):
        return "simple"
    if CPLX.search(q):          # 预路由拦截 + 设计/外部数据/选项/复合 → 强制 complex
        return "complex"
    if is_middle(q):
        return "middle"
    return "complex"            # 兜底：未命中任何信号一律 complex，绝漏发车


def route_with_signals(q: str) -> dict:
    """调试用：返回标签 + 各规则命中情况。"""
    q = (q or "").strip()
    return {
        "route": route_question(q),
        "signals": {
            "simple": is_simple(q),
            "vague": is_vague(q),
            "middle": is_middle(q),
            "complex_forced": bool(CPLX.search(q)),
        },
    }


# ---------------------------------------------------------------------------
# 内置分类自测（用 --self-test 运行；词典调优闭环）
# ---------------------------------------------------------------------------

SELF_TEST = [
    # (问题, 期望标签)
    # ---- simple：定义 / 标准操作 ----
    ("什么是 SDTM", "simple"),
    ("AE 的英文全称是什么", "simple"),
    ("如何提交不良事件报告", "simple"),
    ("CRF 填写步骤", "simple"),
    ("SAE 上报时限", "simple"),
    ("SDTM", "simple"),
    ("上报时限是多少", "simple"),   # 短而清晰（含 STOP），不误判 vague（精度护栏）
    # ---- vague：指代不明 / 过短 / 回指省略（判断偏多）----
    ("这个怎么弄", "vague"),
    ("那个是什么意思", "vague"),
    ("它是指什么", "vague"),
    ("这个样本量怎么算", "vague"),            # 含代词 + CPLX 词，仍判 vague（修复漏判）
    ("那个试验设计要注意什么", "vague"),        # 含代词 + CPLX 词
    ("前面说的统计检验方法该怎么选", "vague"),    # 回指省略
    ("上一条说的不良事件要怎么报", "vague"),      # 复合回指
    ("怎么办", "vague"),
    ("我不太确定自己到底需要什么", "vague"),      # 语义 vague（README 示例 5 ZH）
    ("I'm not sure what I actually need", "vague"),  # 语义 vague（README 示例 5 EN）
    ("我不知道该从哪里开始", "vague"),            # 语义 vague 变体
    # ---- middle：显式解释 / 比较，无 complex 信号 ----
    ("解释 SDTM 和 ADaM 的区别", "middle"),
    ("说明 SDTM 的变量命名规则", "middle"),
    ("为什么 AE 需要分级", "middle"),
    # ---- complex：设计 / 外部数据 / 选项 / 复合（默认） ----
    ("如何设计一个抗肿瘤药的随机对照试验方案", "complex"),
    ("注册库中 PD-1 抑制剂的三期试验有哪些", "complex"),
    ("推荐一个适合二型糖尿病的终点指标", "complex"),
    ("样本量计算要考虑哪些因素", "complex"),
    ("CRF 设计要注意什么", "complex"),
    ("对比两种统计检验方法的优劣", "complex"),
    ("不确定下一步怎么办，做法是否合规", "middle"),  # 语义 vague 命中 + 明确对象排除（是否）→ 不澄清，转发（middle）
    ("I'm not sure if this design is appropriate", "complex"),  # EN 排除 vague
]


def run_self_test() -> int:
    print("route.py 分类自测")
    print("=" * 56)
    ok = 0
    for q, expect in SELF_TEST:
        got = route_question(q)
        mark = "✓" if got == expect else "✗"
        if got == expect:
            ok += 1
        print(f"  {mark} [{got:<7}] 期望 {expect:<7} | {q}")
    total = len(SELF_TEST)
    print("-" * 56)
    print(f"  准确率: {ok}/{total} = {ok / total * 100:.1f}%")
    return 0 if ok == total else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="ct-advisor deterministic difficulty router (Mode B)")
    ap.add_argument("question", nargs="?", help="用户问题原文")
    ap.add_argument("--json", action="store_true", help="输出 JSON（含命中信号）")
    ap.add_argument("--self-test", action="store_true", help="运行内置分类自测")
    args = ap.parse_args()

    if args.self_test:
        return run_self_test()

    if not args.question:
        ap.print_help()
        return 2

    if args.json:
        print(json.dumps(route_with_signals(args.question), ensure_ascii=False))
    else:
        print(route_question(args.question))
    return 0


if __name__ == "__main__":
    sys.exit(main())
