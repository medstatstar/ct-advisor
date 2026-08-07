#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
i18n.py -- bilingual (EN/ZH) localization for ct-advisor user-facing prompts
(Single source of truth for all interactive prompt / hint strings.)

This module mirrors the shared pattern in ct-base/scripts/i18n.py so the whole
ct- library stays consistent. It is consumed by:
  - adapters/backend.py (Coze backend) when it renders clarification menus,
    workflow-routing prompts, QC labels and warning boxes;
  - any future ct-advisor CLI / scaffold that emits user-facing text.

In LOCAL mode the methodology agent reads `knowledge/system_prompt.md` +
`knowledge/prompts.md` directly; `knowledge/prompts.md` is the agent-facing
mirror of the key table below and MUST stay in sync with this file.

Rules (per ct-base/references/language_policy.md + ~/.workbuddy/MEMORY.md):
  - Default: auto-detect from OS locale; switch to Chinese when OS locale contains zh/CN
  - One-sentence switch: `set_lang()` (process) / `set_lang_session()` (this conversation)
    / `set_lang_permanent()` (writes config.json `language`); see scripts/switch_lang.py
  - Code output (R/Python) is NOT affected by this policy
  - In bilingual docs join EN/ZH on one line with " / " (spaces both sides)

Usage:
  from i18n import t, set_lang, set_lang_session, set_lang_permanent, is_chinese_os
  print(t("clarify.understand_as", profile="海外II期、单臂、肿瘤"))
  set_lang("zh"); print(t("menu.A"))          # process override
  set_lang_session("en")                        # lasts this conversation
  set_lang_permanent("en")                      # writes config.json `language`
  # or from shell: python scripts/switch_lang.py en [--permanent]
"""

import os
import sys
import json

# 中文 Windows 控制台默认 cp936，直接打印中文文案会乱码或抛 UnicodeEncodeError。
# 与 refine_answer.py 保持一致：统一固定标准流为 UTF-8。
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# Locale detection / 系统语言检测
# ═══════════════════════════════════════════════════════════════════════════

_OVERRIDE_LANG = None


def set_lang(locale_code):
    """[process override] Set an in-process language override (highest priority,
    valid only for the current script run). Used by `scripts/menu.py --lang` and tests.
    Pass None to clear it and fall back to session > config > OS detection."""
    global _OVERRIDE_LANG
    _OVERRIDE_LANG = locale_code


# ── Language resolution chain / 语言判定链 ──────────────────────────────────────
# Priority (highest → lowest):
#   1. process override (set_lang)          — one script run (menu.py --lang, tests)
#   2. session override file                — one conversation (switch_lang.py)
#   3. config.json `language`              — permanent (switch_lang.py --permanent)
#   4. OS locale detection (is_chinese_os)  — default fallback

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SESSION_LANG_FILE = os.path.join(_SKILL_ROOT, "data", ".lang_session")
_CONFIG_PATH = os.path.join(_SKILL_ROOT, "config.json")


def _normalize_lang(code):
    """归一化为 'zh' / 'en'；非法/空值返回 None。"""
    if not code:
        return None
    return "zh" if str(code).lower().startswith("zh") else "en"


def _read_session_lang():
    """读取会话级语言覆盖文件（一次对话内临时切换）。不存在/损坏返回 None。"""
    try:
        with open(_SESSION_LANG_FILE, encoding="utf-8") as f:
            return _normalize_lang(f.read().strip())
    except Exception:
        return None


def _read_config_lang():
    """读取 config.json 的 `language` 字段（永久切换）。缺失返回 None。"""
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return _normalize_lang(json.load(f).get("language"))
    except Exception:
        return None


def set_lang_session(locale_code):
    """[session] 临时切换：写入 data/.lang_session，对整个对话（多次脚本调用）生效。
    传 None 删除会话文件，恢复为 配置 > OS。"""
    global _OVERRIDE_LANG
    lang = _normalize_lang(locale_code)
    if lang is None:
        _OVERRIDE_LANG = None
        try:
            os.remove(_SESSION_LANG_FILE)
        except OSError:
            pass
        return
    os.makedirs(os.path.dirname(_SESSION_LANG_FILE), exist_ok=True)
    with open(_SESSION_LANG_FILE, "w", encoding="utf-8") as f:
        f.write(lang)
    _OVERRIDE_LANG = locale_code


def set_lang_permanent(locale_code):
    """[permanent] 永久切换：写入 config.json `language`，对后续所有会话生效。
    同时清掉会话覆盖，避免冲突。"""
    global _OVERRIDE_LANG
    lang = _normalize_lang(locale_code)
    if lang is None:
        return
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    cfg["language"] = "zh-CN" if lang == "zh" else "en"
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    try:
        os.remove(_SESSION_LANG_FILE)
    except OSError:
        pass
    _OVERRIDE_LANG = locale_code


def is_chinese_os():
    """Detect if the OS is Chinese (zh-CN, zh-TW, zh-HK, etc.).

    Detection order:
      1. Environment variables: LANGUAGE / LC_ALL / LC_MESSAGES / LANG
      2. Windows API: GetLocaleInfoW + registry (LocaleName)
      3. Python locale module: getdefaultlocale()
    """
    # 1. Check environment variables
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var, "")
        if val.lower().startswith("zh"):
            return True

    # 2. Windows-specific detection
    if sys.platform == "win32":
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(85)
            ctypes.windll.kernel32.GetLocaleInfoW(0x0400, 0x00000005, buf, 85)
            if buf.value.lower().startswith("zh"):
                return True
        except Exception:
            pass

        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Control Panel\International"
            )
            locale_name = winreg.QueryValueEx(key, "LocaleName")[0]
            winreg.CloseKey(key)
            if locale_name.lower().startswith("zh"):
                return True
        except Exception:
            pass

    # 3. Python locale module fallback
    try:
        import locale
        loc = locale.getdefaultlocale()[0]
        if loc and loc.lower().startswith("zh"):
            return True
    except Exception:
        pass

    return False


def _current_lang():
    """Return 'zh' or 'en'. Resolution chain (highest priority first):
       1. process override  (set_lang / menu.py --lang)
       2. session override  (set_lang_session / switch_lang.py)
       3. config.json `language` (set_lang_permanent / switch_lang.py --permanent)
       4. OS locale detection (is_chinese_os) — default fallback
    """
    proc = _normalize_lang(_OVERRIDE_LANG)
    if proc:
        return proc
    sess = _read_session_lang()
    if sess:
        return sess
    cfg = _read_config_lang()
    if cfg:
        return cfg
    return "zh" if is_chinese_os() else "en"


# ═══════════════════════════════════════════════════════════════════════════
# Message dictionary / 消息字典  (ct-advisor user-facing prompts)
# ═══════════════════════════════════════════════════════════════════════════

_MESSAGES = {
    # ── Generic / 通用 ──
    "generic.think_first": {
        "en": "Let me think this through before answering.",
        "zh": "我先梳理一下再回答。",
    },
    "generic.proceed": {
        "en": "Proceeding on the stated assumptions.",
        "zh": "基于所述假设继续。",
    },
    "generic.need_more": {
        "en": "To give a precise answer I need to confirm a few things first:",
        "zh": "为给出准确结论，我需要先确认几点：",
    },

    # ── Clarification gate (gate 0) / 澄清门 ──
    "clarify.understand_as": {
        "en": "I understand your question as: {profile}",
        "zh": "我理解您的问题为：{profile}",
    },
    "clarify.offer_options": {
        "en": "Which of the following best matches your need? (pick 1–3)",
        "zh": "以下哪一项最符合您的需要？（可多选 1–3 项）",
    },
    "clarify.insufficient": {
        "en": "The question is not yet specific enough to decide. Please clarify:",
        "zh": "问题尚未明确到可下结论，请补充：",
    },
    "clarify.high_risk_intro": {
        "en": "Before the formal answer, let me confirm my understanding of the problem profile:",
        "zh": "在给出正式结论前，我先确认一下对问题画像的理解：",
    },
    "clarify.not_impersonate": {
        "en": "I can explain why this is needed or give urgent safety actions, but I won't pretend a project-specific formal conclusion from general principles alone.",
        "zh": "我可以解释为何需要该信息，或给出紧急安全措施，但不会仅凭一般原则冒充针对项目的具体正式结论。",
    },
    "clarify.grill_intro": {
        "en": "Let's pin down what you actually need. I'll ask 1–3 focused questions per round; each comes with a recommended default — confirm or adjust. No data fetch, no handoff to other skills.",
        "zh": "我们先把您真正需要的理清楚。我会每轮问 1–3 个聚焦问题，每个都附带推荐默认答案——您确认或调整即可。不取数、不转交其他技能。",
    },
    "clarify.grill_summary": {
        "en": "Here is your needs portrait and my recommended route:",
        "zh": "这是您的需求画像与我的推荐路由：",
    },
    "clarify.triage_simple": {
        "en": "Quick answer below — just say the word if you want me to open the full menu or go deeper.",
        "zh": "下面直接给结论——若需要我打开完整菜单或进一步展开，告诉我即可。",
    },
    "clarify.vague_invite": {
        "en": "Your question is still open-ended — let's pin it down step by step (grill-me style): I'll ask 1–3 focused questions per round, each with a recommended default.",
        "zh": "您的问题仍比较开放——我们用 grill-me 方式逐轮把它理清楚：每轮问 1–3 个聚焦问题，每个都带推荐默认答案。",
    },

    # ── Workflow routing menu (A–J + gate 0) / 工作流路由菜单 ──
    "menu.title": {
        "en": "Which workflow best fits your need?",
        "zh": "哪个工作流最符合您的需要？",
    },
    "menu.gate0": {
        "en": "0 · Clarify / scope the question",
        "zh": "0 · 厘清问题范围",
    },
    "menu.A": {
        "en": "A · Explain & locate evidence",
        "zh": "A · 概念解释与证据定位",
    },
    "menu.B": {
        "en": "B · Trial design",
        "zh": "B · 试验设计",
    },
    "menu.C": {
        "en": "C · Statistics & estimands",
        "zh": "C · 统计与估计目标",
    },
    "menu.D": {
        "en": "D · GCP & quality",
        "zh": "D · GCP 与质量",
    },
    "menu.E": {
        "en": "E · Clinical operations",
        "zh": "E · 临床运营",
    },
    "menu.F": {
        "en": "F · Safety & DSUR",
        "zh": "F · 安全性与 DSUR",
    },
    "menu.G": {
        "en": "G · Documents & reports",
        "zh": "G · 文件与报告",
    },
    "menu.H": {
        "en": "H · Methodology QC",
        "zh": "H · 方法学 QC",
    },
    "menu.I": {
        "en": "I · User tone writing",
        "zh": "I · 用户语气写作",
    },
    "menu.J": {
        "en": "J · Local memory",
        "zh": "J · 本地记忆",
    },

    # ── Clarification menu (gate 0 → decidable) / 澄清菜单 ──
    # Tier 0 — problem-profile grounding
    "menu.ground.title": {
        "en": "Quick context (helps me scope the answer)",
        "zh": "快速背景（帮助我界定回答范围）",
    },
    "ground.role.q": {
        "en": "Your role?",
        "zh": "您的角色？",
    },
    "ground.role.sponsor": {"en": "Sponsor (medical / stats)", "zh": "申办方（医学 / 统计）"},
    "ground.role.cro": {"en": "CRO / CRA", "zh": "CRO / CRA"},
    "ground.role.investigator": {"en": "Investigator / site", "zh": "研究者 / 研究中心"},
    "ground.role.reg": {"en": "Regulatory affairs", "zh": "注册事务"},
    "ground.role.other": {"en": "Other", "zh": "其他"},
    "ground.stage.q": {"en": "Development stage of the asset?", "zh": "在研品种所处阶段？"},
    "ground.stage.preind": {"en": "Pre-IND", "zh": "IND 前"},
    "ground.stage.ph1": {"en": "Phase I", "zh": "I 期"},
    "ground.stage.ph2": {"en": "Phase II", "zh": "II 期"},
    "ground.stage.ph3": {"en": "Phase III", "zh": "III 期"},
    "ground.stage.ph4": {"en": "Phase IV", "zh": "IV 期"},
    "ground.stage.postmarket": {"en": "Post-marketing", "zh": "上市后"},
    "ground.stage.nda": {"en": "NDA / BLA filing", "zh": "NDA / BLA 申报"},
    "ground.stage.unsure": {"en": "Not sure yet", "zh": "还不确定"},
    "ground.input.q": {"en": "What do you have in hand?", "zh": "您手头有什么？"},
    "ground.input.question": {"en": "Just a question", "zh": "仅一个问题"},
    "ground.input.protocol": {"en": "Draft protocol", "zh": "方案草稿"},
    "ground.input.sap": {"en": "SAP", "zh": "统计分析计划（SAP）"},
    "ground.input.csr": {"en": "CSR", "zh": "临床研究报告（CSR）"},
    "ground.input.safetydb": {"en": "Safety database", "zh": "安全性数据库"},
    "ground.input.otherdoc": {"en": "Other document", "zh": "其他文件"},
    "ground.input.none": {"en": "Nothing yet", "zh": "还没有"},

    # Tier 1 — intent area / specific workflow
    "menu.intent.title": {"en": "Which area fits your need?", "zh": "哪个领域符合您的需要？"},
    "menu.intent.q": {"en": "Pick an area (workflows shown next):", "zh": "选择一个领域（下一步显示具体工作流）："},
    "menu.area.design_stats": {"en": "Trial design & statistics (B, C)", "zh": "试验设计与统计（B, C）"},
    "menu.area.safety_ops": {"en": "Safety & clinical operations (E, F)", "zh": "安全性与临床运营（E, F）"},
    "menu.area.docs_qc": {"en": "Documents & methodology QC (G, H)", "zh": "文件与方法学 QC（G, H）"},
    "menu.area.explain_other": {"en": "Explain / GCP / writing / memory (A, D, I, J)", "zh": "解释 / GCP / 写作 / 记忆（A, D, I, J）"},
    "menu.workflow.title": {"en": "Which workflow?", "zh": "哪个工作流？"},
    "menu.workflow.q": {"en": "Pick the closest workflow:", "zh": "选择最贴近的工作流："},

    # Tier 2 — within-workflow sub-intent
    "menu.sub.title": {"en": "What specifically do you need?", "zh": "您具体需要什么？"},
    "menu.sub.q": {"en": "Pick a sub-intent:", "zh": "选择一个具体意图："},
    "menu.sub.A.define_term": {"en": "Define a confused term", "zh": "厘清一个易混概念"},
    "menu.sub.A.find_basis": {"en": "Find the current official basis", "zh": "查找现行官方依据"},
    "menu.sub.A.compare_guide": {"en": "Compare guidelines", "zh": "对比不同指导原则"},
    "menu.sub.B.design_new": {"en": "Design a new trial", "zh": "设计新试验"},
    "menu.sub.B.critique": {"en": "Critique / optimize an existing design", "zh": "评审 / 优化现有设计"},
    "menu.sub.B.endpoints_estimand": {"en": "Endpoints & estimand", "zh": "终点与估计目标"},
    "menu.sub.B.adaptive": {"en": "Adaptive / enrichment feasibility", "zh": "适应性 / 富集设计可行性"},
    "menu.sub.C.estimand_setup": {"en": "Set up estimand & estimator", "zh": "设定估计目标与估计量"},
    "menu.sub.C.samplesize": {"en": "Sample-size plan (→ ct-samplesize)", "zh": "样本量方案（→ ct-samplesize）"},
    "menu.sub.C.missing_data": {"en": "Missing data & sensitivity", "zh": "缺失数据与敏感性分析"},
    "menu.sub.C.ni_eq": {"en": "Non-inferiority / equivalence", "zh": "非劣效 / 等效"},
    "menu.sub.D.deviation_capa": {"en": "Deviation / CAPA handling", "zh": "偏离 / CAPA 处理"},
    "menu.sub.D.audit_ready": {"en": "Audit / inspection readiness", "zh": "稽查 / 核查准备"},
    "menu.sub.D.consent_irb": {"en": "Informed consent / IRB", "zh": "知情同意 / IRB"},
    "menu.sub.E.enroll_feas": {"en": "Enrollment forecast / feasibility", "zh": "入组预测 / 可行性"},
    "menu.sub.E.monitoring_vendor": {"en": "Monitoring / site / vendor", "zh": "监查 / 中心 / 供应商"},
    "menu.sub.E.dblock_ready": {"en": "Database-lock readiness", "zh": "数据库锁定准备"},
    "menu.sub.E.reg_path": {"en": "Regulatory submission pathway", "zh": "注册申报路径"},
    "menu.sub.F.susar": {"en": "Individual SUSAR / expedited report", "zh": "个例 SUSAR / 快速报告"},
    "menu.sub.F.dsur": {"en": "DSUR preparation", "zh": "DSUR 撰写"},
    "menu.sub.F.signal": {"en": "Safety signal", "zh": "安全性信号"},
    "menu.sub.F.benefit_risk": {"en": "Benefit–risk assessment", "zh": "获益 - 风险评估"},
    "menu.sub.G.csr_review": {"en": "CSR review", "zh": "CSR 评审"},
    "menu.sub.G.protocol_review": {"en": "Protocol review", "zh": "方案评审"},
    "menu.sub.G.sap_review": {"en": "SAP review", "zh": "SAP 评审"},
    "menu.sub.G.draft_section": {"en": "Draft a section from scratch", "zh": "从零起草某章节"},
    "menu.sub.H.design_qc": {"en": "Design QC", "zh": "设计 QC"},
    "menu.sub.H.document_qc": {"en": "Document QC", "zh": "文件 QC"},
    "menu.sub.H.crossfile": {"en": "Cross-file consistency", "zh": "跨文件一致性"},
    "menu.sub.H.submission_ready": {"en": "Submission readiness", "zh": "申报就绪度"},
    "menu.sub.I.reply_tone": {"en": "Reply in my tone", "zh": "用我的语气回复"},
    "menu.sub.I.rewrite": {"en": "Rewrite a draft", "zh": "重写草稿"},
    "menu.sub.J.recall": {"en": "Recall prior context", "zh": "回顾既往上下文"},
    "menu.sub.J.save_pref": {"en": "Save a preference", "zh": "保存一项偏好"},

    # Tier 3 — output format (optional; default = just answer)
    "menu.out.title": {"en": "Preferred output format?", "zh": "偏好哪种输出形式？"},
    "menu.out.q": {"en": "How should I deliver? (default: just answer)", "zh": "希望以何种形式交付？（默认：直接回答）"},
    "out.format.advisory_memo": {"en": "Advisory memo (structured)", "zh": "咨询备忘录（结构化）"},
    "out.format.checklist": {"en": "Checklist", "zh": "检查清单"},
    "out.format.redline_review": {"en": "Redline review", "zh": "修订批注式评审"},
    "out.format.option_compare": {"en": "Option comparison", "zh": "方案对比"},

    # ── Methodology QC labels (workflow H) / 方法学 QC 标签 ──
    "qc.overall": {
        "en": "Overall judgment",
        "zh": "总体结论",
    },
    "qc.verdict.acceptable": {
        "en": "Acceptable",
        "zh": "可接受",
    },
    "qc.verdict.conditional": {
        "en": "Acceptable with conditions",
        "zh": "有条件接受",
    },
    "qc.verdict.unacceptable": {
        "en": "Unacceptable",
        "zh": "不可接受",
    },
    "qc.issue_list": {
        "en": "Issue list (issue / evidence / impact / priority)",
        "zh": "问题清单（问题 / 证据 / 影响 / 优先级）",
    },
    "qc.remediation": {
        "en": "Remediation plan",
        "zh": "整改方案",
    },
    "qc.gap": {
        "en": "Information gap (what is missing / who provides / impact on judgment)",
        "zh": "信息缺口（缺什么 / 由谁提供 / 对结论的影响）",
    },
    "qc.next_gate": {
        "en": "Next quality gate (what must be met before the next stage)",
        "zh": "下一质量门（进入下一阶段前须满足的条件）",
    },

    # ── Warnings / stop rules / 警示与停止规则 ──
    "warn.verify_incomplete": {
        "en": "Verification not yet complete — no definitive judgment on items depending on this basis.",
        "zh": "核实尚未完成——对依赖该依据的事项不下确定结论。",
    },
    "warn.unconfirmed": {
        "en": "Unconfirmed items — why unconfirmable — what judgment this affects:",
        "zh": "未能确认项——为何无法确认——影响哪些结论：",
    },
    "warn.complex_patience": {
        "en": "This question is complex / not yet fully clear. The AI needs to do an in-depth verification to ensure the conclusion is correct — please wait for the result.",
        "zh": "这个问题比较复杂 / 还不够明确，AI 需要对问题做深入核查以确保结论正确，请耐心等候结果。",
    },
    "stop.tracing": {
        "en": "Definitive judgment withheld. Official tracing path below; please return the original for re-check.",
        "zh": "不下确定结论。官方溯源路径如下，请返回原文复核。",
    },
    "stop.no_risk_mask": {
        "en": "Do not use \"no risk found\" to mask unreceived or unreconciled data.",
        "zh": "不得用「未发现风险」掩盖未收到或未核对的资料。",
    },
    "stop.fabricate": {
        "en": "Do not fabricate sample size, deadline, effect size or risk conclusion when key parameters are missing.",
        "zh": "关键参数缺失时，不得编造样本量、时限、效应量或风险结论。",
    },

    # ── Official tracing card / 官方溯源卡 ──
    "trace.title": {
        "en": "Official tracing card",
        "zh": "官方溯源卡",
    },
    "trace.body": {
        "en": "Applicable body & entry / suggested document or topic / copyable search terms / document number, version, status, implementation date, scope / body clause / page or PDF to return",
        "zh": "适用机构与入口 / 建议文件或主题 / 可复制检索词 / 文号·版本·状态·实施日·范围 / 正文条款 / 待返回页面或 PDF",
    },
    "trace.retry": {
        "en": "Please return the original page/PDF so I can re-check against the official source.",
        "zh": "请返回原始页面/PDF，以便我对照官方来源复核。",
    },

    # ── AskUserQuestion option templates / 选项模板 ──
    "ask.adopt": {
        "en": "Adopt the above",
        "zh": "采用以上",
    },
    "ask.revise": {
        "en": "Revise",
        "zh": "修改",
    },
    "ask.cancel": {
        "en": "Cancel",
        "zh": "取消",
    },
    "ask.confirm_assumption": {
        "en": "Continue under the following assumptions?",
        "zh": "在以下假设下继续？",
    },

    # ── Source-tier labels (evidence boundary) / 来源层级标签 ──
    "src.mandatory": {
        "en": "Regulatory / mandatory requirement",
        "zh": "法规 / 强制要求",
    },
    "src.guidance": {
        "en": "Guidance suggestion",
        "zh": "指导建议",
    },
    "src.judgment": {
        "en": "Methodology judgment",
        "zh": "方法学判断",
    },
    "src.practice": {
        "en": "Project practice suggestion",
        "zh": "项目实践建议",
    },

    # ── Grounding rule (cite § or mark 官方核实) / 溯源硬规则（标注章节或官方核实）──
    "grounding.require_cite": {
        "en": "This point is based on {ref} §{section}; verify against the official original if used for a filing / decision.",
        "zh": "该点依据 {ref} §{section}；若用于申报 / 决策，请对照官方原文核实。",
    },
    "grounding.official_verify": {
        "en": "⚠️ 官方核实 / Officially verify — I cannot confirm the current version / status / deadline from static content; please check the official source.",
        "zh": "我无法凭静态内容确认现行版本 / 状态 / 截止日，请查官方来源。",
    },
    "grounding.low_confidence": {
        "en": "Source not found for this claim — treated as unverified, not stated as fact.",
        "zh": "该断言未找到来源——按未核实处理，不作事实陈述。",
    },

    # ── Data grounding & handoff hints / 数据接地与转交提示 ──
    "ground.performed": {
        "en": "Data grounding performed: {source} on {date}.",
        "zh": "已执行数据接地：{source}（{date}）。",
    },
    "ground.skipped": {
        "en": "No data grounding performed (pure methodology / design / compliance question).",
        "zh": "未执行数据接地（纯方法学 / 设计 / 合规问题）。",
    },
    "handoff.samplesize": {
        "en": "Sample-size parameters complete → handing off to `ct-samplesize` for computation (this skill does not compute n in-house).",
        "zh": "样本量参数齐全 → 转交 `ct-samplesize` 计算（本技能不内置计算 n）。",
    },

    # ── Routing (absorbed ct console: total entry) / 路由（吸收 ct 控制台：总入口）──
    "menu.cap.title": {
        "en": "Which kind of help do you need?",
        "zh": "您需要哪一类帮助？",
    },
    "menu.cap.q": {
        "en": "Pick a capability (routes your request):",
        "zh": "选择能力类别（决定请求路由）：",
    },
    "menu.cap.methodology": {
        "en": "Methodology & regulatory advice (design / stats / compliance / QC)",
        "zh": "方法学与法规顾问（设计 / 统计 / 合规 / QC）",
    },
    "menu.cap.data_intel": {
        "en": "Real data & competitive intel (registry / safety / literature)",
        "zh": "真实数据与竞品情报（注册 / 安全性 / 文献）",
    },
    "menu.cap.clarify": {
        "en": "Clarify my needs first (I'm not sure what I want)",
        "zh": "先帮我理清需求（我还不确定要什么）",
    },
    "menu.ct_registry": {
        "en": "Trial-registry landscape (CT.gov / CDE / WHO ICTRP / EU-CTR / ChiCTR / ISRCTN / DRKS)",
        "zh": "试验注册格局（CT.gov / CDE / WHO ICTRP / EU-CTR / ChiCTR / ISRCTN / DRKS）",
    },
    "menu.ct_safety": {
        "en": "Safety signals (FAERS PRR / ROR / IC)",
        "zh": "安全性信号（FAERS PRR / ROR / IC）",
    },
    "menu.ct_literature": {
        "en": "Published literature (OpenAlex / Europe PMC / Semantic Scholar)",
        "zh": "已发表文献（OpenAlex / Europe PMC / Semantic Scholar）",
    },
    "menu.ct_competitive": {
        "en": "Full competitive-intel brief (call registry + safety + literature, stitch in-house ⭐)",
        "zh": "完整竞品情报简报（调用注册 + 安全性 + 文献三源，本技能缝合 ⭐）",
    },
    "menu.explain_diff": {
        "en": "Can't decide? → say \"explain the differences\", I'll clarify before you choose",
        "zh": "还拿不准？→ 说「详细解释差异」，我先讲清再让你决定",
    },
    "menu.data_skill.title": {
        "en": "Which data source?",
        "zh": "哪个数据源？",
    },
    "menu.data_skill.q": {
        "en": "Pick the data skill to invoke:",
        "zh": "选择要调用的数据技能：",
    },
    "menu.data_subintent.title": {
        "en": "How should I proceed?",
        "zh": "如何继续？",
    },
    "menu.data_subintent.q": {
        "en": "Run now, or scope the search first?",
        "zh": "直接运行，还是先聚焦检索范围？",
    },
    "menu.data_subintent.run": {
        "en": "Run now (the skill asks follow-ups inline)",
        "zh": "直接运行（技能内联追问）",
    },
    "menu.data_subintent.focus": {
        "en": "Scope first (drug / indication / time window / comparator set)",
        "zh": "先聚焦范围（药物 / 适应症 / 时间窗 / 对照集）",
    },
    "route.trigger_data": {
        "en": "Routing to data skill `{skill}` for real-data retrieval (via Skill tool).",
        "zh": "正在路由到数据技能 `{skill}` 获取真实数据（通过 Skill 工具）。",
    },

    # ── Boundary / red line reminder / 边界与红线提示 ──
    "boundary.no_pii": {
        "en": "Note: I will not expose personal info, subject info, unpublished project data, private paths or access credentials in the answer.",
        "zh": "提示：我不会在回答中泄露个人信息、受试者信息、未公开项目数据、私有路径或访问凭据。",
    },
}


def t(key, **kwargs):
    """Translate a message key to the current locale.

    Args:
        key: message identifier in _MESSAGES
        **kwargs: format placeholders (e.g., profile="...", source="ct-registry")

    Returns:
        Localized string. Falls back to the key itself if not found.
    """
    lang = _current_lang()
    entry = _MESSAGES.get(key)
    if entry is None:
        return key
    text = entry.get(lang, entry.get("en", key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


# Back-compatible alias
_ = t


if __name__ == "__main__":
    # Quick self-check
    set_lang(None)
    print("[default/en]", t("menu.A"))
    print("[default/en]", t("clarify.understand_as", profile="Ph2 oncology, single-arm"))
    set_lang("zh")
    print("[zh]", t("menu.A"))
    print("[zh]", t("clarify.understand_as", profile="II期肿瘤、单臂"))
    set_lang(None)
