#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plan_endpoints.py — Plan 步骤 → A 档技能后端 Coze 端点的本地调用器（2026-11-18）。

定位
====
plan_runner 拓扑调度的执行末端。只做「构造信封 / 发请求 / 提取结构化摘要」，
不含任何检索或统计实现，不持有凭据（凭据来自本地 coze_token_embedded，
env 可覆盖），Coze 云端包内零凭据不变。

四条端点路由（config/plan_contract.json::endpoint_routing）：
  · ct-registry / ct-safety / ct-literature → 复用 cloud_brief.run_brief
    （ct-search.coze.site，brief 速览口径 D2，8/6/6 参数白名单，三条护栏）
  · ct-samplesize → ct-samplesize.coze.site/run（最小信封，Bearer 本地内嵌凭据）

设计约束
========
* 每个调用返回统一结构：{skill, status, expect, summary, error}
  - status=ok：summary 为结构化摘要 dict（只含公开字段，供二次 Coze 出域）
  - status=error：error 为原因码，summary 为空；绝不伪造 0 结果
* 单步失败由 plan_runner 标记，不中断其余步骤；本模块吞掉网络异常返回 error。
* async-first：响应 status=accepted + run_id 时轮询回收（网关 60s 硬超时，
  /stream_run 只作快速路径）。本模块提供同步轮询封装， deadline 分档。
* doc_context 绝不进入本通道（F33 数据出域红线）。

用法
====
    python adapters/plan_endpoints.py --self-test   # 离线自测，不触网
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
for _p in (str(SCRIPT_DIR), str(SKILL_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

CONTRACT_PATH = SKILL_ROOT / "config" / "plan_contract.json"
SAMPLESIZE_ENDPOINT = "https://ct-samplesize.coze.site/run"
SAMPLESIZE_TIMEOUT = 60
POLL_DEADLINE = 300


def load_contract() -> dict:
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 统一结果封装 ────────────────────────────────────────────────────────────

def _ok(skill: str, expect: str, summary: dict) -> dict:
    return {"skill": skill, "status": "ok", "expect": expect,
            "summary": summary, "error": ""}


def _err(skill: str, expect: str, code: str) -> dict:
    return {"skill": skill, "status": "error", "expect": expect,
            "summary": {}, "error": code}


# ── A 档三检索技能：复用 cloud_brief ────────────────────────────────────────

def _empty_trial(t: Any) -> bool:
    """sample_trials 条目是否为空壳（所有字段值均为空）。"""
    if not isinstance(t, dict):
        return True
    return not any(str(v or "").strip() for v in t.values())


def _phase_from_title(title: str) -> str:
    """projects 无独立 phase 字段时，从试验标题兜底抽取分期（Phase II / 期）。"""
    import re
    s = str(title or "")
    m = re.search(r"\b(?:PHASE|期)\s*([1-4IVX]+)\b", s, re.I)
    if m:
        tok = m.group(1).upper()
        roman = {"I": "I", "II": "II", "III": "III", "IV": "IV",
                 "1": "I", "2": "II", "3": "III", "4": "IV"}
        return "Phase " + roman.get(tok, tok)
    return ""


def _repair_sample_trials(payload: dict, summary: dict) -> dict:
    """速览字段映射 bug 兜底（2026-11-19）：registry 走 who_fast_path 单页快速路径时，
    brief.sample_trials 偶发全空壳（{id:"",title:"",...}），但顶层 projects 仍带真实
    登记号/公共标题/招募状态。空壳进二次综合会被渲染成「登记号未提供｜分期:—」的
    无效列表。这里在出域前用 projects 的公开字段重建 sample_trials（最多 10 条，
    与云端 _render_detail_list 一致）；两者都无有效明细则移除该键，避免渲染空壳列表。

    F33：sample_trials 本就是 plan_result_fields 允许出域的字段，只取公开字段，
    不发送 projects 原始大对象（detail_url / 适应症 / 药物名等）。
    """
    trials = summary.get("sample_trials")
    # 上游给了真实明细则原样保留（不覆盖好数据）
    if isinstance(trials, list) and trials and not all(_empty_trial(t) for t in trials):
        return summary
    projects = (payload or {}).get("projects") or []
    repaired = []
    if isinstance(projects, list):
        for p in projects[:10]:
            if not isinstance(p, dict):
                continue
            rid = str(p.get("登记号") or p.get("Main ID") or p.get("project_id") or "").strip()
            title = str(p.get("公共标题") or p.get("试验通俗题目") or "").strip()
            status = str(p.get("招募状态") or p.get("试验状态") or "").strip()
            if not (rid or title):
                continue
            repaired.append({"id": rid, "title": title, "status": status,
                             "phase": _phase_from_title(title), "sponsor": ""})
    if repaired:
        summary["sample_trials"] = repaired
    elif isinstance(trials, list):
        # 上游空壳且 projects 也无有效明细 → 移除，避免渲染无效空壳列表
        summary.pop("sample_trials", None)
    return summary


def _call_brief_step(skill: str, params: dict, card: dict, expect: str) -> dict:
    """ct-registry / safety / literature → cloud_brief（速览口径 D2）。

    复用 cloud_brief.run_brief 的三护栏校验 + 分档超时 + 短 TTL 缓存；
    summary 只取 brief 下的公开字段，绝不携带原始 projects 大对象。
    """
    try:
        import cloud_brief
    except Exception as e:  # noqa: BLE001
        return _err(skill, expect, "BRIEF_MODULE_UNAVAILABLE:%s" % type(e).__name__)
    payload = cloud_brief.run_brief(skill, params or {}, card or {})
    if payload is None:
        return _err(skill, expect, "BRIEF_FAILED")
    brief = payload.get("brief") or {}
    # 只抽结构化摘要字段，剔除 projects 原始命中列表（出域最小化）
    summary_keys = ("query", "total_hits", "unique_works", "sources_used",
                    "phase_counts", "status_counts", "top_sponsors", "sample_trials",
                    "drug", "event", "counts_2x2", "measures", "topic", "top_works",
                    "partial_sources", "note")
    summary = {k: brief[k] for k in summary_keys if k in brief}
    # 速览字段映射 bug 兜底：sample_trials 空壳时用顶层 projects 公开字段补偿；
    # 只对 registry 生效（safety/literature 的明细字段本就从 brief 正确抽取）。
    if skill == "ct-registry":
        summary = _repair_sample_trials(payload, summary)
    summary["brief_kind"] = payload.get("brief_kind", "")
    summary["disclaimer"] = payload.get("disclaimer", "")
    return _ok(skill, expect, summary)


# ── ct-samplesize：本地直连计算端点 ────────────────────────────────────────

def _samplesize_token() -> str:
    env = os.environ.get("CTSS_COZE_TOKEN", "").strip()
    if env:
        return env
    try:
        from adapters import coze_token_embedded
        return coze_token_embedded.get_samplesize_token() or ""
    except Exception:  # noqa: BLE001
        return ""


def _query_origin(card: dict) -> str:
    origin = str((card or {}).get("query_origin") or "").strip()
    if origin:
        return origin
    return os.environ.get("CT_QUERY_ORIGIN", "").strip()


def _build_samplesize_envelope(params: dict, card: dict) -> dict:
    """构造最小合法信封（对齐 coze_client.call 的 payload 核心字段）。

    test 缺省时按 tool_mapping.test_hints 无法推断 → 由本地 route_tool 补齐；
    这里只做白名单过滤与默认值填充，不做领域推断（不引入本地 LLM 决策）。
    """
    test = str((params or {}).get("test") or "").strip()
    allowed = ("test", "alpha", "power", "nobs", "effect", "k_groups", "side",
               "sd", "margin", "p1", "p2")
    clean = {k: v for k, v in (params or {}).items() if k in allowed}
    if test:
        clean["test"] = test
    mode = "power" if clean.get("nobs") and "power" not in clean else "n"
    return {
        "test": test,
        "params": clean,
        "mode": mode,
        "return_r_code": False,
        "locale": (card or {}).get("locale") or "zh-CN",
        "query_origin": _query_origin(card),
        "skill_version": "ct-advisor/plan-v1",
        "entry_point": "skill",
    }


def _dig_samplesize_summary(outer: Any) -> Optional[dict]:
    """从 samplesize 外层响应提取结构化摘要（只取公开计算字段）。

    2026-11-18（CTQA PLAN 层 B1/B2 捕获的 P0 修复）：
      真实 ct-samplesize v5 信封是嵌套结构 ``{status, stats:{n,power,...},
      narrative, figures}``——核心数值在 ``stats`` 子字典与主叙述 ``narrative``，
      旧实现只认顶层扁平键 ``n/power/effect`` → 数值全丢，二次 Coze 拿到空摘要，
      samplesize 步骤等于白跑。现兼容两形态：
        ① 真实嵌套：把 ``stats`` 子字典字段提升到顶层（与旧扁平键同名），
           ``narrative`` 纳入允许键；
        ② 旧扁平：原逻辑不变（向后兼容历史 mock / 缓存）。
      出域最小化不变：figures / repro / svg 等大对象、未知键一律剔除。
    """
    if not isinstance(outer, dict):
        return None
    inner = outer
    if isinstance(outer.get("result"), str):
        try:
            inner = json.loads(outer["result"])
        except ValueError:
            inner = outer
    # 真实 v5：stats 子字典 + narrative 主叙述 → 归一到扁平视图（不修改原对象）
    if isinstance(inner.get("stats"), dict):
        inner = dict(inner)
        stats = inner.pop("stats")
        for k, v in stats.items():
            inner.setdefault(k, v)  # 顶层已有值优先，不覆盖
    if "narrative" in inner and "summary" not in inner:
        inner = dict(inner)
        inner["summary"] = inner.pop("narrative")  # 主叙述作为 summary 出域（不重复带 narrative）
    # 只保留标量 / 小型结构，剔除 figures / repro / svg 等大对象（出域最小化）
    keys = ("status", "n", "power", "test", "mode", "alpha", "effect",
            "summary", "conclusion", "note", "notes", "params", "narrative")
    dict_keys = {"summary", "params"}  # 仅这两个键允许保留 dict 形态
    list_keys = set()                  # 不保留任何原始 list
    out = {}
    for k in keys:
        if k not in inner:
            continue
        v = inner[k]
        if isinstance(v, dict) and k not in dict_keys:
            continue
        if isinstance(v, list) and k not in list_keys:
            continue
        if isinstance(v, str) and len(v) > 4000:
            continue
        if isinstance(v, dict) and len(json.dumps(v, ensure_ascii=False)) > 4000:
            continue
        out[k] = v
    return out or {"status": inner.get("status", "unknown")}


def _poll_samplesize(run_id: str, token: str, deadline: int = POLL_DEADLINE) -> Optional[dict]:
    """轮询 accepted 任务（最小实现：GET /run?run_id=...，兼容常见 Coze 契约）。"""
    url = "https://ct-samplesize.coze.site/run?run_id=" + urllib.parse.quote(run_id)
    t0 = time.time()
    while time.time() - t0 < deadline:
        time.sleep(3)
        try:
            req = urllib.request.Request(
                url, headers={"Authorization": "Bearer %s" % token,
                              "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                obj = json.loads(resp.read().decode("utf-8", errors="replace"))
            if isinstance(obj, dict) and obj.get("status") not in ("accepted", "running", None):
                return obj
        except Exception:  # noqa: BLE001
            continue
    return None


def _call_samplesize_step(params: dict, card: dict, expect: str) -> dict:
    skill = "ct-samplesize"
    token = _samplesize_token()
    if not token:
        return _err(skill, expect, "NO_TOKEN")
    envelope = _build_samplesize_envelope(params, card)
    if "query_origin" not in envelope or not envelope["query_origin"]:
        return _err(skill, expect, "QUERY_ORIGIN_MISSING")
    if not envelope.get("test"):
        return _err(skill, expect, "MISSING_REQUIRED:test")
    body = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        SAMPLESIZE_ENDPOINT, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer %s" % token,
                 "Accept": "application/json, text/event-stream"})
    try:
        with urllib.request.urlopen(req, timeout=SAMPLESIZE_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        return _err(skill, expect, "HTTP_ERROR:%s" % type(e).__name__)
    try:
        outer = json.loads(raw)
    except ValueError:
        return _err(skill, expect, "RESPONSE_UNPARSEABLE")
    if isinstance(outer, dict) and outer.get("status") == "accepted":
        run_id = str(outer.get("run_id") or "")
        if not run_id:
            return _err(skill, expect, "ACCEPTED_NO_RUN_ID")
        outer = _poll_samplesize(run_id, token)
        if outer is None:
            return _err(skill, expect, "POLL_TIMEOUT")
    summary = _dig_samplesize_summary(outer)
    if summary is None:
        return _err(skill, expect, "SUMMARY_EXTRACT_FAILED")
    if str(summary.get("status", "ok")).lower() in ("error", "failed"):
        return _err(skill, expect, "UPSTREAM_ERROR")
    return _ok(skill, expect, summary)


# ── 统一入口 ────────────────────────────────────────────────────────────────

def call_step(step: dict, card: dict, contract: Optional[dict] = None) -> dict:
    """按 step.skill 路由到对应端点调用器，返回统一结果封装。

    异常绝不外抛；任何失败都以 status=error + 原因码返回，交二次 Coze 据实说明。
    """
    cfg = contract or load_contract()
    skill = str((step or {}).get("skill") or "")
    expect = str((step or {}).get("expect") or "")
    params = (step or {}).get("params") or {}
    if skill not in cfg["skills"]:
        return _err(skill or "(empty)", expect, "SKILL_NOT_ALLOWED")
    try:
        if skill == "ct-samplesize":
            return _call_samplesize_step(params, card, expect)
        return _call_brief_step(skill, params, card, expect)
    except Exception as e:  # noqa: BLE001
        return _err(skill, expect, "UNEXPECTED:%s" % type(e).__name__)


# ── 离线自测 ────────────────────────────────────────────────────────────────

def self_test() -> int:
    cfg = load_contract()
    ok = True

    def chk(label: str, cond: bool) -> None:
        nonlocal ok
        print("  [%s] %s" % ("PASS" if cond else "FAIL", label))
        ok = ok and cond

    print("plan_endpoints 离线自测（不触网）")
    print("-" * 62)
    chk("白名单 4 技能", len(cfg["skills"]) == 4 and
        set(cfg["skills"]) == {"ct-registry", "ct-safety", "ct-literature", "ct-samplesize"})
    chk("B 档 sdtm/adam 不在白名单",
        "ct-sdtm" not in cfg["skills"] and "ct-adam" not in cfg["skills"])
    # 非白名单技能被拒
    r = call_step({"skill": "ct-sdtm", "expect": "x"}, {})
    chk("非白名单技能返回 SKILL_NOT_ALLOWED", r["status"] == "error" and
        "NOT_ALLOWED" in r["error"])
    # samplesize 信封构造
    env = _build_samplesize_envelope(
        {"test": "proportion_two", "p1": 0.3, "p2": 0.5, "alpha": 0.05, "__junk": 1},
        {"locale": "zh-CN", "query_origin": "sha256:" + "a" * 64})
    chk("samplesize 信封 test 正确", env["test"] == "proportion_two")
    chk("samplesize 信封过滤未知键", "__junk" not in env["params"])
    chk("samplesize 信封携带 query_origin", env["query_origin"].startswith("sha256:"))
    chk("samplesize 信封无 doc_context", "doc_context" not in env)
    # 摘要提取剔除大字段
    sm = _dig_samplesize_summary({"result": json.dumps(
        {"status": "ok", "n": 120, "power": 0.8,
         "figures": [{"url": "x"}] * 100})})
    chk("摘要提取 n/power", sm.get("n") == 120 and sm.get("power") == 0.8)
    chk("摘要剔除 figures 大字段", "figures" not in sm)
    # sample_trials 空壳补偿（2026-11-19：速览字段映射 bug 兜底）
    _payload = {"projects": [
        {"登记号": "NCT00000001", "公共标题": "A Phase II Study of X",
         "招募状态": "Recruiting", "detail_url": "SECRET_SHOULD_NOT_LEAK"}]}
    _shell = {"sample_trials": [{"id": "", "title": "", "status": "", "phase": "", "sponsor": ""}]}
    _fixed = _repair_sample_trials(_payload, dict(_shell))
    chk("空壳 sample_trials 被补偿为真实登记号",
        _fixed["sample_trials"][0]["id"] == "NCT00000001")
    chk("补偿抽取标题分期", _fixed["sample_trials"][0]["phase"] == "Phase II")
    chk("补偿不泄露 projects 原始字段",
        "detail_url" not in json.dumps(_fixed, ensure_ascii=False))
    chk("上游真实明细不被覆盖",
        _repair_sample_trials(_payload, {"sample_trials": [{"id": "NCT_REAL"}]})[
            "sample_trials"][0]["id"] == "NCT_REAL")
    _both_empty = _repair_sample_trials({"projects": []}, dict(_shell))
    chk("两者皆空则移除 sample_trials 键", "sample_trials" not in _both_empty)
    print("-" * 62)
    print("结论：%s" % ("✅ 全部通过" if ok else "❌ 存在 FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Plan 端点调用器")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    print("用法：python adapters/plan_endpoints.py --self-test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
