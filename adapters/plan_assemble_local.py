#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plan_assemble_local.py — Plan 结果的本地顺序陈列（2026-11-20，D4'）。

定位
====
替代原「二次 Coze 综合」：plan_runner 执行完拿到的 plan_results，其 summary 已是
各技能速览端点算好的成品字段（命中数 / 分期分布 / 2×2+PRR / top works / n）。
本模块**零 LLM、零出域、零网络**，纯确定性把这些成品按顺序陈列成最终答案：

  ① 首趟草稿（draft_answer）原样保留
  ② 一句跨技能归纳（纯代码拼装，不调用 LLM）
  ③ 按 plan 原始顺序逐项陈列各技能结果（ok 渲染字段 / error 据实标注）
  ④ 尾部 F33 导流页脚（disclaimer + @skill 建议，boundary.audit 强制）

统一入口 assemble() 同时服务两条调用路径（orchestrate 自动兜底 + confirm_menu
的 defer→resume 工作台主路径），并用契约开关 + env 支持一键回滚到云端二次综合：

  * config/plan_contract.json::assemble.mode = local_render（默认）/ cloud_second_call
  * env CT_ADVISOR_ASSEMBLE = local|local_render（强制本地）/ cloud|cloud_second_call（强制云端回滚）

失败语义
========
本地渲染几乎不会失败（无网络 / 无 LLM）。仍保留硬失败口径：若构造出空答案，
返回空 final_answer，由调用方 confirm_menu / orchestrate 按既有错误通道处理，
绝不返回未经确认的半成品。samplesize / error 步无字段时不伪造内容，据实标注。

用法
====
    python adapters/plan_assemble_local.py --self-test   # 离线自测，不触网
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
for _p in (str(SCRIPT_DIR), str(SKILL_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

CONTRACT_PATH = SKILL_ROOT / "config" / "plan_contract.json"
BRIEF_CONTRACT_PATH = SKILL_ROOT / "config" / "brief_contract.json"

# 技能展示名（归纳句 / 小标题用；与 _TOOL_DESC 同口径，简写）
_SKILL_CN = {
    "ct-registry": "注册库检索",
    "ct-safety": "安全性信号",
    "ct-literature": "文献检索",
    "ct-samplesize": "样本量估算",
}


def load_contract() -> dict:
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_brief_contract() -> dict:
    with open(BRIEF_CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def use_local(cfg: Optional[dict] = None) -> bool:
    """是否走本地陈列。默认读契约 assemble.mode=local_render；env 可强制回滚。"""
    spec = cfg or load_contract()
    mode = str((spec.get("assemble") or {}).get("mode", "local_render")).strip().lower()
    env = os.environ.get("CT_ADVISOR_ASSEMBLE", "").strip().lower()
    if env in ("cloud", "cloud_second_call", "cloud_2nd"):
        return False
    if env in ("local", "local_render", "local_ordered"):
        return True
    return mode != "cloud_second_call"


# ── 一句跨技能归纳（纯代码，零 LLM）──────────────────────────────────────────

def _metric_phrase(r: dict) -> str:
    """从单个 ok 步骤的 summary 抽一个关键指标短语（无字段则据实说"已取数"）。"""
    skill = str(r.get("skill") or "")
    s = r.get("summary") or {}
    if skill == "ct-registry":
        hits = s.get("total_hits", "?")
        return "注册库命中%s条" % hits
    if skill == "ct-safety":
        m = s.get("measures") or {}
        prr = m.get("prr")
        if prr is not None:
            return "安全性信号 PRR=%s" % prr
        c = s.get("counts_2x2") or {}
        if c:
            return "安全性信号已得 2×2 计数"
        return "安全性信号已取数"
    if skill == "ct-literature":
        uniq = s.get("unique_works", s.get("total_hits", "?"))
        return "文献去重后%s篇" % uniq
    if skill == "ct-samplesize":
        n = s.get("n", "?")
        return "样本量 n=%s" % n
    return "%s已取数" % _SKILL_CN.get(skill, skill)


def cross_skill_digest(plan_results: List[dict]) -> str:
    """一句跨技能归纳：覆盖全部步骤（含 error），句号结尾的单句。"""
    results = [r for r in (plan_results or []) if isinstance(r, dict)]
    if not results:
        return "本轮无取数结果。"
    parts: List[str] = []
    for r in results:
        skill = str(r.get("skill") or "")
        name = _SKILL_CN.get(skill, skill)
        if r.get("status") != "ok":
            reason = str(r.get("error") or "无结果")
            parts.append("%s未成功（%s）" % (name, reason))
        else:
            parts.append(_metric_phrase(r))
    return "本轮共执行%d项取数：%s。以下按执行顺序陈列各项结果。" % (
        len(results), "、".join(parts))


# ── 单个技能结果块渲染 ──────────────────────────────────────────────────────

def _pairs(block: Any, limit: int = 8) -> str:
    if not isinstance(block, dict) or not block:
        return ""
    return "；".join("%s %s" % (k, v) for k, v in list(block.items())[:limit])


def _list_truncation_hint(shown: int, total, noun: str, skill: str) -> str:
    """列表被截断时提示「仅列前 N 条 / 完整清单用技能单独取」（2026-11-20 用户要求）。

    仅当命中总数可解析为整数且 > 实际展示条数时才提示——全列出来时不说「仅列部分」，
    避免误导。total 可能是 int / str / "?"，解析失败一律不提示（据实、不猜）。
    """
    try:
        t = int(total)
    except (TypeError, ValueError):
        return ""
    if t <= shown:
        return ""
    return ("- ℹ️ 上方仅展示前 %d 条%s（共命中 %d 条）；"
            "完整清单、检索策略与可核验产物请单独调用 `%s` 技能获取。"
            % (shown, noun, t, skill))


def _render_summary(skill: str, s: dict) -> List[str]:
    """把 summary 渲染成字段行（与 cloud_brief.render_brief_text 字段口径一致）。"""
    lines: List[str] = []
    if skill == "ct-registry":
        lines.append("- 检索词：`%s`｜命中 %s 条｜数据源：%s" % (
            s.get("query", ""), s.get("total_hits", 0),
            ", ".join(s.get("sources_used") or []) or "无"))
        for label, key in (("分期分布", "phase_counts"), ("状态分布", "status_counts"),
                           ("主要申办方", "top_sponsors")):
            val = _pairs(s.get(key))
            if val:
                lines.append("- %s：%s" % (label, val))
        trials = s.get("sample_trials") or []
        shown = 0
        for t in trials[:5]:
            if not isinstance(t, dict):
                continue
            if not any(str(v or "").strip() for v in t.values()):
                continue  # 空壳不渲染（_repair_sample_trials 上游已兜底）
            shown += 1
            lines.append("  - %s ｜ %s ｜ %s" % (
                t.get("id") or "-", str(t.get("title") or "")[:90], t.get("status") or "-"))
        _hint = _list_truncation_hint(shown, s.get("total_hits"), "试验", "ct-registry")
        if _hint:
            lines.append(_hint)
    elif skill == "ct-safety":
        lines.append("- 药物：`%s`｜事件：`%s`" % (
            s.get("drug", ""), s.get("event") or "未指定"))
        c = s.get("counts_2x2") or {}
        if c:
            lines.append("- 2×2 计数：a=%s b=%s c=%s d=%s" % (
                c.get("a", "-"), c.get("b", "-"), c.get("c", "-"), c.get("d", "-")))
        m = s.get("measures") or {}
        if m.get("prr") is not None:
            lines.append("- PRR=%s（95%%CI %s）｜ROR=%s（95%%CI %s）" % (
                m.get("prr"), m.get("prr_ci95"), m.get("ror"), m.get("ror_ci95")))
        if m.get("note"):
            lines.append("- %s" % m["note"])
    elif skill == "ct-literature":
        lines.append("- 主题：`%s`｜命中 %s 条｜去重后 %s 篇｜数据源：%s" % (
            s.get("topic", ""), s.get("total_hits", 0), s.get("unique_works", 0),
            ", ".join(s.get("sources_used") or []) or "无"))
        works = s.get("top_works") or []
        shown = 0
        for w in works[:5]:
            if not isinstance(w, dict):
                continue
            shown += 1
            lines.append("  - %s（%s，被引 %s）%s" % (
                str(w.get("title") or "")[:100], w.get("year") or "-",
                w.get("cited_by_count", 0),
                " DOI:" + w["doi"] if w.get("doi") else ""))
        _hint = _list_truncation_hint(shown, s.get("total_hits"), "文献", "ct-literature")
        if _hint:
            lines.append(_hint)
    elif skill == "ct-samplesize":
        lines.append("- 检验：`%s`｜模式：%s｜alpha=%s" % (
            s.get("test", ""), s.get("mode") or "-", s.get("alpha", "-")))
        bits = []
        for k, label in (("n", "n"), ("power", "power"), ("effect", "effect")):
            if s.get(k) is not None:
                bits.append("%s=%s" % (label, s[k]))
        if bits:
            lines.append("- " + "｜".join(bits))
        for key in ("summary", "conclusion", "note"):
            if s.get(key):
                lines.append("- %s" % s[key])
    else:
        lines.append("- 该项取数成功，技能 `%s` 无可展示的结构化字段（不伪造内容）。" % skill)

    if s.get("partial_sources"):
        lines.append("- ⚠️ 部分数据源未完成：%s（已如实标注，未补齐）" %
                     ", ".join(s["partial_sources"]))
    if s.get("note") and skill not in ("ct-safety", "ct-samplesize"):
        lines.append("- %s" % s["note"])
    if not lines:
        lines.append("- 该项取数成功，但未返回可展示字段（不伪造内容）。")
    return lines


def render_block(r: dict) -> str:
    """渲染单个 plan 步骤为文本块（含 error 据实标注）。"""
    skill = str(r.get("skill") or "")
    if r.get("status") != "ok":
        return ("- 状态：取数失败\n- 原因码：`%s`\n"
                "- 说明：该项未取得数据，未做补零或推测。" %
                (str(r.get("error") or "UNKNOWN")))
    s = r.get("summary") or {}
    return "\n".join(_render_summary(skill, s))


# ── 尾部导流页脚（F33 / boundary.audit 强制）──────────────────────────────────

def _footer(plan_results: List[dict]) -> List[str]:
    bc = _load_brief_contract()
    lines = ["---", "", str(bc.get("disclaimer_text", "")), ""]
    suggest = bc.get("suggest_text") or {}
    seen = set()
    for r in (plan_results or []):
        sk = str(r.get("skill") or "")
        if r.get("status") == "ok" and sk in suggest and sk not in seen:
            lines.append(str(suggest[sk]))
            seen.add(sk)
    if not seen:
        lines.append("需要完整分析（含可复算交付物与审计级报告），请调用对应技能本体。")
    return lines


# ── 主装配 ───────────────────────────────────────────────────────────────────

def reconcile_results(plan_results: List[dict], authoritative: str) -> List[dict]:
    """两套标准的最终结果仲裁（2026-11-20 用户裁定：Coze 为准）。

    - authoritative=cloud：Coze 已给明确判断，最终结果一律以 Coze 端返回为准。
      仅保留 origin=cloud（远端端点）的结果；本地预判来源(local)的结果丢弃，
      避免两套标准不一致时把本地结果混进 Coze 输出。
    - authoritative=local_fallback / 其它：Coze 无判断，本地兜底结果全部保留。
    """
    rows = [r for r in (plan_results or []) if isinstance(r, dict)]
    if str(authoritative or "") == "cloud":
        return [r for r in rows if str(r.get("origin") or "cloud") != "local"]
    return rows


def assemble_local(original_question: str, first_draft: str,
                   plan_results: List[dict], authoritative: str = "") -> Any:
    """本地确定性装配，返回 RefineResult(final_answer=...)。

    authoritative=cloud 时先按 reconcile_results 仲裁：只陈列 Coze 端结果。
    """
    from adapters import RefineResult

    plan_results = reconcile_results(plan_results, authoritative)
    out: List[str] = []
    draft = str(first_draft or "").strip()
    # 2026-11-20 用户裁定：multi 最终输出必须保留首趟原始输出（draft / 初步说明）。
    # 旧逻辑「有成功取数且 draft 含拒答措辞 → 整段剔除」会误删初步说明：三合一首趟
    # draft 形如「我暂无法直接提供…」，命中剔除后最终答案只剩取数结果，丢失用户
    # 一开始看到的原始输出（web 端实测）。与 single 的 draft+result 缝合口径、以及
    # 本模块设计「①首趟草稿原样保留」都不一致。
    # 改为原样保留 draft，并加「初步说明」小标题分层：原始内容不丢，且与后面的真实
    # 取数结果明确区分——不再产生「先说无法提供、后又列真实结果」的误读。
    if draft:
        out += ["## 初步说明（首趟生成，仅供参考）", "", draft, ""]
    out += [cross_skill_digest(plan_results), ""]

    results = [r for r in (plan_results or []) if isinstance(r, dict)]
    if results:
        out += ["## 取数结果（按执行顺序陈列）", ""]
        for i, r in enumerate(results, 1):
            skill = str(r.get("skill") or "")
            name = _SKILL_CN.get(skill, skill)
            mark = "成功" if r.get("status") == "ok" else "取数失败"
            out += ["### %d. %s · %s（%s）" % (i, name, skill, mark), ""]
            out += [render_block(r), ""]
    out += _footer(results)
    text = "\n".join(out).strip() + "\n"
    return RefineResult(final_answer=text, need_tool=None)


def assemble(req, config_path: str, plan_results: List[dict],
             authoritative: str = "") -> Any:
    """统一入口：默认本地陈列；CT_ADVISOR_ASSEMBLE=cloud 或契约 mode=cloud_second_call
    时回滚到原二次 Coze 综合。两条调用路径（orchestrate / confirm_menu）共用本函数。

    authoritative=cloud（Coze 有判断）时，结果层只陈列 Coze 端返回（见 reconcile_results）。
    """
    if not use_local():
        from adapters import plan_assemble_cloud
        return plan_assemble_cloud.assemble(req, config_path, plan_results)
    return assemble_local(
        getattr(req, "original_question", ""),
        getattr(req, "draft_answer", ""),
        plan_results,
        authoritative=authoritative,
    )


# ── 离线自测 ────────────────────────────────────────────────────────────────

def self_test() -> int:
    ok = True

    def chk(label: str, cond: bool) -> None:
        nonlocal ok
        print("  [%s] %s" % ("PASS" if cond else "FAIL", label))
        ok = ok and cond

    print("plan_assemble_local 离线自测（不触网）")
    print("-" * 62)
    results = [
        {"skill": "ct-registry", "status": "ok", "expect": "registry_landscape",
         "summary": {"query": "NSCLC", "total_hits": 12,
                     "phase_counts": {"II": 5}, "sources_used": ["who", "cde"],
                     "sample_trials": [{"id": "CTR20260001", "title": "A Study", "status": "Recruiting"}]},
         "error": ""},
        {"skill": "ct-safety", "status": "ok", "expect": "safety_signal",
         "summary": {"drug": "pembrolizumab", "event": "hepatotoxicity",
                     "counts_2x2": {"a": 30, "b": 10, "c": 5, "d": 100},
                     "measures": {"prr": 3.2, "prr_ci95": "1.8-5.6", "ror": 3.4, "ror_ci95": "1.9-6.0"}},
         "error": ""},
        {"skill": "ct-literature", "status": "error", "expect": "literature_evidence",
         "summary": {}, "error": "BRIEF_FAILED"},
        {"skill": "ct-samplesize", "status": "ok", "expect": "samplesize_number",
         "summary": {"test": "proportion_two", "mode": "power", "alpha": 0.05,
                     "n": 120, "power": 0.8, "conclusion": "每组 120 例"},
         "error": ""},
    ]
    res = assemble_local("帕博利珠单抗治疗 NSCLC", "【初步答案】需外部数据。", results)
    text = res.final_answer
    chk("返回 RefineResult 且 need_tool=None", res.need_tool is None)
    chk("首趟草稿原样保留", "【初步答案】需外部数据。" in text)
    chk("跨技能归纳一句存在", "本轮共执行4项取数" in text and "PRR=3.2" in text)
    chk("error 步据实标注", "BRIEF_FAILED" in text and "取数失败" in text)
    chk("按 plan 顺序陈列（1→4）",
        text.index("1. 注册库检索") < text.index("2. 安全性信号")
        < text.index("3. 文献检索") < text.index("4. 样本量估算"))
    chk("registry 明细渲染", "CTR20260001" in text)
    chk("列表截断提示（20>1，registry）",
        "仅展示前 1 条试验（共命中 12 条）" in text and "单独调用 `ct-registry` 技能" in text)
    chk("未截断时不误报（safety 无列表提示）", "共命中" not in text.split("### 2. 安全性信号")[1].split("### 3.")[0])
    chk("safety 2x2 + PRR 渲染", "a=30 b=10 c=5 d=100" in text and "PRR=3.2" in text)
    chk("samplesize n/power 渲染", "n=120" in text and "power=0.8" in text)
    chk("F33 页脚：disclaimer", "本结果由公开数据一次性聚合" in text)
    chk("F33 页脚：@skill 导流", "@skill:ct-registry" in text and "@skill:ct-safety" in text)
    chk("error 技能不进导流页脚", "@skill:ct-literature" not in text.split("---")[-1])

    # 2026-11-20 回归：拒答措辞 draft 也必须保留（用户裁定 multi 输出含初步说明）。
    # 旧「命中拒答措辞即整段剔除」曾误删三合一首趟原始输出。
    _punt_draft = "**方法学解释**：我暂无法直接提供实时清单，可通过官方平台自行检索。"
    _punt_text = assemble_local("q", _punt_draft, results).final_answer
    chk("拒答措辞 draft 仍保留", "方法学解释" in _punt_text)
    chk("draft 带初步说明分层标题", "初步说明（首趟生成，仅供参考）" in _punt_text)

    # 两套标准仲裁（2026-11-20 Coze 为准）：cloud 权威剔除 local 结果
    mixed = [
        {"skill": "ct-registry", "status": "ok", "origin": "cloud",
         "summary": {"query": "X", "total_hits": 9}, "error": ""},
        {"skill": "ct-safety", "status": "ok", "origin": "local",
         "summary": {"drug": "Y", "measures": {"prr": 9.9}}, "error": ""},
    ]
    t_cloud = assemble_local("q", "【Coze 草稿】", mixed, authoritative="cloud").final_answer
    chk("cloud 权威保留 Coze 结果", "命中 9 条" in t_cloud)
    chk("cloud 权威剔除 local 结果", "PRR=9.9" not in t_cloud)
    t_local = assemble_local("q", "", mixed, authoritative="local_fallback").final_answer
    chk("local 兜底保留全部结果", "命中 9 条" in t_local and "PRR=9.9" in t_local)

    # 开关行为
    cfg = load_contract()
    old = os.environ.pop("CT_ADVISOR_ASSEMBLE", None)
    try:
        chk("契约默认 local_render → use_local=True", use_local(cfg) is True)
        os.environ["CT_ADVISOR_ASSEMBLE"] = "cloud"
        chk("env=cloud 强制回滚 → use_local=False", use_local(cfg) is False)
        os.environ["CT_ADVISOR_ASSEMBLE"] = "local"
        chk("env=local 强制本地 → use_local=True", use_local(cfg) is True)
    finally:
        if old is None:
            os.environ.pop("CT_ADVISOR_ASSEMBLE", None)
        else:
            os.environ["CT_ADVISOR_ASSEMBLE"] = old

    # 空摘要 / 全 error 不伪造
    all_err = [{"skill": "ct-registry", "status": "error", "summary": {}, "error": "X"}]
    t2 = assemble_local("q", "", all_err).final_answer
    chk("无草稿时归纳句为开篇（无草稿段）", t2.startswith("本轮共执行"))
    chk("全 error 时归纳句据实", "未成功（X）" in t2)
    chk("全 error 时无 @skill 误导流", "@skill:" not in t2.split("---")[-1])
    print("-" * 62)
    print("结论：%s" % ("✅ 全部通过" if ok else "❌ 存在 FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Plan 本地顺序陈列器")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    print("用法：python adapters/plan_assemble_local.py --self-test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
