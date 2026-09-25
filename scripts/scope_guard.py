#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ct-advisor — 范围路由与超范围转介（改进 C，2026-09-23）

背景（来自 Ct-Advisor_连续提问诊断报告）：
  - 用户 B 的两条 medical-writing 请求（EEG / 神经调控报告大纲）：1175 的回答已自承
    「未在本技能核心临床试验知识库中找到直接对应依据」，却仍带免责声明硬答——
    正属于诊断报告指出的「应提示用户使用其他技能」的情形。
  - 技能核心范围（见 C12 范围外声明 / knowledge）：临床试验**法规·方法学**——
    试验设计、GCP 合规、注册申报、安全性评价（PV/SAE）、统计分析（SAP/样本量）、
    数据管理（SDTM/ADaM/EDC）等。
  - 超范围典型：通用**医学写作 / 综述 / 报告撰写 / 科普**，且缺乏临床试验运营信号。

设计要点（保守，避免误伤）：
  - 仅当「强写作意图」**且**「弱试验运营信号」同时成立，才判为超范围 → 触发转介。
  - 不阻断、不硬答替代：仅产出转介声明，由 refine_answer.py 在最终答案**前置**注入，
    云端仍会产出一份尽力参考（与现有 C13 / suggest_footer 机制一致）。
  - 任何异常 → 一律视为「在范围内」（宁可多答，不误拦）。stdlib-only。
"""

import re

# 强写作意图：明确要求"写/起草/大纲/综述/模板"等产出物
MEDICAL_WRITING = re.compile(
    r"(撰写|起草|拟写|写一份|写一?份|写个|帮我写|请写|大纲|框架|目录|综述|文献综述|"
    r"稿件|论文|科普|模板|范本|范例|知情同意书|试验方案.*模板|病历|病例报告|"
    r"报告.*结构|结构.*报告|报告.*怎么写|怎么写.*报告|文稿|投稿|写作)",
    re.IGNORECASE,
)

# 临床试验运营信号（命中任一 → 视为试验语境，不判超范围）
TRIAL_OPS = re.compile(
    r"(临床试验|临床试|试验方案|研究方案|方案设计|研究设计|受试者|参试|病例报告表|"
    r"CRF|EDC|IRB|伦理委员|申办者|申办方|合同研究|CRO|GCP|ICH|主要终点|次要终点|"
    r"终点指标|随机|盲法|双盲|SAP|统计分析计划|样本量|对照|安慰剂|IND|NDA|"
    r"注册申报|上市申请|申报|不良事件|严重不良|SAE|药物警戒|\bPV\b|知情同意|"
    r"入选标准|排除标准|入排|剂量爬坡|剂量递增|生物等效|桥接试验|真实世界|RWE)",
    re.IGNORECASE,
)

# 转介声明（中文；与 C12 范围外声明风格一致）。英文由调用方按语言切换（此处聚焦中文主路径）。
REFERRAL_ZH = (
    "⚠️ 本题偏向「医学写作 / 综述 / 报告撰写」类任务，超出 Ct-Advisor 的临床试验"
    "法规·方法学核心范围（核心覆盖：试验设计、GCP 合规、注册申报、安全性评价、统计分析、"
    "数据管理）。建议改用语雀 / 腾讯文档等通用写作技能完成撰写；以下为基于通用知识的参考，"
    "未经临床试验知识库核验，仅供参考、不构成规范依据。"
)


def assess(question: str) -> tuple:
    """评估是否在核心范围内。

    返回 (in_scope, scope_tag, referral)：
      - in_scope=True           → ("", "")（不处理）；
      - in_scope=False（超范围）→ (tag, referral 声明文本)。
    异常 → (True, "", "")（宁多答不误拦）。
    """
    try:
        q = question or ""
        if MEDICAL_WRITING.search(q) and not TRIAL_OPS.search(q):
            return False, "medical_writing", REFERRAL_ZH
        return True, "", ""
    except Exception:  # noqa: BLE001
        return True, "", ""


def apply_referral(final_answer: str, scope_tag: str) -> str:
    """把超范围转介声明前置注入最终答案（不截断原答案）。已含声明则跳过。"""
    if not scope_tag:
        return final_answer
    fa = final_answer or ""
    if "超出 Ct-Advisor" in fa or "未经临床试验知识库核验" in fa:
        return fa  # 已含声明，避免重复
    return REFERRAL_ZH + "\n\n---\n\n" + fa


if __name__ == "__main__":
    print(assess("请帮我起草一份 EEG 神经调控研究报告的大纲"))   # 超范围
    print(assess("请帮我设计这个抗肿瘤药的随机对照试验方案"))     # 在范围
    print(assess("写一份关于糖尿病的科普文章"))                   # 超范围
