#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""confirm_menu.py — 技能调用「用户确认菜单」两阶段协议（2026-11-19，纯代码）。

背景（用户裁定 2026-11-19）
============================
入口 plan_gate 一次轻量 LLM 判定 direct / single / multi 后，技能调用不再自动执行，
而是交给用户以**多选菜单**确认一次（避免 Coze 误判导致无谓取数与二次综合开销）：

  * direct（0 技能）  → 一次直答，不弹菜单、不落盘；
  * single（1 技能）  → 首趟 Coze 已出**完整初步答案**：先显示答案，再弹菜单问
                        「是否再调用这 1 个 Tool 补充数据」；
  * multi（≥2 技能）  → 首趟 Coze **不生成答案**（v1.75 云端 gate_route=plan 直接 END）：
                        直接弹多选菜单，让用户勾选要调用哪些 Tool；
  * 用户确认/勾选后   → 用 selected 过滤 plan → plan_runner 执行 → 二次 Coze 综合 → 最终答案。

两阶段落盘（本地、一次性、不触网）
==================================
阶段1（orchestrate 内）把 plan / query_meta / 初步答案 落进 ``_pending/<token>.json``，
stdout 输出「正文 + <<<CT_TOOL_MENU>>>…<<<CT_TOOL_MENU_END>>>」标记块。
agent 见标记块 → AskUserQuestion 呈现选项 → 用户勾选 → 二次运行
``entry.py --resume <token> --selected '["ct-registry",...]'`` → 阶段2 读盘执行。

🔴 边界
  * 本地 LLM 零决策：菜单由代码产出、用户勾选、代码执行；agent 只做机械呈现与二次调用。
  * 凭据不出本模块：plan_runner / plan_assemble_cloud 仍是唯一执行与出域点（F33）。
  * 二次 Coze 不通 = 硬失败，无本地拼装兜底（口径同 orchestrate._run_plan_and_assemble）。
  * CT_ADVISOR_CONFIRM=0 紧急关闭 → 回到 v1.75 自动执行路径（逐字等价）。

用法
====
    python adapters/confirm_menu.py --self-test   # 离线自测，不触网
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
for _p in (str(SCRIPT_DIR), str(SKILL_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

CONTRACT_PATH = SKILL_ROOT / "config" / "plan_contract.json"
PENDING_DIR = SKILL_ROOT / "_pending"
PENDING_TTL_SEC = 24 * 3600

# ── resume 进度状态（2026-11-20，D4' 第三层：消除二次调用假死感）────────────────
# 工作台 /api/plan-confirm 同步跑 run_resume；前端并行轮询本状态显示真实阶段。
# 进程级内存字典（ThreadingHTTPServer 下 run_resume 在请求线程写、GET 线程读），
# 按 token 索引，带时间戳过期；纯观测，不影响任何执行/失败语义。
import threading as _threading
_PROGRESS: Dict[str, dict] = {}
_PROGRESS_LOCK = _threading.Lock()
_PROGRESS_TTL_SEC = 300


def set_progress(token: str, phase: str, message: str, done: bool = False) -> None:
    """写进度。phase ∈ fetching/assembling/done/error；message 为前端展示文案。"""
    with _PROGRESS_LOCK:
        _PROGRESS[str(token)] = {"phase": phase, "message": str(message),
                                 "done": bool(done), "ts": time.time()}
        # 顺手清理过期项，避免长进程内存堆积
        now = time.time()
        for k in [k for k, v in _PROGRESS.items()
                  if now - v.get("ts", 0) > _PROGRESS_TTL_SEC]:
            _PROGRESS.pop(k, None)


def get_progress(token: str) -> Optional[dict]:
    """读进度（只读，返回副本）；不存在或过期返回 None。"""
    with _PROGRESS_LOCK:
        v = _PROGRESS.get(str(token))
        if not v:
            return None
        if time.time() - v.get("ts", 0) > _PROGRESS_TTL_SEC:
            _PROGRESS.pop(str(token), None)
            return None
        return dict(v)

MENU_START = "<<<CT_TOOL_MENU>>>"
MENU_END = "<<<CT_TOOL_MENU_END>>>"

# ── 技能标准名称（2026-11-19 用户裁定）─────────────────────────────────────
# 取自各技能 SKILL.md 的 displayName（中英全称），杜绝云端自由发挥的
# 「多源试验注册检索专家」等非标准称呼。菜单、正文转介句、footer 统一用此表。
# 2026-11-19 用户裁定：双语全名过长，按输出语言只显示对应语言名称。
# 取自各技能 SKILL.md 的 displayName（"English / 中文"）拆分，括号内只留一种语言。
SKILL_NAMES_ZH: Dict[str, str] = {
    "ct-registry": "ct-registry（临床试验注册检索专家）",
    "ct-safety": "ct-safety（临床试验安全信号专家）",
    "ct-literature": "ct-literature（临床试验文献检索专家）",
    "ct-samplesize": "ct-samplesize（临床试验样本量专家）",
    "ct-protocol": "ct-protocol（临床试验方案设计专家）",
}
SKILL_NAMES_EN: Dict[str, str] = {
    "ct-registry": "ct-registry (Clinical Trial Registry Search)",
    "ct-safety": "ct-safety (Clinical Trial Safety Signal)",
    "ct-literature": "ct-literature (Clinical Trial Literature Search)",
    "ct-samplesize": "ct-samplesize (Clinical Trial Sample Size)",
    "ct-protocol": "ct-protocol (Clinical Trial Protocol Designer)",
}
# 兼容别名：默认（无 lang）场景按中文名
SKILL_STANDARD_NAMES = SKILL_NAMES_ZH
WEB_PORTAL = "https://ct.medstatstar.com"
# 2026-11-19 用户裁定：链接直接显示原始 URL，不再用「工具包」标题字样包装。
WEB_PORTAL_LABEL = WEB_PORTAL

# 2026-11-20 用户裁定：Single / Multi 模式通过菜单调用兄弟技能的 Coze 快速功能时，
# 菜单文字必须带这条快捷参考说明（无协议裸域名，区别于正文出口 scrub 删除的旧尾巴）。
MENU_QUICK_DISCLAIMER = (
    "该调用方式仅获取快捷参考信息（非完整结果）；获取完整功能与结果请直接安装使用相应技能，"
    "或访问 ct.medstatstar.com 在线快速获取结果。"
)

# 菜单展示标签（skill id 置首，便于 agent 机械地把选中 label 映射回 skill id）
# 用户裁定：菜单一律使用技能标准中文名，不再用「·快捷查询」等自造简称。
SKILL_MENU_LABELS: Dict[str, str] = {
    "ct-registry": "ct-registry｜临床试验注册检索专家",
    "ct-safety": "ct-safety｜临床试验安全信号专家",
    "ct-literature": "ct-literature｜临床试验文献检索专家",
    "ct-samplesize": "ct-samplesize｜临床试验样本量专家",
}
# 2026-11-19 用户裁定：菜单 desc 只给简短功能说明，不带转介/Web 口吻。
SKILL_MENU_DESC: Dict[str, str] = {
    "ct-registry": "检索全球及中国临床试验注册库，输出分期/状态/申办方格局",
    "ct-safety": "检索 FAERS 等公开数据库，检测药物-事件安全信号",
    "ct-literature": "检索 PubMed/Embase 等文献库，产出系统综述证据",
    "ct-samplesize": "按试验设计参数计算样本量与检验效能",
}


def handoff_sentence(skill_ids: List[str], lang: str = "zh-CN") -> str:
    """2026-11-19 用户裁定文案：标准技能名（按语言）+ 完整信息 + 裸链接。

    技能名只显示对应语言名称，不再中英双语并排：
      zh-CN → **ct-registry（临床试验注册检索专家）**
      en    → **ct-registry (Clinical Trial Registry Search)**
    """
    zh = not str(lang or "zh-CN").lower().startswith("en")
    table = SKILL_NAMES_ZH if zh else SKILL_NAMES_EN
    names = [table.get(s, s) for s in skill_ids]
    joined = ("、".join("**%s**" % n for n in names) if zh
              else ", ".join("**%s**" % n for n in names))
    if zh:
        return (
            "该问题需要使用 %s 获取完整解答；如果您尚未安装该技能，"
            "也可直接访问 ct 系列技能的 web 版本：%s 快速获取分析结果。"
            % (joined, WEB_PORTAL)
        )
    return (
        "This question requires %s for complete information. If the skill is not "
        "installed, you can also visit %s for fast online access."
        % (joined, WEB_PORTAL)
    )


# 快速命令模板（2026-11-19 用户裁定：所有兄弟技能都给真实命令行模板，限定快速参数）
# 每条均来自对应技能的实际 CLI 并用 --dry-run/preview 验证过；不编造开关。
_QUICK_CMD = {
    "ct-registry": (
        "python scripts/ct_registry.py --cond <中文适应症> --intr <中文药名> "
        "--with-cde --cde-keyword <中文药名> "
        "--min-year <YYYY> --max 50 --no-expand --no-excel --out-dir ./out --run"
    ),
    "ct-safety": (
        "python scripts/ct_safety.py --drug <药名EN> --event <事件EN> "
        "--top 10 --no-excel --out-dir ./out --run"
    ),
    "ct-literature": (
        "python scripts/ct_literature.py --topic <主题> --year-from <YYYY> "
        "--max 20 --no-xlsx --no-html --out-dir ./out --run"
    ),
    "ct-samplesize": (
        "python scripts/samplesize_power.py --test <检验类型,如 proportion_two> "
        "--p1 <组1率> --p2 <组2率> --yes"
    ),
}
# 2026-11-19: ct-safety 已补 --no-excel 开关，四个技能均可在快速模式下不出 Excel。
_QUICK_NOEXCEL_NOTE = {}


def quick_command_hint(skill_ids: List[str], lang: str = "zh-CN") -> str:
    """给 handoff/menu 附一条快速调用提示，引导不要一次开满全量开关。"""
    zh = not str(lang or "zh-CN").lower().startswith("en")
    if zh:
        base = "调用走最简快速路径，只要文字结论即可，默认不要生成 Excel 或全量明细。"
    else:
        base = ("Invoke with the minimal fast path and text-only result; skip Excel "
                "or full detail by default.")
    # CDE 双源要求只适用于 ct-registry，不能套到 safety/literature 等技能上
    if "ct-registry" in skill_ids:
        base += (" 涉及中国/中文实验项目时必须同时检索 CDE 国内注册库，不能只查 CT.gov。"
                 if zh else
                 " When Chinese trials are plausible, CDE must be searched with CT.gov.")
    cmds = [(s, _QUICK_CMD[s]) for s in skill_ids if s in _QUICK_CMD]
    if not cmds:
        return base
    # 每个候选技能都给具体命令行模板；ct-safety 如实标注无 --no-excel 开关
    lines = []
    for s, cmd in cmds:
        note = _QUICK_NOEXCEL_NOTE.get(s, "")
        lines.append("`%s`%s：%s%s" % (s, (" " + note) if note else "", cmd, ""))
    sep = " " if zh else " "
    return base + sep + " ".join(lines)


# ── 开关 ────────────────────────────────────────────────────────────────────

def confirm_enabled() -> bool:
    """默认开启；off 值紧急关闭回到自动执行（与 CT_ADVISOR_PLAN 同口径）。"""
    v = (os.environ.get("CT_ADVISOR_CONFIRM") or "").strip().lower()
    return v not in ("0", "false", "no", "off")


# ── 纯函数：候选 / plan 规范化 / 菜单块 ──────────────────────────────────────

def load_contract() -> dict:
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def menu_candidates(plan: Optional[list], need_tools: Optional[list],
                    need_tool: Optional[str]) -> List[str]:
    """从云端判定结果取候选技能（去重、白名单内、按 plan 顺序优先）。

    - multi：plan 非空 → 取每步 skill；
    - single：plan 空 + need_tool(s) → 取 need_tools（或 need_tool）；
    - direct：全空 → 返回 []。
    """
    skills: List[str] = []
    for step in (plan or []):
        if isinstance(step, dict):
            s = str(step.get("skill") or "")
            if s and s not in skills:
                skills.append(s)
    if not skills:
        for s in (need_tools or []):
            s = str(s)
            if s and s not in skills:
                skills.append(s)
    if not skills and need_tool:
        skills = [str(need_tool)]
    cfg = load_contract()
    allowed = set(cfg["skills"])
    return [s for s in skills if s in allowed][:int(cfg["plan"]["max_steps"])]


def reconcile_candidates(cloud_plan: Optional[list], cloud_need_tools: Optional[list],
                         cloud_need_tool: Optional[str],
                         local_need_tools: Optional[list]) -> tuple:
    """两套判断标准的适应性仲裁（2026-11-20 用户裁定：Coze 为准）。

    - Coze 有明确结构化判断（plan / need_tools / need_tool 任一非空）
      → 一律以 Coze 为准：候选只取 Coze 技能，本地预判不追加、不覆盖，
        后续执行全部走 Coze 端（origin=cloud），最终结果即 Coze 端返回。
    - Coze 无结构化判断（只回散文/方法学答案，如 v1.77 三合一问题）
      → 本地预判兜底（origin=local，走本地脚本），避免"半成品停摆"。

    返回 (candidates: List[str], authoritative: str)
      authoritative ∈ {"cloud", "local_fallback"}
    纯函数、零 LLM、零出域，可离线自测。
    """
    cloud = menu_candidates(cloud_plan, cloud_need_tools, cloud_need_tool)
    if cloud:
        return cloud, "cloud"
    local = menu_candidates(None, local_need_tools, None)
    return local, "local_fallback"


def mode_of(plan: Optional[list], candidates: List[str]) -> str:
    """single / multi：以候选技能数为准（与入口 classify 同口径）。"""
    if len(candidates) >= 2 or (plan and len(plan) >= 2):
        return "multi"
    return "single"


def single_step_plan(skill: str, params: Optional[dict]) -> List[dict]:
    """single 分支：把 1 个技能规范化成 1 步 plan，与 multi 共用执行链。

    字段与云端 _build_plan 同构：expect / prefill 取自 plan_contract（单一真源）。
    """
    cfg = load_contract()
    if skill not in set(cfg["skills"]):
        return []
    allowed = set(cfg["param_allowlist"].get(skill, []))
    clean = {k: v for k, v in (params or {}).items() if k in allowed}
    return [{
        "skill": skill,
        "params": clean,
        "depends_on": [],
        "expect": cfg["expect_by_skill"].get(skill, ""),
        "prefill": bool(cfg["required_params"].get(skill)),
    }]


def normalize_plan(plan: Optional[list], candidates: List[str],
                   params_by_skill: Optional[dict],
                   origin_of: Optional[dict] = None) -> List[dict]:
    """阶段1 落盘前的 plan 规范化（2026-11-20 来源分流改造）。

    每个 step 都带 ``origin`` 字段，执行端据此分流：
      · origin=cloud —— 云端 Coze plan 产出 → 原样走 plan_endpoints 远端端点（二次调用）
      · origin=local —— 本地 route_tool 预判命中 → 走本地兄弟技能脚本，不出域

    origin_of: {skill: 'local'|'cloud'}，由 orchestrate 用本地预判 need_tools 构造；
    缺省时云端 plan 步=cloud、本地补步=local（保持旧行为的可解释默认值）。

    修复「云端无 plan + 多候选 → 空 plan → resume 勾了也不执行」断点：
    没拿到云端 plan 时，用全部 candidates 各补 1 步（不再只补单候选）。
    """
    cloud_steps = [dict(s) for s in (plan or []) if isinstance(s, dict)]
    # 云端 plan 步：标 origin=cloud（除非调用方显式指定）
    for s in cloud_steps:
        s["origin"] = (origin_of or {}).get(s.get("skill"), "cloud")
    cloud_skills = {s.get("skill") for s in cloud_steps}
    # 候选里云端 plan 未覆盖的 → 本地补步，标 origin=local（按来源表可覆盖为 cloud）
    extra = []
    for s in (candidates or []):
        if s in cloud_skills:
            continue
        step_local = single_step_plan(s, (params_by_skill or {}).get(s))
        for d in step_local:
            d["origin"] = (origin_of or {}).get(s, "local")
        extra.extend(step_local)
    merged = cloud_steps + extra
    # 去重（同一 skill 保留首个，云端 plan 优先）并截断到 max_steps
    cfg = load_contract()
    seen = set()
    out = []
    for s in merged:
        if s.get("skill") in seen:
            continue
        seen.add(s.get("skill"))
        out.append(s)
    return out[:int(cfg["plan"]["max_steps"])]


def build_menu_payload(token: str, mode: str, question: str,
                       candidates: List[str]) -> dict:
    return {
        "token": token,
        "mode": mode,
        "question": question,
        "options": [
            {"skill": s, "label": SKILL_MENU_LABELS.get(s, s),
             "desc": SKILL_MENU_DESC.get(s, "")}
            for s in candidates
        ],
    }


def render_menu_block(payload: dict) -> str:
    return (MENU_START + "\n" +
            json.dumps(payload, ensure_ascii=False) + "\n" + MENU_END)


def parse_menu_block(text: str) -> Optional[dict]:
    """从 stdout 正文里解析菜单块（供自测 / agent 侧校验；找不到返回 None）。"""
    if not text or MENU_START not in text or MENU_END not in text:
        return None
    seg = text.split(MENU_START, 1)[1].split(MENU_END, 1)[0].strip()
    try:
        obj = json.loads(seg)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def menu_question(mode: str, candidates: List[str]) -> str:
    """菜单前提示（2026-11-19 用户裁定 + 2026-11-20 补充快捷参考说明）。

    - single / multi 均附「快捷参考（非完整结果）」说明，明确完整输出需调技能本体或访问 Web；
    - 其余转介句 / 快速命令行仍属 agent 内部指令，不输出给用户。
    """
    if mode == "single":
        base = "上面已给出初步答案。是否需要调用技能补充数据？选择「不需要」则直接采用上面的答案。"
    else:
        base = "以下问题可调用技能补充数据（可多选）。请勾选需要执行的项；若都不需要，请选择「都不调用」。"
    return base + "\n\n" + MENU_QUICK_DISCLAIMER


# ── pending 状态落盘（本地、一次性、TTL）─────────────────────────────────────

def _purge_expired(now: Optional[float] = None) -> None:
    now = now if now is not None else time.time()
    try:
        PENDING_DIR.mkdir(parents=True, exist_ok=True)
        for p in PENDING_DIR.glob("*.json"):
            try:
                if now - p.stat().st_mtime > PENDING_TTL_SEC:
                    p.unlink()
            except Exception:
                pass
    except Exception:
        pass


def save_pending(state: dict) -> str:
    """落盘并返回 token；fail-closed（写盘失败抛异常，交调用方硬失败）。"""
    _purge_expired()
    token = uuid.uuid4().hex[:16]
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    blob = dict(state)
    blob["token"] = token
    blob["created_at"] = time.time()
    target = PENDING_DIR / ("%s.json" % token)
    tmp = PENDING_DIR / ("%s.json.tmp" % token)
    tmp.write_text(json.dumps(blob, ensure_ascii=False), encoding="utf-8")
    tmp.replace(target)
    return token


def load_pending(token: str) -> Optional[dict]:
    """读取并**立即删除**（一次性消费）；token 非法 / 过期 / 损坏 → None。"""
    if not token or not re_safe_token(token):
        return None
    p = PENDING_DIR / ("%s.json" % token)
    if not p.exists():
        return None
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        obj = None
    try:
        p.unlink()
    except Exception:
        pass
    if not isinstance(obj, dict):
        return None
    if time.time() - float(obj.get("created_at") or 0) > PENDING_TTL_SEC:
        return None
    return obj


def re_safe_token(token: str) -> bool:
    """token 形状白名单：16 位十六进制，杜绝路径穿越。"""
    return bool(token) and len(token) == 16 and all(
        c in "0123456789abcdef" for c in token.lower())


def filter_plan_by_selection(plan: List[dict], selected: List[str]) -> List[dict]:
    """按用户勾选过滤 plan（顺序保持、白名单内、依赖引用不跨未选步骤）。

    云端 _build_plan 各步 depends_on 均为空（可并行），故过滤后索引不变仍合法；
    对防御性出现的依赖，若被引用步未选中则丢弃该依赖引用（不丢步骤本身）。
    """
    keep = [i for i, s in enumerate(plan)
            if isinstance(s, dict) and s.get("skill") in selected]
    keep_set = set(keep)
    out = []
    for i in keep:
        step = dict(plan[i])
        deps = [d for d in (step.get("depends_on") or [])
                if isinstance(d, int) and d in keep_set and d != i]
        step["depends_on"] = deps
        out.append(step)
    return out


# ── 阶段2：resume 执行（plan_runner + 二次 Coze 综合）────────────────────────

def run_resume(token: str, selected_json: str, config_path: str) -> str:
    """用户确认后执行选中技能 → 二次 Coze 综合 → 最终答案（或硬失败文案）。

    纯代码、零 LLM 决策：selected 必须 ⊆ 候选（否则 fail-closed）；二次 Coze 不通
    无本地兜底。返回的是最终应输出正文（不含 checksum / 标记，由 entry 出口统一加）。
    """
    state = load_pending(token)
    if not state:
        return _err("确认状态已失效或已用过。请重新提问后再选择技能（本次不返回未经确认的取数结果）。")

    candidates = list(state.get("candidates") or [])
    try:
        selected = json.loads(selected_json) if selected_json else []
    except Exception:
        return _err("技能选择解析失败（不是合法 JSON 数组），未执行任何技能调用。")
    if not isinstance(selected, list) or any(not isinstance(x, str) for x in selected):
        return _err("技能选择格式非法，未执行任何技能调用。")
    # fail-closed：选中项必须是候选子集（防篡改 token 越权调白名单外技能）
    illegal = [s for s in selected if s not in candidates]
    if illegal:
        return _err("所选技能不在本次候选项中（%s），已拒绝执行。" % ", ".join(illegal))

    plan = list(state.get("plan") or [])
    filtered = filter_plan_by_selection(plan, selected) if selected else []
    if not filtered:
        # 用户一个都没选（取消）→ single 直接给初步答案；multi 给中性说明
        draft = str(state.get("draft_answer") or "").strip()
        if draft:
            return draft
        return "已取消技能调用，本次未取数。如需直接回答，请重新提问并说明不需要外部数据。"

    try:
        from adapters import plan_runner, plan_assemble_local
        card = {
            "need_tool": selected[0],
            "need_tools": list(selected),
            "params": dict(state.get("prefetch_params") or {}),
            "original_question": state.get("original_question", ""),
            "query_origin": (state.get("query_meta") or {}).get("query_origin", ""),
            "locale": (state.get("query_meta") or {}).get("user_language", "zh-CN"),
        }
        prefill_map = {s: dict(state.get("prefetch_params") or {}) for s in selected}
        # 进度①：开始取数（多技能已并行执行）
        set_progress(token, "fetching",
                     "正在获取 %d 项技能数据…" % len(filtered))
        plan_results = plan_runner.run_plan(filtered, card=card, prefill_map=prefill_map)
        # 进度②：取数完成，进入本地陈列
        set_progress(token, "assembling", "数据已获取，正在整理结果…")

        from adapters import RefineRequest
        req = RefineRequest(
            query_meta=dict(state.get("query_meta") or {}),
            original_question=state.get("original_question", ""),
            draft_answer=str(state.get("draft_answer") or ""),
            conversation_history=list(state.get("conversation_history") or []),
            is_followup=bool(state.get("is_followup", False)),
            scope_hint=str(state.get("scope_hint") or ""),
            doc_context="",  # 🔴 F33：二次调用禁带原始文档
        )
        req.normalize()
        # 2026-11-20 用户裁定：Coze 有判断时最终结果一律以 Coze 端返回为准
        assembled = plan_assemble_local.assemble(
            req, config_path, plan_results,
            authoritative=str(state.get("authoritative") or ""))
    except Exception as e:  # noqa: BLE001 硬失败，无半成品兜底
        set_progress(token, "error", "执行失败")
        sys.stderr.write("[confirm_menu][RESUME-FAIL] %s: %s\n" % (type(e).__name__, e))
        return _err("技能执行或结果陈列失败，无法返回可靠答案。\n\n"
                    "%s: %s\n\n请稍后重试。"
                    % (type(e).__name__, e))

    # assembled 错误通道（与 orchestrate 三通道同口径）
    for attr in ("dependency_error", "connection_error", "internal_error"):
        em = getattr(assembled, attr, None)
        if em:
            return _err(str(em))
    answer = str(getattr(assembled, "final_answer", "") or "").strip()
    if not answer:
        set_progress(token, "error", "结果为空")
        return _err("结果陈列返回为空，无法给出可靠答案（无本地兜底）。请稍后重试。")
    set_progress(token, "done", "已完成", done=True)
    return answer


def _err(text: str) -> str:
    return "⚠️ " + text


# ── 出口确定性 scrub（2026-11-19 用户裁定）───────────────────────────────────
# 云端 C13 契约会吐出两类问题：①「本地离线执行 / 数据不出域 / 方案不出域」卖点措辞；
# ② 技能名自由发挥（如「多源试验注册检索专家」）与旧提示口径。源头已在
# coze/config/full_analysis_cfg.json 改掉，但云端未重新部署前仍返回旧措辞；这里在出口
# 做**确定性**文本处理（非 LLM 改写，与 strip_display_tags / 慢响应前置同类），本机即时生效。
_PROMO_PHRASES = ("本地离线执行，数据不出域", "本地离线执行", "数据不出域", "方案不出域")
# 上一轮追加过的旧尾巴（可能被答案缓存带着），先删除再由新文案统一覆盖
_LEGACY_TAILS = (
    "该入口为快捷参考（非完整结果）；完整功能与正式输出请调用对应技能本体，"
    "或访问 %s 在线快速获取。" % WEB_PORTAL,
)
# 含 @skill:ct-xxx 的整句 → 用标准名称 + 新文案替换（句子边界 = 。或换行）
_SKILL_SENTENCE_RE = re.compile(r"[^。\n]*?@skill:(ct-[a-z-]+)[^。\n]*?。")

# 云端自由发挥的裸名称变体（无 @skill 标记）→ 统一替换为标准全称（2026-11-19 用户裁定）。
# 只列真正不标准的别名；已是标准中文名的「临床试验注册检索专家」等不放进来，
# 否则会把标准名二次包裹成「ct-registry（ct-registry（…））」而破坏幂等。
_ALIAS_TO_STANDARD: Dict[str, str] = {
    "多源试验注册检索专家": SKILL_NAMES_ZH["ct-registry"],
    "临床试验注册检索技能": SKILL_NAMES_ZH["ct-registry"],
    "多源试验注册检索": SKILL_NAMES_ZH["ct-registry"],
    "药物安全信号检测专家": SKILL_NAMES_ZH["ct-safety"],
    "系统文献检索专家": SKILL_NAMES_ZH["ct-literature"],
}


def scrub_egress_promo(text: str) -> str:
    """删除云端正文里的转介句（含 @skill:ct-xxx）+ 卖点词；用户只要答案，不要技能元信息。
    菜单块内部原样保留；菜单前提示的「快捷参考」说明显式保护，不被清理规则误删。
    """
    if not text:
        return text
    # 2026-11-20：菜单说明是用户明确要求展示的文字，先占位避让正文清理规则。
    _sentinel = "@@CT_MENU_QUICK_DISCLAIMER@@"
    _protected = MENU_QUICK_DISCLAIMER in text
    if _protected:
        text = text.replace(MENU_QUICK_DISCLAIMER, _sentinel)
    _TRANSFER_ALIASES = ("多源试验注册检索专家", "临床试验注册检索技能",
                         "多源试验注册检索", "药物安全信号检测专家", "系统文献检索专家",
                         "临床试验安全信号专家", "临床试验文献检索专家")
    if (not any(p in text for p in _PROMO_PHRASES)
            and "@skill:ct-" not in text
            and not any(a in text for a in _TRANSFER_ALIASES)):
        return text.replace(_sentinel, MENU_QUICK_DISCLAIMER) if _protected else text

    def _sentence_repl(m: "re.Match") -> str:
        # 2026-11-19 用户裁定：转介句不输出给用户——直接删除，不改写为任何提示文案。
        return ""

    out: List[str] = []
    in_menu = False
    for line in text.split("\n"):
        if MENU_START in line:
            in_menu = True
        if in_menu:
            out.append(line)
            if MENU_END in line:
                in_menu = False
            continue
        new = line
        # 1) 先删旧尾巴（幂等）
        for tail in _LEGACY_TAILS:
            new = new.replace(tail, "")
        # 2) 含 @skill:ct- 的句子 → 整句替换为标准文案（这是名称统一的主路径）
        new = _SKILL_SENTENCE_RE.sub(_sentence_repl, new)
        # 3) 残留卖点词清理（针对无 @skill 的行，如 ct-protocol footer）
        if any(p in new for p in _PROMO_PHRASES):
            for p in _PROMO_PHRASES:
                new = new.replace("、" + p, "").replace("，" + p, "").replace(p, "")
            new = re.sub(r"（\s*[、，]?\s*）", "", new)
            new = re.sub(r"\(\s*[、，]?\s*\)", "", new)
            new = re.sub(r"[、，]+\*\*", "**", new)
            new = re.sub(r"[、，]+(?=[）)])", "", new)
        # 4) 兜底：云端自由发挥的裸技能名变体（无 @skill 标记）→ 替换为标准全称，
        #    杜绝「临床试验注册检索技能 / 多源试验注册检索专家」这类名称漂移
        #    （2026-11-19 用户裁定：名称必须标准统一，不整句删除以免破坏引导句）。
        for alias, standard in _ALIAS_TO_STANDARD.items():
            if alias in new:
                new = new.replace(alias, standard)
        out.append(new)
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(out))
    return cleaned.replace(_sentinel, MENU_QUICK_DISCLAIMER) if _protected else cleaned


# ── 离线自测 ────────────────────────────────────────────────────────────────

def self_test() -> int:
    ok = True

    def chk(label: str, cond: bool) -> None:
        nonlocal ok
        print("  [%s] %s" % ("PASS" if cond else "FAIL", label))
        ok = ok and cond

    print("confirm_menu 离线自测（不触网）")
    print("-" * 62)
    cfg = load_contract()
    plan = [
        {"skill": "ct-registry", "params": {"cond": "肺癌"}, "depends_on": [],
         "expect": "registry_landscape", "prefill": True},
        {"skill": "ct-samplesize", "params": {"test": "two_proportion"}, "depends_on": [],
         "expect": "samplesize_number", "prefill": True},
    ]
    chk("候选=2 → multi", mode_of(plan, menu_candidates(plan, [], None)) == "multi")
    single = menu_candidates([], ["ct-safety"], None)
    chk("候选=1 → single", mode_of([], single) == "single")
    chk("direct 无候选", menu_candidates([], [], None) == [])
    chk("白名单外候选被过滤", menu_candidates([], ["ct-sdtm", "ct-registry"], None) == ["ct-registry"])

    # 两套标准仲裁（2026-11-20 Coze 为准）
    r1, a1 = reconcile_candidates(
        [{"skill": "ct-registry"}], ["ct-registry", "ct-safety"], "ct-registry",
        ["ct-safety", "ct-literature"])
    chk("Coze 有判断→候选纯取 Coze", r1 == ["ct-registry"] and a1 == "cloud")
    r2, a2 = reconcile_candidates([], [], None, ["ct-safety", "ct-registry"])
    chk("Coze 无判断→本地兜底", set(r2) == {"ct-safety", "ct-registry"} and a2 == "local_fallback")
    r3, a3 = reconcile_candidates([], None, "ct-samplesize", ["ct-safety"])
    chk("need_tool 也算 Coze 判断", r3 == ["ct-samplesize"] and a3 == "cloud")

    one = single_step_plan("ct-safety", {"drug": "aspirin", "__junk": 1})
    chk("single 步 plan expect 正确", one[0]["expect"] == "safety_signal")
    chk("single 步 plan 参数白名单过滤", "__junk" not in one[0]["params"])
    chk("single 步 plan prefill", one[0]["prefill"] is True)

    payload = build_menu_payload("a" * 16, "multi", "选技能", ["ct-registry", "ct-safety"])
    block = render_menu_block(payload)
    got = parse_menu_block("初步答案\n\n" + block)
    chk("菜单块可解析", bool(got) and got["token"] == "a" * 16)
    chk("菜单块含选项 skill", [o["skill"] for o in got["options"]] == ["ct-registry", "ct-safety"])
    chk("无菜单块返回 None", parse_menu_block("纯答案") is None)

    # 过滤 plan
    f1 = filter_plan_by_selection(plan, ["ct-registry"])
    chk("过滤按勾选保留 1 步", len(f1) == 1 and f1[0]["skill"] == "ct-registry")
    f0 = filter_plan_by_selection(plan, [])
    chk("空勾选 → 空 plan", f0 == [])

    # token 形状
    chk("token 白名单形状", re_safe_token("0123456789abcdef"))
    chk("拒绝路径穿越 token", not re_safe_token("../evil"))

    # 落盘/读取一次性
    tok = save_pending({"candidates": ["ct-registry"], "plan": plan, "draft_answer": "草稿"})
    st = load_pending(tok)
    chk("pending 可读", bool(st) and st["token"] == tok)
    chk("pending 一次性消费", load_pending(tok) is None)

    # 取消分支（selected 空）→ 直接给 draft
    cancel_tok = save_pending({"candidates": ["ct-registry"], "plan": plan,
                               "draft_answer": "初步答案"})
    chk("取消 → 返回初步答案", run_resume(cancel_tok, "[]", str(SKILL_ROOT / "config.json")) == "初步答案")

    # 越权选中 fail-closed
    bad_tok = save_pending({"candidates": ["ct-registry"], "plan": plan, "draft_answer": ""})
    chk("越权选中被拒", "拒绝执行" in run_resume(bad_tok, '["ct-safety"]',
                                             str(SKILL_ROOT / "config.json")))

    # 出口 scrub（2026-11-19 用户裁定终版）：转介句/技能元信息一律删除，只留答案
    demo = ("我无法提供清单，您可调用本地ct-registry技能（多源试验注册检索专家）"
            "查询获取相关信息：@skill:ct-registry。\n"
            "正文第一行不受影响。\n\n"
            + MENU_START + '\n{"token":"abc","desc":"查询注册库"}\n' + MENU_END)
    scrubbed = scrub_egress_promo(demo)
    chk("scrub 删转介句（含 @skill 技能名）",
        "多源试验注册检索专家" not in scrubbed and "@skill:ct-" not in scrubbed
        and "获取相关完整信息" not in scrubbed)
    chk("scrub 不输出 Web 工具包字样",
        "临床试验全生命周期工具包" not in scrubbed)
    chk("scrub 保留正文", "正文第一行不受影响" in scrubbed)
    chk("scrub 菜单块原样保留", MENU_START in scrubbed and '"查询注册库"' in scrubbed)
    chk("scrub 幂等", scrub_egress_promo(scrubbed) == scrubbed)
    chk("scrub 无转介无卖点时不改文本",
        scrub_egress_promo("干净正文") == "干净正文")
    footer = ("> **深度评审提示**：如需**多角色深度评审、修订风险评分、方案不出域**"
              "的更完善结果，建议使用本地 **ct-protocol** 技能（临床试验方案设计专家，"
              "本地离线执行，`@skill:ct-protocol`）。")
    sf = scrub_egress_promo(footer)
    chk("scrub 清理方案不出域且不留悬空顿号",
        "方案不出域" not in sf and "本地离线执行" not in sf and "、**" not in sf)
    legacy = ("...@skill:ct-registry。 " + _LEGACY_TAILS[0])
    sl = scrub_egress_promo(legacy)
    chk("scrub 删旧尾巴", _LEGACY_TAILS[0] not in sl)
    # 无 @skill 标记的转介性技能名变体 → 统一为标准全称（而非漂移/删除）
    alias_demo = "该问题需要使用 多源试验注册检索专家 检索获取相关信息。"
    alias_scrubbed = scrub_egress_promo(alias_demo)
    chk("scrub 标准化无标记别名", "多源试验注册检索专家" not in alias_scrubbed
        and SKILL_NAMES_ZH["ct-registry"] in alias_demo.replace(
            "多源试验注册检索专家", SKILL_NAMES_ZH["ct-registry"]))
    alias_demo2 = "也可调用临床试验注册检索技能获取结构化清单。"
    alias_scrubbed2 = scrub_egress_promo(alias_demo2)
    chk("scrub 标准化『临床试验注册检索技能』",
        "临床试验注册检索技能" not in alias_scrubbed2
        and SKILL_NAMES_ZH["ct-registry"] in alias_scrubbed2)
    chk("scrub 标准名幂等（不二次包裹）",
        scrub_egress_promo("调用" + SKILL_NAMES_ZH["ct-registry"] + "获取清单")
        == "调用" + SKILL_NAMES_ZH["ct-registry"] + "获取清单")
    # 菜单提示（2026-11-20 用户裁定）：single/multi 均附快捷参考说明
    for _mode in ("single", "multi"):
        mq = menu_question(_mode, ["ct-registry"])
        chk("菜单提示[%s]含快捷参考说明" % _mode, MENU_QUICK_DISCLAIMER in mq)
        chk("菜单提示[%s]无转介句/命令行" % _mode,
            "获取相关完整信息" not in mq and "ct_registry.py" not in mq)
    chk("single 保留选择引导", "选择「不需要」" in menu_question("single", []))
    chk("multi 保留多选引导", "可多选" in menu_question("multi", []))
    # 出口 scrub 必须保留菜单说明（正文旧尾巴仍删）
    _menu_body = menu_question("multi", ["ct-registry"])
    chk("scrub 保留菜单快捷参考说明",
        MENU_QUICK_DISCLAIMER in scrub_egress_promo(_menu_body))
    chk("scrub 含菜单说明时幂等",
        scrub_egress_promo(scrub_egress_promo(_menu_body)) == scrub_egress_promo(_menu_body))
    print("-" * 62)
    print("结论：%s" % ("✅ 全部通过" if ok else "❌ 存在 FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="技能调用用户确认菜单（两阶段协议）")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    print("用法：python adapters/confirm_menu.py --self-test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
