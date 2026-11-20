#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plan_runner.py — Plan 校验器 + 拓扑执行器（2026-11-18，纯代码、零 LLM）。

职责
====
Coze 在 full_analysis 判断「答不了」后由 tool_router 产出结构化 plan；
本模块是本地侧的确定性守门人与执行者：

  _validate(plan)  —— 白名单（仅 4 个 A 档）/ 参数 fail-closed / 依赖无环 /
                       步数 ≤5 / expect 枚举。任一违规 fail-closed。
  run_plan(plan, card) —— 拓扑序调用 plan_endpoints.call_step，产出 plan_results。
                        单步失败仅该步标 status=error，其余继续；不设整体回落。

设计约束
========
* 本地 LLM 零决策：plan 的校验、补齐、执行、结果封装全程代码。
* 凭据不在本模块：调用器 plan_endpoints 从本地 coze_token_embedded 读取。
* 失败语义：主 Coze 不通在 orchestrate 已硬失败（与本模块无关）；本模块的
  单步失败是「该步 status=error」，交二次 Coze 据实说明，绝不伪造 0 结果，
  也不叫「回落」（清单 §5 红线 3）。
* 不做真实参数推断：prefill=true 的必填参数由调用方（orchestrate）用本地
  route_tool 预判结果补齐后传入；本模块只做白名单过滤与缺失检测。

用法
====
    python adapters/plan_runner.py --self-test   # 离线自测，不触网
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
for _p in (str(SCRIPT_DIR), str(SKILL_ROOT), str(SCRIPTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

CONTRACT_PATH = SKILL_ROOT / "config" / "plan_contract.json"


def load_contract() -> dict:
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _runs_local(skill: str) -> bool:
    """本地/云端分流的唯一判据（2026-11-20 用户裁定）：装了就调本地技能，没装才走云端。

    与技能来源 origin（谁建议的）/ 权威源 authoritative 无关——那些只管「调哪些」。
    CT_ADVISOR_FORCE_CLOUD=1 强制全走云端，仅供离线自测隔离。
    """
    if os.environ.get("CT_ADVISOR_FORCE_CLOUD", "").strip() == "1":
        return False
    skill = str(skill or "")
    if not skill:
        return False
    try:
        from handle_need_tool import _client_callable
        return bool(_client_callable(skill))
    except Exception:  # noqa: BLE001 - 探测失败按未装处理，回落云端
        return False


class PlanValidationError(ValueError):
    """Plan 契约违约（fail-closed，由调用方按硬失败处理）。"""


def _filter_params(skill: str, params: dict, cfg: dict) -> Dict[str, Any]:
    """参数白名单过滤：未知键直接丢弃（fail-closed）。"""
    allowed = cfg["param_allowlist"].get(skill, [])
    return {k: v for k, v in (params or {}).items() if k in allowed}


def _validate(plan: List[dict], cfg: dict) -> List[dict]:
    """校验并规范化 plan。违规抛 PlanValidationError（fail-closed）。

    返回规范化后的步骤列表（参数已按白名单过滤、字段补全）。
    """
    if not isinstance(plan, list):
        raise PlanValidationError("plan 非列表")
    max_steps = int(cfg["plan"]["max_steps"])
    if len(plan) > max_steps:
        raise PlanValidationError("plan 步数 %d > %d" % (len(plan), max_steps))

    skills = set(cfg["skills"])
    expect_enum = set(cfg["plan"]["expect_enum"])
    normalized = []
    for i, step in enumerate(plan):
        if not isinstance(step, dict):
            raise PlanValidationError("step[%d] 非 dict" % i)
        skill = str(step.get("skill") or "")
        if skill not in skills:
            raise PlanValidationError("step[%d] 技能 %s 不在白名单" % (i, skill))
        expect = str(step.get("expect") or "")
        if expect not in expect_enum:
            raise PlanValidationError("step[%d] expect %s 非法" % (i, expect))
        deps = step.get("depends_on") or []
        if not isinstance(deps, list):
            raise PlanValidationError("step[%d] depends_on 非列表" % i)
        for d in deps:
            if not isinstance(d, int) or d < 0 or d >= len(plan) or d == i:
                raise PlanValidationError("step[%d] 依赖索引 %r 非法" % (i, d))
        if isinstance(step.get("params"), dict):
            params = _filter_params(skill, step["params"], cfg)
        else:
            params = {}
        normalized.append({
            "skill": skill,
            "params": params,
            "depends_on": [int(d) for d in deps],
            "expect": expect,
            "prefill": bool(step.get("prefill", False)),
            # 2026-11-20 来源分流：cloud=走远端端点（英文化补齐）；local=走本地脚本（保留中文原文）
            "origin": str(step.get("origin") or "cloud"),
        })

    # 依赖环检测（Kahn 拓扑排序）
    n = len(normalized)
    indeg = [0] * n
    graph: List[List[int]] = [[] for _ in range(n)]
    for i, step in enumerate(normalized):
        for d in step["depends_on"]:
            graph[d].append(i)
            indeg[i] += 1
    queue = [i for i in range(n) if indeg[i] == 0]
    seen = 0
    while queue:
        u = queue.pop(0)
        seen += 1
        for v in graph[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    if seen != n:
        raise PlanValidationError("plan 依赖存在环")
    return normalized


def _topo_order(steps: List[dict]) -> List[int]:
    """返回拓扑序索引列表（同层按原顺序，确定性）。"""
    n = len(steps)
    indeg = [0] * n
    graph: List[List[int]] = [[] for _ in range(n)]
    for i, step in enumerate(steps):
        for d in step["depends_on"]:
            graph[d].append(i)
            indeg[i] += 1
    queue = [i for i in range(n) if indeg[i] == 0]
    order = []
    while queue:
        u = queue.pop(0)
        order.append(u)
        for v in graph[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    return order


def _prefill_params(steps: List[dict], prefill_map: dict, cfg: dict) -> None:
    """用本地 route_tool 预判结果补齐 prefill=true 的必填参数（原地修改）。

    prefill_map: {skill: {param: value}}，由 orchestrate 从 need_tool 卡片构造。
    补齐后仍缺失的必填参数不在此报错——交由 endpoint 调用器报 MISSING_REQUIRED，
    该步标 status=error，交二次 Coze 据实说明（不伪造）。
    """
    for step in steps:
        if not step["prefill"]:
            continue
        skill = step["skill"]
        extra = (prefill_map or {}).get(skill) or {}
        allowed = cfg["param_allowlist"].get(skill, [])
        for k, v in extra.items():
            if k in allowed and k not in step["params"]:
                step["params"][k] = v


_TERM_MAP_PATH = SKILL_ROOT.parent / "ct-base" / "references" / "term_map.json"


def _load_term_map() -> Dict[str, str]:
    """读 ct-base 权威中英术语映射（只读文件，禁跨技能 import §20.19.6）。"""
    try:
        with open(_TERM_MAP_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001 - 映射缺失时降级为空，不阻断
        return {}


def _zh_drug_to_en(text: str, term_map: Dict[str, str]) -> str:
    """从中文问句里抽药物名（单抗/抑制剂/药等后缀），用 term_map 映射成英文通用名。

    只遍历 term_map 里**含药物后缀**的中文键，避免命中「adverse events」等噪声词；
    多个命中取最长（最具体）者。
    """
    _DRUG_SUFFIX = ("单抗", "抑制剂", "抗体", "肽", "药物", "类似物")
    hits = [(zh, en) for zh, en in term_map.items()
            if zh.endswith(_DRUG_SUFFIX) and zh in (text or "")
            and isinstance(en, str) and en.strip()]
    if not hits:
        return ""
    hits.sort(key=lambda x: len(x[0]), reverse=True)
    return hits[0][1].strip()


# 中文不良事件 → 英文（openFDA reactionmeddrapt 认英文 MedDRA 术语）。
# term_map 的精确词（肝毒性/肾毒性/急性肾损伤…）优先；此处补「X损伤」等组合词。
# 2026-11-19 用户裁定：L0 速览 repeatedly 无 event → 无 2×2 → 无数值（等于没做）。
_AE_ZH2EN: Dict[str, str] = {
    "肝损伤": "hepatotoxicity",
    "肝功能损伤": "hepatotoxicity",
    "肝损害": "hepatotoxicity",
    "肝功能异常": "hepatotoxicity",
    "肝肾损伤": "hepatotoxicity",       # 组合词：brief 单事件能力边界，取肝为主；完整双事件由 ct-safety 本体
    "肾损伤": "acute kidney injury",       # FAERS 实测 nephrotoxicity 返 404，标准 PT 用 AKI
    "肾功能损伤": "acute kidney injury",
    "肾损害": "acute kidney injury",
    "肝功能衰竭": "hepatic failure",
    "肝衰竭": "hepatic failure",
    "免疫相关肝损伤": "immune-mediated hepatic disorder",
}
# term_map 里可作 event 的不良事件键（值含英文）；按长度降序优先精确匹配
_AE_EXACT_KEYS = (
    "急性肾损伤", "免疫相关不良事件", "间质性肺疾病", "间质性肺病",
    "甲状腺功能亢进", "甲状腺功能减退", "心脏毒性", "特发性肺纤维化",
    "肝毒性", "肾毒性",
)


def _zh_event_to_en(text: str, term_map: Dict[str, str]) -> str:
    """从中文问句抽不良事件并映射成英文 MedDRA 术语（用于 ct-safety 的 event）。

    优先级：term_map 精确长词 > _AE_ZH2EN 组合词（都按长度降序取最长命中）。
    只返回单个事件——brief(advisor_safety_brief) 的 faers_node 一次只算一个 2×2；
    多事件/完整分层由 ct-safety 本体承担（用户只要速览数值时可由此得到 PRR/ROR）。
    """
    if not text:
        return ""
    cands: List[tuple] = []
    # 1) term_map 精确词（英文值）
    for zh in _AE_EXACT_KEYS:
        en = term_map.get(zh)
        if zh in text and isinstance(en, str) and en.strip():
            cands.append((len(zh), en.strip()))
    # 2) 组合词
    for zh, en in _AE_ZH2EN.items():
        if zh in text:
            cands.append((len(zh), en))
    if not cands:
        return ""
    cands.sort(key=lambda x: x[0], reverse=True)
    en = cands[0][1]
    # FAERS 实测：nephrotoxicity 不是 reactionmeddrapt 有效 PT（openFDA 404），
    # 统一换成标准 PT acute kidney injury，否则 L0 仍拿不到 2×2。
    if en.lower() == "nephrotoxicity":
        en = "acute kidney injury"
    return en


# ── 检索词翻译：ct-base 单一入口（2026-11-20 家族统一）──────────────────────
# 🔴 翻译实现唯一真源 = ct-base/scripts/kw_localize.py。本模块只做「定位 + 调用」，
# 绝不复制实现、绝不跨技能加载 ct-literature/topic_translator（发布包无该兄弟目录）。
# 按目标分流输出形态：
#   - 注册库国外源（who/ctgov/ictrp/eu_ctr/isrctn/drks）→ 中译英「干净单术语」
#   - 注册库国内源（cde/chictr）→ 保留中文
#   - 文献库（literature/openalex/europepmc/pubmed）→ 中译英 + 同义词 OR 扩展
# 定位顺序：开发态 ct-base 兄弟目录真源 → 发布态本技能 vendored 同份副本（md5 一致）。
_KW_BASE = None
_KW_BASE_TRIED = False

# 中文修饰词（翻译后残留不影响检索，但剥离后更精准）
_SEARCH_NOISE = re.compile(r"\b(?:treatment|therapy|effect| study| the| a| of)\b", re.I)

# 文献库目标（走 OR 扩展）；其余目标走注册库干净术语
_LITERATURE_TARGETS = {"literature", "openalex", "europepmc", "pubmed", "pmc", "scihub"}
# 国内源（保留中文）
_DOMESTIC_TARGETS = {"cde", "chictr"}


def _load_kw_base():
    """唯一定位 ct-base kw_localize（开发态真源 / 发布态 vendored 副本）；失败 None。"""
    global _KW_BASE, _KW_BASE_TRIED
    if _KW_BASE_TRIED:
        return _KW_BASE
    _KW_BASE_TRIED = True
    try:
        import importlib as _il
        for _d in (SKILL_ROOT.parent / "ct-base" / "scripts",
                   SKILL_ROOT.parent.parent / "ct-base" / "scripts",
                   SKILL_ROOT / "scripts"):
            if (_d / "kw_localize.py").is_file():
                if str(_d) not in sys.path:
                    sys.path.insert(0, str(_d))
                _KW_BASE = _il.import_module("kw_localize")
                break
        return _KW_BASE
    except Exception:  # noqa: BLE001 - 基座不可用 → 降级原文
        return None


def _localize_search(text: str, target: str) -> str:
    """ct-base 单一入口：按目标站点把中文检索词本地化为对应形态。

    target ∈ 注册库源(who/ctgov/cde/chictr/...) 或 文献源(literature/openalex/...)。
    返回本地化后的字符串；ct-base 不可用/翻译失败时降级原文（不伪造）。
    """
    text = str(text or "").strip()
    if not text:
        return text
    kw = _load_kw_base()
    if kw is None:
        sys.stderr.write("[plan-runner] ct-base kw_localize 不可用，翻译降级原文\n")
        return text
    try:
        if target in _LITERATURE_TARGETS:
            # 已是英文无需翻译（CJK 短路，无中文直接原文返回）
            if not any("\u4e00" <= c <= "\u9fff" for c in text):
                return text
            info = kw.localize_literature(text, online_fallback=True)
            en = str(info.get("topic_en") or "").strip()
            if not en:
                return text
            for zh in (info.get("untranslated") or []):
                en = en.replace(zh, " ")
            en = _SEARCH_NOISE.sub(" ", en)
            en = re.sub(r"\s+", " ", en).strip()
            en = re.sub(r"\)\s*(?=[A-Za-z])", ") ", en)
            # 不 strip("()")：开头左括号是 OR 表达式的一部分
            return en or text
        # 注册库干净单术语（国内源保留中文由 ct-base SOURCE_LANG 决定）
        result, _src = kw.localize_for_source(text, target)
        return str(result or text).strip()
    except Exception as exc:  # noqa: BLE001 - 翻译降级原文，绝不阻断主流程
        sys.stderr.write("[plan-runner] ct-base 翻译失败(%s)，降级原文\n" % type(exc).__name__)
        return text


def _enrich_domain_params(steps: List[dict], card: dict, cfg: dict) -> None:
    """领域参数补齐（2026-11-19 用户裁定，纯代码确定性、零 LLM）：

    1. ct-registry：中文问题且已抽到 cond → 补 with_cde=true + cde_keyword=cond，
       保证中国药/中国适应症连 CDE 国内注册库一起检索（brief 端点已支持该开关）。
    2. ct-safety：必填 drug 缺失时，用 term_map 把中文药名映射成英文通用名后填入
       （openFDA 只认英文名，硬填中文会零命中，故只填可信映射命中的英文）。
    3. ct-safety：event 缺失时，用中文不良事件→英文 MedDRA 映射填入（2026-11-19 修复：
       此前从不抽 event → faers_node 无 event → 无 2×2 → L0 零数值，等于没做）。
    4. 检索词翻译（2026-11-19 B2）：literature 的 topic、registry 的 cond 含中文时
       翻成英文（brief 端点 openalex/europepmc/CT.gov 只认英文，中文命中 0）。
       registry 的 cde_keyword 保留中文（CDE 国内源要中文检索）。
    """
    q = str((card or {}).get("original_question") or "")
    is_zh = any("\u4e00" <= c <= "\u9fff" for c in q)
    term_map = _load_term_map() if is_zh else {}
    for step in steps:
        skill = step.get("skill")
        # 2026-11-20 装机分流：装了技能→走本地脚本（自带检索词中英本地化）→
        # 跳过"英文化翻译"（registry/literature 的 cond/intr/topic）；没装→走云端
        # brief 端点（只认英文）→需英文化。与 origin 来源标记无关。
        # ⚠️ 2026-11-20 修复：跳过英文化 ≠ 跳过必填参数补齐。ct-safety 的 drug/event
        # 是 openFDA 硬要求的英文通用名，本地脚本无 openFDA 中英映射（--drug-cn 只给
        # CN-PV），若不补 → MISSING_REQUIRED:drug 直接取数失败。故本地分支只跳过
        # "英文化"，safety 的必填映射补齐仍要执行；literature topic 为空时也要从
        # question 补中文主题（本地脚本自带 topic_translator 会翻英）。
        local = _runs_local(skill)
        params = step.get("params")
        if not isinstance(params, dict):
            continue
        allowed = set(cfg["param_allowlist"].get(skill, []))
        if skill == "ct-registry" and is_zh:
            cond = str(params.get("cond") or "").strip()
            intr = str(params.get("intr") or "").strip()
            if cond:
                # 基线补齐（2026-11-19 裁定，纯代码确定性）：
                # with_cde=true 打开国内 CDE 支路；cde_keyword 优先用药名中文（intr），
                # 无 intr 时才退回疾病中文（cond）——CDE 国内源要中文检索。
                if "with_cde" in allowed and "with_cde" not in params:
                    params["with_cde"] = True
                if "cde_keyword" in allowed and not str(params.get("cde_keyword") or "").strip():
                    params["cde_keyword"] = intr or cond   # 国内源：药名中文优先
                # 国外源（WHO/CT.gov/ICTRP）一律中译英——统一基座 ct-base kw_localize。
                # 本地脚本自带本地化 → 保留中文原词，不在此英文化。
                if not local:
                    if "cond" in allowed:
                        params["cond"] = _localize_search(cond, "who")
                    if intr and "intr" in allowed:
                        params["intr"] = _localize_search(intr, "who")
        elif skill == "ct-literature" and is_zh:
            topic = str(params.get("topic") or "").strip()
            if not topic:
                # 本地预判只给通用 {cond,intr}（在 card.params，经 allowlist 过滤后
                # step.params 里已无这两键）→ 拼成干净检索主题，不用整句问话：
                # 整句会把"在研临床试验""安全信号"等噪声带进 openalex 检索。
                # 本地脚本自带 topic_translator 翻英；云端则下方英文化。
                generic = (card.get("params") or {}) if isinstance(card, dict) else {}
                intr = str(generic.get("intr") or params.get("intr") or "").strip()
                cond = str(generic.get("cond") or params.get("cond") or "").strip()
                topic = " ".join(x for x in (intr, cond) if x).strip() or q[:80]
            if topic and "topic" in allowed:
                # 本地脚本自带翻译 → 传中文原词；云端端点只认英文 → 英文化。
                params["topic"] = topic if local else _localize_search(topic, "literature")
        elif skill == "ct-safety":
            # openFDA 只认英文通用名/MedDRA PT，本地脚本无中英映射（--drug-cn 仅给 CN-PV）。
            # 必填补齐与执行路径无关，本地/云端都要做；复用 ct-base term_map（单一真源）。
            if not str(params.get("drug") or "").strip():
                en = _zh_drug_to_en(q, term_map)
                if en and "drug" in allowed:
                    params["drug"] = en
            if not str(params.get("event") or "").strip():
                ev = _zh_event_to_en(q, term_map)
                if ev and "event" in allowed:
                    params["event"] = ev


def _levels(steps: List[dict]) -> List[int]:
    """步骤依赖层级：level=0 无依赖；有依赖则 = max(前置 level)+1。

    同层步骤互不依赖 → 可安全并发；层间按 level 升序串行。_validate 已保证
    依赖索引合法且无环，故用拓扑序动态推进即可（不依赖索引先后顺序）。
    """
    n = len(steps)
    order = _topo_order(steps)
    lvl = [0] * n
    for i in order:
        deps = steps[i]["depends_on"]
        if deps:
            lvl[i] = max(lvl[d] for d in deps) + 1
    return lvl


def _parallel_enabled() -> bool:
    """multi 取数并行开关：默认开启；CT_ADVISOR_PLAN_PARALLEL=0 可回滚串行。

    并发只针对同层无依赖步骤；call_step 无共享可变状态、结果写独立 results[idx]，
    异常由 call_step 内部吞掉返回 error 封装，故线程安全。
    """
    val = os.environ.get("CT_ADVISOR_PLAN_PARALLEL", "").strip().lower()
    return val not in ("0", "false", "no", "off")


def run_plan(plan: List[dict], card: Optional[dict] = None,
             prefill_map: Optional[dict] = None,
             contract: Optional[dict] = None) -> List[dict]:
    """校验并按依赖拓扑执行 plan，返回 plan_results（每步统一结果封装）。

    调度（2026-11-20 性能改造）：无依赖的同层步骤并发（ThreadPoolExecutor），
    层间按拓扑序串行；结果一律写回 results[原 plan 索引]，最终按原始顺序返回，
    与串行版逐字一致。CT_ADVISOR_PLAN_PARALLEL=0 可回滚串行。

    plan 为空 → 返回 []（调用方不应进入本函数，此处防御）。
    校验失败 → 抛 PlanValidationError（调用方按硬失败处理，不走本函数的结果）。
    """
    cfg = contract or load_contract()
    if not plan:
        return []
    steps = _validate(plan, cfg)
    _prefill_params(steps, prefill_map, cfg)
    _enrich_domain_params(steps, card or {}, cfg)

    import plan_endpoints
    results: Dict[int, dict] = {}

    def _call(idx: int) -> None:
        step = steps[idx]
        step_card = dict(card or {})
        step_card.setdefault("query_origin", (card or {}).get("query_origin", ""))
        # 2026-11-20 用户裁定：分流只看装机状态——装了就调本地技能脚本（不出域），
        # 没装才走云端端点。与技能来源 origin（谁建议的）无关；origin/authoritative
        # 只管「调哪些技能」，不管「怎么调」。
        if _runs_local(step.get("skill")):
            try:
                import local_step_runner
                results[idx] = local_step_runner.run_local_step(
                    step["skill"], step.get("params") or {}, step_card,
                    step.get("expect", ""))
            except Exception as e:  # noqa: BLE001 硬失败按 error 步，不伪造结果
                results[idx] = {"skill": step["skill"], "status": "error",
                                "expect": step.get("expect", ""), "summary": {},
                                "error": "LOCAL_DISPATCH_FAIL:%s" % type(e).__name__}
        else:
            results[idx] = plan_endpoints.call_step(step, step_card, cfg)

    if _parallel_enabled() and len(steps) > 1:
        from concurrent.futures import ThreadPoolExecutor
        levels = _levels(steps)
        # 同层并发、层间串行：逐层收集索引 → 一批提交 → 等该批全部完成
        buckets: Dict[int, List[int]] = {}
        for idx, lvl in enumerate(levels):
            buckets.setdefault(lvl, []).append(idx)
        for lvl in sorted(buckets):
            batch = buckets[lvl]
            if len(batch) == 1:
                _call(batch[0])
            else:
                with ThreadPoolExecutor(max_workers=len(batch)) as pool:
                    futures = [pool.submit(_call, idx) for idx in batch]
                    for f in futures:
                        f.result()  # call_step 内部已吞异常；此处抛则交调用方硬失败
    else:
        for idx in _topo_order(steps):
            _call(idx)

    # 按原始 plan 顺序输出（不按执行序），保证与串行版一致，便于对照步骤编号
    # 2026-11-20：给每条结果透传 origin（local/cloud），供装配层按权威源仲裁
    for _i, _step in enumerate(steps):
        if _i in results and isinstance(results[_i], dict):
            results[_i].setdefault("origin", str(_step.get("origin") or "cloud"))
    return [results[i] for i in range(len(steps))]


# ── 离线自测 ────────────────────────────────────────────────────────────────

def self_test() -> int:
    import os  # noqa: F811 - 与函数内后续 import os 同对象，避免局部绑定陷阱
    cfg = load_contract()
    ok = True

    def chk(label: str, cond: bool) -> None:
        nonlocal ok
        print("  [%s] %s" % ("PASS" if cond else "FAIL", label))
        ok = ok and cond

    print("plan_runner 离线自测（不触网）")
    print("-" * 62)
    # 2026-11-20 装机分流：参数补齐用例针对云端端点（验证英文化），
    # 强制走云端以隔离本机装机状态；末尾单独验证装机判据本身。
    _old_force_cloud = os.environ.get("CT_ADVISOR_FORCE_CLOUD")
    os.environ["CT_ADVISOR_FORCE_CLOUD"] = "1"
    good = [
        {"skill": "ct-samplesize", "params": {"alpha": 0.05}, "depends_on": [],
         "expect": "samplesize_number", "prefill": True},
        {"skill": "ct-registry", "params": {"max": 20}, "depends_on": [],
         "expect": "registry_landscape", "prefill": True},
    ]
    chk("合法 plan 校验通过", len(_validate(good, cfg)) == 2)

    # 参数 fail-closed
    dirty = [dict(good[0], params={"alpha": 0.05, "__junk": 1})]
    chk("未知参数被过滤", "__junk" not in _validate(dirty, cfg)[0]["params"])

    # 白名单拒绝（含 B 档）
    for bad_skill in ("ct-sdtm", "ct-adam", "ct-protocol", "unknown"):
        try:
            _validate([dict(good[0], skill=bad_skill)], cfg)
            chk("拒绝 %s" % bad_skill, False)
        except PlanValidationError:
            chk("拒绝 %s" % bad_skill, True)

    # 步数上限
    too_many = [dict(good[0], skill="ct-samplesize") for _ in range(cfg["plan"]["max_steps"] + 1)]
    try:
        _validate(too_many, cfg)
        chk("拒绝超过 5 步", False)
    except PlanValidationError:
        chk("拒绝超过 5 步", True)

    # 依赖环
    cyclic = [
        dict(good[0], depends_on=[1]),
        dict(good[1], depends_on=[0]),
    ]
    try:
        _validate(cyclic, cfg)
        chk("拒绝依赖环", False)
    except PlanValidationError:
        chk("拒绝依赖环", True)

    # 合法依赖的拓扑序
    dag = [
        dict(good[0], depends_on=[]),
        dict(good[1], depends_on=[0]),
    ]
    norm = _validate(dag, cfg)
    order = _topo_order(norm)
    chk("拓扑序依赖在前", order.index(0) < order.index(1))

    # 非法依赖索引
    for bad_dep in ([2], [-1], [1]):
        try:
            _validate([dict(good[0], depends_on=bad_dep)], cfg)
            chk("拒绝非法依赖 %s" % bad_dep, False)
        except PlanValidationError:
            chk("拒绝非法依赖 %s" % bad_dep, True)

    # expect 枚举
    try:
        _validate([dict(good[0], expect="bogus")], cfg)
        chk("拒绝非法 expect", False)
    except PlanValidationError:
        chk("拒绝非法 expect", True)

    # prefill
    pf = _validate(good, cfg)
    _prefill_params(pf, {"ct-registry": {"cond": "肺癌"}}, cfg)
    chk("prefill 补齐 cond", pf[1]["params"].get("cond") == "肺癌")

    # 领域参数补齐（2026-11-19 用户裁定：中国药双源 + 中文药名映射英文）
    reg = _validate([dict(good[1], params={"cond": "肝癌", "intr": "信迪利单抗"})], cfg)
    _enrich_domain_params(reg, {"original_question": "信迪利单抗治疗肝癌的在研临床试验"}, cfg)
    chk("registry 中文问题补 with_cde", reg[0]["params"].get("with_cde") is True)
    chk("registry cde_keyword=药名中文(国内源检索主词)",
        reg[0]["params"].get("cde_keyword") == "信迪利单抗")
    saf = _validate([dict(good[0], skill="ct-safety", expect="safety_signal",
                          params={})], cfg)
    _enrich_domain_params(saf, {"original_question": "信迪利单抗肝损伤不良反应安全信号"}, cfg)
    chk("safety 中文药名映射英文 drug", saf[0]["params"].get("drug") == "sintilimab")
    chk("safety 中文不良事件映射英文 event", saf[0]["params"].get("event") == "hepatotoxicity")
    # 肝肾损伤：brief 单事件边界，取肝为主；仍必须有 event 才能出 2×2
    saf2 = _validate([dict(good[0], skill="ct-safety", expect="safety_signal",
                           params={})], cfg)
    _enrich_domain_params(saf2, {"original_question":
                          "检测信迪利单抗肝肾损伤不良反应的安全信号"}, cfg)
    chk("safety 肝肾损伤映射 event(取肝)", saf2[0]["params"].get("event") == "hepatotoxicity")
    saf_ev = _validate([dict(good[0], skill="ct-safety", expect="safety_signal",
                             params={"event": "nephrotoxicity"})], cfg)
    _enrich_domain_params(saf_ev, {"original_question": "信迪利单抗肝损伤"}, cfg)
    chk("safety 不覆盖已有 event", saf_ev[0]["params"].get("event") == "nephrotoxicity")
    # term_map 精确词优先（急性肾损伤 → AKI，而非肾损伤组合词）
    saf3 = _validate([dict(good[0], skill="ct-safety", expect="safety_signal",
                           params={})], cfg)
    _enrich_domain_params(saf3, {"original_question": "帕博利珠单抗急性肾损伤安全信号"}, cfg)
    chk("safety 精确词优先(AKI)", "nephrotoxicity" not in str(saf3[0]["params"].get("event"))
        and "acute kidney injury" in str(saf3[0]["params"].get("event")))
    # 肾损伤组合词也必须映射为 FAERS 有效 PT（AKI），不能是 404 的 nephrotoxicity
    saf4 = _validate([dict(good[0], skill="ct-safety", expect="safety_signal",
                           params={})], cfg)
    _enrich_domain_params(saf4, {"original_question": "信迪利单抗肾损伤不良反应"}, cfg)
    chk("safety 肾损伤映射 AKI(避开 404)",
        saf4[0]["params"].get("event") == "acute kidney injury")
    # 检索词翻译（B2）：中文 topic/cond → 英文（brief 端点只认英文）
    import os
    _old_online = os.environ.get("CT_TRANSLATE_ONLINE")
    os.environ["CT_TRANSLATE_ONLINE"] = "0"   # 自测离线：只用本地词典
    try:
        lit = _validate([dict(good[0], skill="ct-literature", expect="literature_evidence",
                              params={"topic": "信迪利单抗治疗肝癌的系统综述"})], cfg)
        _enrich_domain_params(lit, {"original_question":
                              "信迪利单抗治疗肝癌的系统综述"}, cfg)
        topic_en = str(lit[0]["params"].get("topic") or "")
        chk("literature 中文 topic 翻英文", "sintilimab" in topic_en.lower()
            and not any("\u4e00" <= c <= "\u9fff" for c in topic_en))
        chk("topic 翻译含同义词扩展", "liver cancer" in topic_en.lower()
            or "hepatocellular" in topic_en.lower())
        # 正确语义：cond=疾病(适应症)、intr=药物；国外源翻干净英文，国内源 cde_keyword 用药名中文
        reg_tr = _validate([dict(good[1], params={"cond": "非小细胞肺癌", "intr": "帕博利珠单抗"})], cfg)
        _enrich_domain_params(reg_tr, {"original_question": "帕博利珠单抗治疗非小细胞肺癌"}, cfg)
        _p = reg_tr[0]["params"]
        chk("registry cond(适应症)翻干净英文",
            "non-small cell lung cancer" in str(_p.get("cond")).lower()
            and " OR " not in str(_p.get("cond")).upper())
        chk("registry intr(药物)翻干净英文",
            "pembrolizumab" in str(_p.get("intr")).lower()
            and " OR " not in str(_p.get("intr")).upper())
        chk("registry cde_keyword=药名中文(非疾病)",
            _p.get("cde_keyword") == "帕博利珠单抗")
        chk("registry 补 with_cde", _p.get("with_cde") is True)
    finally:
        if _old_online is None:
            os.environ.pop("CT_TRANSLATE_ONLINE", None)
        else:
            os.environ["CT_TRANSLATE_ONLINE"] = _old_online
    # 英文问题不应被误补 CDE
    reg_en = _validate([dict(good[1], params={"cond": "NSCLC"})], cfg)
    _enrich_domain_params(reg_en, {"original_question": "pembrolizumab for NSCLC"}, cfg)
    chk("英文问题不补 CDE", "with_cde" not in reg_en[0]["params"])

    # 并行调度（2026-11-20）：依赖分层 + 结果按原序归并
    dag_lv = [
        dict(good[0], depends_on=[]),                    # level 0
        dict(good[1], depends_on=[]),                    # level 0（与上同层可并发）
        {"skill": "ct-samplesize", "params": {"alpha": 0.05},
         "depends_on": [0, 1], "expect": "samplesize_number", "prefill": False},  # level 1
    ]
    _norm = _validate(dag_lv, cfg)
    lvl = _levels(_norm)
    chk("依赖分层 level=[0,0,1]", lvl == [0, 0, 1])
    # mock call_step 记录调用，验证并行输出仍按原 plan 索引归并
    import time as _time
    from unittest import mock as _mock
    import plan_endpoints as _pe
    seen_order = []

    def _fake_step(step, step_card, cfg2=None):
        seen_order.append(step["skill"])
        _time.sleep(0.02)
        return {"skill": step["skill"], "status": "ok", "expect": step.get("expect", ""),
                "summary": {"n": len(seen_order)}, "error": ""}

    old_parallel = os.environ.pop("CT_ADVISOR_PLAN_PARALLEL", None)
    try:
        with _mock.patch.object(_pe, "call_step", side_effect=_fake_step):
            t0 = _time.time()
            out = run_plan(dag_lv, card={"original_question": "q", "query_origin": "sha256:" + "a" * 64})
            elapsed = _time.time() - t0
        chk("并行结果按原 plan 顺序归并",
            [r["skill"] for r in out] == ["ct-samplesize", "ct-registry", "ct-samplesize"])
        chk("同层并发省时（3 步 < 串行 60ms）", elapsed < 0.055)
        # 回滚串行
        os.environ["CT_ADVISOR_PLAN_PARALLEL"] = "0"
        chk("CT_ADVISOR_PLAN_PARALLEL=0 关闭并发", _parallel_enabled() is False)
        with _mock.patch.object(_pe, "call_step", side_effect=_fake_step):
            out_serial = run_plan(dag_lv, card={"original_question": "q"})
        chk("串行版输出顺序一致", [r["skill"] for r in out_serial]
            == [r["skill"] for r in out])
    finally:
        if old_parallel is None:
            os.environ.pop("CT_ADVISOR_PLAN_PARALLEL", None)
        else:
            os.environ["CT_ADVISOR_PLAN_PARALLEL"] = old_parallel

    # 2026-11-20 装机分流判据专测：装了→本地，没装→云端，与 origin 无关
    from unittest import mock as _mock2
    import handle_need_tool as _hnt
    # 解除强制云端，用 mock 模拟装机状态
    os.environ.pop("CT_ADVISOR_FORCE_CLOUD", None)
    try:
        with _mock2.patch.object(_hnt, "_client_callable",
                                 side_effect=lambda s: s == "ct-registry"):
            chk("装机分流：装了→本地", _runs_local("ct-registry") is True)
            chk("装机分流：没装→云端", _runs_local("ct-safety") is False)
            # 同一技能，无论 step 标 origin=local 还是 cloud，判据都只看装机
            _step_l = dict(good[1], origin="local")
            _step_c = dict(good[1], origin="cloud")
            chk("origin=local 但装了→仍本地",
                _runs_local(_step_l["skill"]) is True)
            chk("origin=cloud 但没装→仍云端",
                _runs_local("ct-literature") is False)
    finally:
        if _old_force_cloud is None:
            os.environ.pop("CT_ADVISOR_FORCE_CLOUD", None)
        else:
            os.environ["CT_ADVISOR_FORCE_CLOUD"] = _old_force_cloud
    print("-" * 62)
    print("结论：%s" % ("✅ 全部通过" if ok else "❌ 存在 FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Plan 校验器 + 拓扑执行器")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    print("用法：python adapters/plan_runner.py --self-test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
