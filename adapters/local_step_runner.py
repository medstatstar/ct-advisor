#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_step_runner.py — 本地来源 plan 步骤的执行器（2026-11-20 来源分流）。

定位
====
confirm_menu 阶段1 给 plan step 标 ``origin=local``（本地 route_tool 预判命中，
云端 plan 未覆盖）后，plan_runner 把这类步骤分派到本模块而非 plan_endpoints 的
远端 Coze 端点。本模块：

  ① 用 scripts/handle_need_tool 的现成能力（_build_cmd / 安全边界 / subprocess /
     _extract_json / _read_artifacts）执行本地兄弟技能脚本；
  ② 把本地技能的产物 JSON 归一成 plan_assemble_local 能渲染的 brief 同构 summary
     （query / total_hits / sources_used / phase_counts / measures / top_works …）；
  ③ 全程本地执行、公开源检索，不出域（F33：不发原始产物、附件、涉密字段）。

与远端路径的关系
================
cloud 步骤原样走 plan_endpoints.call_step → cloud_brief（远端速览），本模块只服务
local 步骤。两条路径返回**同一封装结构** {skill,status,expect,summary,error}，
故下游 plan_assemble_local 无需感知差异。

失败语义：任何失败 status=error + 原因码，绝不伪造 0 结果（与远端口径一致）。

用法
====
    python adapters/local_step_runner.py --self-test   # 离线自测，不触网
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
for _p in (str(SCRIPTS_DIR), str(SCRIPT_DIR), str(SKILL_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _ok(skill: str, expect: str, summary: dict) -> dict:
    return {"skill": skill, "status": "ok", "expect": expect,
            "summary": summary, "error": ""}


def _err(skill: str, expect: str, code: str) -> dict:
    return {"skill": skill, "status": "error", "expect": expect,
            "summary": {}, "error": code}


# ── 产物 → brief 同构 summary（纯本地归一，不触网）──────────────────────────

def _top_pairs(obj: Any, n: int = 8) -> dict:
    """把 [{'k':..,'n':..}] 或 Counter/dict 压成 {name: count}（渲染器 _pairs 认 dict）。"""
    if isinstance(obj, dict):
        items = list(obj.items())[:n]
        return {str(k): v for k, v in items}
    if isinstance(obj, list):
        out = {}
        for x in obj[:n]:
            if isinstance(x, dict) and "k" in x:
                out[str(x["k"])] = x.get("n", 0)
            elif isinstance(x, (list, tuple)) and len(x) == 2:
                out[str(x[0])] = x[1]
        return out
    return {}


def normalize_ct_registry(result: Any, artifacts: dict) -> dict:
    """ct-registry --print-summary 产物 → registry brief summary。"""
    body = result if isinstance(result, dict) else {}
    land = body.get("landscape") if isinstance(body.get("landscape"), dict) else body
    # 真实产物 agg.json 注入：{total, phase_dist, status_dist, top_sponsors, dedup_summary}
    agg = body.get("_agg") if isinstance(body.get("_agg"), dict) else {}
    if agg:
        dedup = agg.get("dedup_summary") or {}
        land = {
            "n_trials": (dedup.get("deduped_total") if dedup.get("deduped_total") is not None
                         else agg.get("total")),
            "raw_total": dedup.get("raw_total", agg.get("total")),
            "phase_mix": agg.get("phase_dist") or [],
            "status_mix": agg.get("status_dist") or [],
            "top_sponsors": agg.get("top_sponsors") or [],
            "query": land.get("query", ""),
        }
    n = land.get("n_trials", land.get("raw_total"))
    # 2026-11-20 修复：真实 agg.json 只有 records/phase_dist/... 没有 query/sources/
    # sample_trials，旧归一化只读这三个键 → 陈列显示「检索词：``｜数据源：无」且
    # 没有具体试验（用户要"列出主要在研试验"）。这里从权威产物补齐：
    #   query        ← 入参 cond + intr（检索主词）
    #   sources_used ← records[].source 汇总（去重、保序）
    #   sample_trials← records[] 映射 id/title/status（渲染器认这三个键）
    params = body.get("_params") if isinstance(body.get("_params"), dict) else {}
    query = str(land.get("query", body.get("query", "")) or "")
    if not query and params:
        query = " ".join(str(params.get(k) or "").strip()
                         for k in ("intr", "cond") if str(params.get(k) or "").strip())
    records = agg.get("records") if isinstance(agg.get("records"), list) else []
    if not records and isinstance(body.get("records"), list):
        records = body["records"]
    sources = []
    for r in records:
        if isinstance(r, dict):
            src = str(r.get("source") or r.get("registry") or "").strip()
            if src and src not in sources:
                sources.append(src)
    s = {
        "query": query,
        "total_hits": n if n is not None else 0,
        "sources_used": [str(x) for x in (
            land.get("sources") or body.get("sources_used") or sources)][:8],
        "phase_counts": _top_pairs(land.get("phase_mix") or land.get("phase_counts")),
        "status_counts": _top_pairs(land.get("status_mix") or land.get("status_counts")),
        "top_sponsors": _top_pairs(land.get("top_sponsors")),
        "brief_kind": "local_ct_registry",
    }
    trials = land.get("sample_trials")
    if isinstance(trials, list) and trials:
        s["sample_trials"] = trials[:10]
    elif records:
        s["sample_trials"] = [{
            "id": r.get("registry_id") or r.get("nct_id") or r.get("id") or "-",
            "title": r.get("title") or "",
            "status": r.get("status") or "-",
        } for r in records[:10] if isinstance(r, dict)]
    if artifacts:
        s["note"] = "本地产物：" + ", ".join(str(x) for x in artifacts.values() if x)[:300]
    return s


def normalize_ct_safety(result: Any, artifacts: dict) -> dict:
    """ct-safety 产物 → safety brief summary（PRR/ROR + 2×2）。

    真实产物 disproportionality.json 结构：{table:{a,b,c,d}, PRR:{value,ci_low,ci_high},
    ROR:{...}, IC:{...}, EBGM:{...}, raw_counts, drug, event}。优先读它；stdout 的
    measures/counts_2x2/signals 作为兼容兜底。
    """
    body = result if isinstance(result, dict) else {}
    measures = body.get("measures") if isinstance(body.get("measures"), dict) else {}
    counts = body.get("counts_2x2") if isinstance(body.get("counts_2x2"), dict) else {}
    dispro = body.get("_disproportionality") if isinstance(body.get("_disproportionality"), dict) else {}
    if dispro:
        table = dispro.get("raw_counts") or dispro.get("table") or {}
        if isinstance(table, dict):
            counts = counts or {k: table.get(k) for k in ("a", "b", "c", "d")}
        prr = dispro.get("PRR") or {}
        ror = dispro.get("ROR") or {}
        if isinstance(prr, dict):
            measures = {
                "prr": prr.get("value"),
                "prr_ci95": [prr.get("ci_low"), prr.get("ci_high")],
                "chi2": prr.get("chi2"),
                "ror": ror.get("value") if isinstance(ror, dict) else None,
                "ror_ci95": ([ror.get("ci_low"), ror.get("ci_high")]
                             if isinstance(ror, dict) else None),
                "ic": (dispro.get("IC") or {}).get("value"),
                "ebgm": (dispro.get("EBGM") or {}).get("value"),
                "signal": dispro.get("signal_overall"),
            }
    if not counts and isinstance(body.get("signals"), list) and body["signals"]:
        first = body["signals"][0]
        if isinstance(first, dict):
            measures = measures or first.get("measures") or {}
            counts = counts or first.get("counts_2x2") or {}
    s = {
        "drug": str(body.get("drug") or dispro.get("drug") or ""),
        "event": str(body.get("event") or dispro.get("event") or ""),
        "counts_2x2": counts,
        "measures": measures,
        "brief_kind": "local_ct_safety",
    }
    if artifacts:
        s["note"] = "本地产物：" + ", ".join(str(x) for x in artifacts.values() if x)[:300]
    return s


def normalize_ct_literature(result: Any, artifacts: dict) -> dict:
    """ct-literature 产物 → literature brief summary（命中/去重/top works）。"""
    body = result if isinstance(result, dict) else {}
    merged = body.get("_merged") if isinstance(body.get("_merged"), dict) else {}
    if merged:
        # .merged.json 真实结构：{count, works, prisma, meta:{topic, ...}, verification}
        # 旧归一化只读顶层 total_hits/unique_works/topic → 全空。这里按真实路径回填。
        meta = merged.get("meta") if isinstance(merged.get("meta"), dict) else {}
        for k in ("topic", "topic_en", "sources_used", "search_topic"):
            if k in meta:
                body.setdefault(k, meta[k])
        if "topic" in merged:
            body.setdefault("topic", merged["topic"])
        count = merged.get("count")
        if count is not None:
            body.setdefault("total_hits", count)
            body.setdefault("unique_works", count)
        if "works" in merged:
            body.setdefault("works", merged["works"])
        # 兼容旧构建版（平铺字段）
        for k in ("total_hits", "unique_works", "topic", "sources_used"):
            if k in merged:
                body.setdefault(k, merged[k])
    works = body.get("works") or body.get("top_works") or []
    top = []
    for w in (works if isinstance(works, list) else [])[:8]:
        if not isinstance(w, dict):
            continue
        top.append({
            "title": w.get("title", ""),
            "year": w.get("year", w.get("publication_year", "")),
            "cited_by_count": w.get("cited_by_count", w.get("citation_count", 0)),
            "doi": w.get("doi", ""),
        })
    sources = [str(x) for x in (body.get("sources_used") or []) if x]
    if not sources:
        # .merged.json 无顶层 sources_used → 从 works[].source 去重汇总（保序）
        for w in (works if isinstance(works, list) else []):
            if not isinstance(w, dict):
                continue
            src = str(w.get("source") or "").strip()
            if src and src not in sources:
                sources.append(src)
    s = {
        "topic": str(body.get("topic", "") or ""),
        "total_hits": body.get("total_hits", body.get("total", 0)) or 0,
        "unique_works": body.get("unique_works", body.get("deduped_total", len(top))) or len(top),
        "sources_used": sources[:8],
        "top_works": top,
        "brief_kind": "local_ct_literature",
    }
    if artifacts:
        s["note"] = "本地产物：" + ", ".join(str(x) for x in artifacts.values() if x)[:300]
    return s


def normalize_ct_samplesize(result: Any, artifacts: dict) -> dict:
    """ct-samplesize 本地脚本 r_result → 样本量 brief summary。

    真实 r_result（本地脚本 stdout 的主 JSON）：
        {'n_per_group': 162, 'total': 324, 'power': 0.8, 'solve_for': 'n'}
    陈列器 plan_assemble_local._render_summary(ct-samplesize) 认
    test / mode / alpha / n / power / effect / summary / note。

    2026-11-20 修正：此前把本地已安装的 ct-samplesize 误归为"未知技能→文本兜底"，
    实际本地脚本可执行（engine=coze 指其底层调远端 R 服务，非无本地回退）。
    """
    # 非结构化文本（如远端失败回退）：据实呈现，绝不伪造数值
    if not isinstance(result, dict):
        return {"note": str(result)[:2000] if result else "本地脚本无结构化输出",
                "brief_kind": "local_text"}
    body = result
    p = body.get("_params") if isinstance(body.get("_params"), dict) else {}
    # 取样本量：优先每组 n（与脚本自身提取键一致），其次总量
    n, n_key = None, ""
    for k in ("n_per_group", "nPerGroup", "n1", "n", "n_total",
              "total_n", "N", "required_n", "total"):
        if body.get(k) is not None:
            n, n_key = body[k], k
            break
    total = body.get("total") if body.get("total") is not None else body.get("n_total")
    if total is None and n_key in ("total", "n_total", "total_n", "N", "required_n"):
        total = n
    effect = body.get("effect")
    if effect is None and p.get("p1") is not None and p.get("p2") is not None:
        effect = "p1=%s vs p2=%s" % (p.get("p1"), p.get("p2"))
    s = {
        "test": str(p.get("test") or body.get("test") or ""),
        "mode": str(body.get("solve_for") or body.get("mode") or "-"),
        "alpha": p.get("alpha", body.get("alpha")),
        "n": n,
        "power": body.get("power", p.get("power")),
        "effect": effect,
        "brief_kind": "local_ct_samplesize",
    }
    if n is not None:
        total_key = n_key in ("total", "n_total", "total_n", "N", "required_n")
        s["summary"] = ("总 N=%s" % n) if total_key else (
            "每组 n=%s" % n + (("，总 N=%s" % total) if total is not None and total != n else ""))
    if artifacts:
        s["note"] = "本地产物：" + ", ".join(str(x) for x in artifacts.values() if x)[:300]
    return s


_NORMALIZERS = {
    "ct-registry": normalize_ct_registry,
    "ct-safety": normalize_ct_safety,
    "ct-literature": normalize_ct_literature,
    "ct-samplesize": normalize_ct_samplesize,
}


def _normalize_summary(skill: str, result: Any, artifacts: dict) -> dict:
    fn = _NORMALIZERS.get(skill)
    if fn:
        return fn(result, artifacts)
    # 真正未知/未映射技能：本地脚本输出塞进 note 据实呈现
    return {"note": str(result)[:2000] if result else "本地脚本无结构化输出",
            "brief_kind": "local_text"}


# ── 真实产物注入 ────────────────────────────────────────────────────────────

def _find_artifact(workdir: Path, names: tuple) -> Optional[dict]:
    """在 workdir（含 out/ 子目录）下按文件名特征找 JSON 产物，读第一个命中。"""
    import glob as _glob
    for name in names:
        for p in _glob.glob(str(workdir / "**" / name), recursive=True):
            try:
                with open(p, encoding="utf-8") as f:
                    d = json.load(f)
                if isinstance(d, dict):
                    return d
            except Exception:  # noqa: BLE001 - 坏文件跳过
                continue
    return None


def _inject_artifacts(skill: str, workdir: Path, result: Any) -> Any:
    """把本地脚本权威产物的字段注入 result，供归一化读取（不覆盖已有真值）。"""
    extra = None
    if skill == "ct-safety":
        dispro = _find_artifact(workdir, ("disproportionality.json",))
        if dispro:
            extra = {"_disproportionality": dispro}
    elif skill == "ct-registry":
        agg = _find_artifact(workdir, ("agg.json", "agg_full.json"))
        if agg:
            extra = {"_agg": agg}
    elif skill == "ct-literature":
        # 2026-11-20 修复：ct-literature 真实产物是隐藏文件 `.merged.json`（点开头），
        # glob 的 `*.merged.json` / `merged.json` 都匹配不到 → 产物从未注入 →
        # summary 空（topic 空、0 hits）。补精确名 `.merged.json`。
        merged = _find_artifact(workdir, (".merged.json", "*.merged.json", "merged.json"))
        if merged:
            extra = {"_merged": merged}
    if not extra:
        return result
    base = dict(result) if isinstance(result, dict) else {}
    for k, v in extra.items():
        base.setdefault(k, v)
    return base


# ── 本地执行（复用 handle_need_tool 的现成能力）──────────────────────────────

def run_local_step(skill: str, params: dict, card: dict, expect: str) -> dict:
    """执行本地兄弟技能脚本 → 归一成 brief 同构 summary。异常不外抛。"""
    try:
        import handle_need_tool as hnt
    except Exception as e:  # noqa: BLE001
        return _err(skill, expect, "LOCAL_RUNNER_UNAVAILABLE:%s" % type(e).__name__)
    mapping = hnt._load_mapping()
    tool_cfg = mapping.get("skills", {}).get(skill)
    if not tool_cfg:
        return _err(skill, expect, "LOCAL_SKILL_UNMAPPED")
    # 装机检查：脚本落盘且客户端可调用（未装则不伪造结果）
    if not hnt._client_callable(skill):
        return _err(skill, expect, "LOCAL_SKILL_NOT_INSTALLED")
    try:
        full_params, missing = hnt._infer_missing_params(tool_cfg, params or {},
                                                          str((card or {}).get("original_question") or ""))
    except Exception as e:  # noqa: BLE001
        return _err(skill, expect, "LOCAL_PARAM_INFER_FAIL:%s" % type(e).__name__)
    if missing:
        return _err(skill, expect, "MISSING_REQUIRED:" + ",".join(str(m) for m in missing))
    try:
        cmd = hnt._build_cmd(tool_cfg, full_params)
    except Exception as e:  # noqa: BLE001
        return _err(skill, expect, "LOCAL_BUILD_CMD_FAIL:%s" % type(e).__name__)
    violation = hnt._execution_boundary_violation(cmd)
    if violation:
        return _err(skill, expect, "LOCAL_BOUNDARY:%s" % violation)

    workdir = hnt.CARDS_ROOT / skill
    try:
        workdir.mkdir(parents=True, exist_ok=True)
    except Exception as e:  # noqa: BLE001
        return _err(skill, expect, "LOCAL_WORKDIR_FAIL:%s" % type(e).__name__)
    env = dict(os.environ)
    env["CTSS_LOCALE"] = str((card or {}).get("locale") or "zh-CN")
    if (card or {}).get("query_origin"):
        env["CT_QUERY_ORIGIN"] = str(card["query_origin"])
    timeout = int(tool_cfg.get("timeout", 120))
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace", cwd=str(workdir),
            env=env, **hnt._hidden_kwargs())
    except subprocess.TimeoutExpired:
        return _err(skill, expect, "LOCAL_TIMEOUT")
    except FileNotFoundError:
        return _err(skill, expect, "LOCAL_SCRIPT_MISSING")
    except Exception as e:  # noqa: BLE001
        return _err(skill, expect, "LOCAL_EXEC_FAIL:%s" % type(e).__name__)
    if proc.returncode != 0:
        tail = ((proc.stderr or "") + "\n" + (proc.stdout or ""))[-500:]
        return _err(skill, expect, "LOCAL_RC_%s:%s" % (proc.returncode, tail.replace("\n", " ")))
    try:
        result = hnt._sanitize_result(hnt._extract_json(proc.stdout or ""))
        artifacts = hnt._read_artifacts(tool_cfg, workdir)
    except Exception as e:  # noqa: BLE001
        return _err(skill, expect, "LOCAL_ARTIFACT_FAIL:%s" % type(e).__name__)
    # 真实产物注入：本地脚本的权威数值在 out/ 子目录的产物文件里（stdout 常是过程日志）。
    # 若 stdout 未解析出结构化 dict，或产物含更权威字段，则注入后交给归一化。
    result = _inject_artifacts(skill, workdir, result)
    # 注入本次入参（r_result 常只含输出值，test/alpha/p1/p2 需从入参补齐）
    if isinstance(result, dict):
        result.setdefault("_params", dict(params or {}))
    # PREVIEW / KW-GATE 假成功守卫（与 handle_need_tool 同口径）
    engine = str(tool_cfg.get("engine", "local"))
    if engine != "coze" and isinstance(result, str):
        if "[PREVIEW]" in result and not artifacts:
            return _err(skill, expect, "LOCAL_PREVIEW_NO_RUN")
        if "[KW-GATE]" in result:
            return _err(skill, expect, "LOCAL_KW_GATE")
    summary = _normalize_summary(skill, result, artifacts or {})
    sys.stderr.write("[local-step] %s ok in %.1fs (summary keys=%s)\n" % (
        skill, time.time() - t0, list(summary.keys())))
    return _ok(skill, expect, summary)


# ── 离线自测 ────────────────────────────────────────────────────────────────

def self_test() -> int:
    ok = True

    def chk(label: str, cond: bool) -> None:
        nonlocal ok
        print("  [%s] %s" % ("PASS" if cond else "FAIL", label))
        ok = ok and cond

    print("local_step_runner 离线自测（不触网、不跑真实技能）")
    print("-" * 62)
    land = {"n_trials": 42, "phase_mix": [{"k": "Phase 3", "n": 12}, {"k": "Phase 2", "n": 30}],
            "top_sponsors": [{"k": "BMS", "n": 5}], "query": "NSCLC"}
    s1 = normalize_ct_registry({"landscape": land}, {})
    chk("registry total_hits", s1.get("total_hits") == 42)
    chk("registry phase_counts 归一", s1.get("phase_counts", {}).get("Phase 3") == 12)
    s2 = normalize_ct_safety({"drug": "sintilimab", "event": "hepatotoxicity",
                              "counts_2x2": {"a": 7, "b": 1177, "c": 22281, "d": 21030694},
                              "measures": {"prr": 5.59}}, {})
    chk("safety measures.prr", s2.get("measures", {}).get("prr") == 5.59)
    chk("safety 2x2", s2.get("counts_2x2", {}).get("a") == 7)
    s3 = normalize_ct_literature({"topic": "HCC", "total": 20, "unique_works": 18,
                                  "works": [{"title": "T", "year": 2022, "cited_by_count": 205,
                                             "doi": "10.1/x"}]}, {})
    chk("literature unique_works", s3.get("unique_works") == 18)
    chk("literature top_works 字段", s3.get("top_works", [{}])[0].get("doi") == "10.1/x")
    # ct-samplesize 本地已装且可执行（engine=coze 是底层引擎，非无本地回退）
    s4 = normalize_ct_samplesize(
        {"n_per_group": 162, "total": 324, "power": 0.8, "solve_for": "n",
         "_params": {"test": "proportion_two", "alpha": 0.05, "p1": 0.3, "p2": 0.45}}, {})
    chk("samplesize n_per_group→n", s4.get("n") == 162)
    chk("samplesize 总N入summary", "324" in str(s4.get("summary", "")))
    chk("samplesize test/alpha 补齐", s4.get("test") == "proportion_two" and s4.get("alpha") == 0.05)
    chk("samplesize brief_kind", s4.get("brief_kind") == "local_ct_samplesize")
    # 文本兜底只留给真正未知技能
    chk("未知技能走文本兜底", _normalize_summary("ct-nonexistent", "text", {}).get("brief_kind") == "local_text")
    chk("未映射技能 error", run_local_step("ct-sdtm", {}, {}, "x")["status"] == "error")
    print("-" * 62)
    print("结论：%s" % ("✅ 全部通过" if ok else "❌ 存在 FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="本地来源 plan 步骤执行器")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    print("用法：python adapters/local_step_runner.py --self-test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
