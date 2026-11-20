#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CTQA 六组合矩阵：调用方式 × 问题类型的端到端一致性门禁（stdlib-only，零外网）。

§16.9 exempt — urllib.request is used ONLY against the local loopback workbench proxy
(http://127.0.0.1:8900), never any external endpoint; this is a test harness, not an
outbound adapter. Verified by PROXY constant below.

背景（2026-11-20 用户要求）：此前按 bug 逐个修反复复发，用户要求一次性做全面 CTQA。
本脚本把「两种调用方式 × 三种问题类型」固化成 6 组合矩阵，逐组验证同一问题的
判定/参数/菜单/缝合在两条路径上一致，作为可永久回归的门禁（经 ctqa.config.json
的 skill_tests 桥接，或独立运行）。

调用方式（2）：
  - WORKBENCH：工作台页面调用。走 proxy 的本地可离线端点 `/api/route-hint`
    （后端 local_route_predict → route_tool.predict）与 `/api/plan-menu`
    （confirm_menu 菜单构造，含本地抽参补齐）。服务未起时自动降级为直接调
    local_route_predict 函数 + confirm_menu 函数，仍零外网。
  - PROMPT：上下文提示词调用。走 entry.py --q 的本地预判链路
    route_tool.predict + orchestrate.resolve_need_tools + confirm_menu。

问题类型（3）：
  - PLAIN  普通问题：need_tool=None / need_tools=[] / 无菜单
  - SINGLE 单技能调用：need_tools=[tool] / ambiguity=single / 菜单 mode=single
  - MULTI  多技能调用：need_tools>=2 / split_advice=True / 菜单 mode=multi

每组校验维度：路由判定、参数抽取（cond/intr）、菜单 mode/candidates、
Coze 优先仲裁、长上下文抗污染（法条名/限定词不污染 cond）。

逐条结果以 `CTQA-CASE\t<status>\t<name>\t<detail>` 输出（兼容 ctqa emit 协议）。

用法：
  python scripts/ctqa_six_matrix.py            # 自动探测 proxy（在则走 HTTP，否则降级函数层）
  python scripts/ctqa_six_matrix.py --no-http  # 强制只走函数层
  python scripts/ctqa_six_matrix.py --json OUT # 额外写 JSON 报告
退出码：0 全过 / 1 有 FAIL
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

ADVISOR = Path(__file__).resolve().parents[1]
SKILLS = ADVISOR.parent
sys.path.insert(0, str(ADVISOR / "scripts"))
sys.path.insert(0, str(ADVISOR / "adapters"))
sys.path.insert(0, str(ADVISOR / "workbench"))
sys.path.insert(0, str(ADVISOR))
# CTQA-CASE 输出协议公共件上收 ct-base（单一真相源，与 legacy 解析侧配对）
sys.path.insert(0, str(SKILLS / "ct-base" / "testing"))
from ctqa.case_emit import (  # noqa: E402
    emit, chk, get_fail, get_results, passed as count_passed,
)

PROXY = "http://127.0.0.1:8900"
PROXY_UP = False


def probe_proxy():
    try:
        r = urllib.request.urlopen(PROXY + "/api/health", timeout=2)
        return r.status == 200 and json.loads(r.read()).get("ok") is True
    except Exception:
        return False


def http_post(path, payload):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(PROXY + path, data=data,
                                 headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=8)
    return json.loads(r.read().decode("utf-8"))


# ── 两条调用路径的统一取数 ────────────────────────────────────────────────────
def route_workbench(q):
    """工作台页面路径：优先 HTTP /api/route-hint，降级 proxy.local_route_predict。"""
    if PROXY_UP:
        try:
            d = http_post("/api/route-hint", {"question": q})
            return {"source": "http", "need_tool": d.get("need_tool"),
                    "need_tools": d.get("need_tools") or [],
                    "ambiguity": d.get("ambiguity"),
                    "split_advice": bool(d.get("split_advice")),
                    "complexity_hint": d.get("complexity_hint") or ""}
        except Exception as e:
            emit("error", "WB.route.http", "端点调用失败已降级: %s" % e)
    # 降级：直接调 proxy 函数（与 /api/route-hint 同一真相源）
    # 文件名含连字符（ct-advisor-proxy.py），须按路径加载而非常规 import
    import importlib.util  # noqa: E402
    spec = importlib.util.spec_from_file_location(
        "ct_advisor_proxy", ADVISOR / "workbench" / "ct-advisor-proxy.py")
    proxy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proxy)
    d = proxy.local_route_predict(q)
    return {"source": "func", "need_tool": d.get("need_tool"),
            "need_tools": d.get("need_tools") or [],
            "ambiguity": d.get("ambiguity"),
            "split_advice": bool(d.get("split_advice")),
            "complexity_hint": d.get("complexity_hint") or ""}


def route_prompt(q):
    """上下文提示词路径：entry.py --q 的本地预判（route_tool.predict）。"""
    import route_tool as R  # noqa: E402
    p = R.predict(q)
    return {"source": "predict", "need_tool": p.get("need_tool"),
            "need_tools": p.get("need_tools") or [],
            "ambiguity": p.get("ambiguity"),
            "split_advice": bool(p.get("split_advice")),
            "complexity_hint": p.get("complexity_hint") or "",
            "params": p.get("params") or {}}


def params_workbench(q, candidates):
    """工作台补参：与 /api/plan-menu STEP1 同口径（route_tool 抽参）。

    注意菜单 payload 只含 token/mode/options（安全设计，不回显参数）；
    权威参数在 confirm_menu.PENDING_DIR 落盘的 state 里。HTTP 模式下从
    落盘 state 只读读取 prefetch_params/plan 做断言，不消费 token。
    """
    import route_tool as R  # noqa: E402
    if PROXY_UP:
        try:
            d = http_post("/api/plan-menu", {
                "plan": [], "need_tools": candidates,
                "need_tool": candidates[0] if candidates else "",
                "original_question": q, "draft_answer": "", "prefetch_params": {},
            })
            menu = d.get("menu")
            out = {"source": "http", "menu": menu, "note": d.get("note")}
            if isinstance(menu, dict) and menu.get("token"):
                # 只读落盘 state（不调用 load_pending，避免一次性消费）
                from adapters import confirm_menu as CM  # noqa: E402
                st = CM.PENDING_DIR / ("%s.json" % menu["token"])
                if st.exists():
                    blob = json.loads(st.read_text(encoding="utf-8"))
                    out["plan"] = blob.get("plan") or []
                    out["prefetch"] = blob.get("prefetch_params") or {}
            return out
        except Exception as e:
            emit("error", "WB.menu.http", "端点调用失败已降级: %s" % e)
    # 降级函数层：直接拼菜单（与 proxy 同逻辑）
    from adapters import confirm_menu as CM  # noqa: E402
    cands = CM.menu_candidates([], candidates, candidates[0] if candidates else "")
    if not cands:
        return {"source": "func", "menu": None, "note": "NO_CANDIDATES"}
    mode = CM.mode_of([], cands)
    prefetch = dict(R.extract_params_for_tools(cands, q))
    norm = CM.normalize_plan([], cands, {s: prefetch for s in cands})
    payload = CM.build_menu_payload("0" * 16, mode, q, cands)
    payload["hint"] = CM.menu_question(mode, cands)
    return {"source": "func", "menu": payload, "plan": norm,
            "prefetch": prefetch, "mode": mode}


# ── 6 组合用例 ────────────────────────────────────────────────────────────────
# (case_id, 类型, 问题, 期望need_tools集合, 期望mode, 参数断言函数)
PLAIN_Q = "什么是临床试验方案"
SINGLE_Q = "检索 PD-1 三线 NSCLC 的注册 III 期试验。"
MULTI_Q = "检索 PD-1 三线 NSCLC 的注册 III 期试验，并查一下相关文献"
LONG_CTX = (SINGLE_Q + "\n初步说明（首趟生成，仅供参考）\n"
            "可通过 CDE 按限定PD-1单抗检索。\n"
            "依据：CDE《抗肿瘤药物临床试验技术指导原则（2020年版）》\n"
            "原因码：MISSING_REQUIRED:cond")

CASES = [
    ("W-PLAIN", "WORKBENCH", "PLAIN", PLAIN_Q, set(), None),
    ("W-SINGLE", "WORKBENCH", "SINGLE", SINGLE_Q, {"ct-registry"}, "single"),
    ("W-MULTI", "WORKBENCH", "MULTI", MULTI_Q,
     {"ct-registry", "ct-literature"}, "multi"),
    ("P-PLAIN", "PROMPT", "PLAIN", PLAIN_Q, set(), None),
    ("P-SINGLE", "PROMPT", "SINGLE", SINGLE_Q, {"ct-registry"}, "single"),
    ("P-MULTI", "PROMPT", "MULTI", MULTI_Q,
     {"ct-registry", "ct-literature"}, "multi"),
]


def check_case(cid, path, qtype, q, exp_tools, exp_mode):
    router = route_workbench if path == "WORKBENCH" else route_prompt
    r = router(q)
    chk("%s.%s.route" % (cid, path),
        set(r["need_tools"]) == exp_tools,
        "need=%s tools=%s amb=%s split=%s src=%s" %
        (r["need_tool"], r["need_tools"], r["ambiguity"],
         r["split_advice"], r["source"]))

    if qtype == "PLAIN":
        chk("%s.%s.no_tool" % (cid, path),
            r["need_tool"] is None and not r["need_tools"],
            "普通问题不得触发工具")
    elif qtype == "SINGLE":
        chk("%s.%s.single" % (cid, path),
            len(r["need_tools"]) == 1 and r["ambiguity"] == "single"
            and not r["split_advice"],
            "single 判定: %s" % r["need_tools"])
    elif qtype == "MULTI":
        chk("%s.%s.multi" % (cid, path),
            len(r["need_tools"]) >= 2 and r["split_advice"]
            and r["ambiguity"] == "multi",
            "multi 判定: %s split=%s" % (r["need_tools"], r["split_advice"]))
        chk("%s.%s.hint" % (cid, path),
            bool(r["complexity_hint"]),
            "multi 必须有复杂调用提示")

    # 菜单层：两条路径都要能构造正确 mode 的菜单
    candidates = list(r["need_tools"]) or ([r["need_tool"]] if r["need_tool"] else [])
    if qtype == "PLAIN":
        m = params_workbench(q, [])
        chk("%s.%s.menu_none" % (cid, path),
            m.get("menu") is None,
            "无候选不得弹菜单: %s" % m.get("note"))
    else:
        m = params_workbench(q, candidates)
        menu = m.get("menu")
        chk("%s.%s.menu" % (cid, path),
            isinstance(menu, dict) and menu.get("mode") == exp_mode
            and bool(menu.get("token")),
            "mode=%s candidates=%s src=%s" %
            (menu.get("mode") if menu else None,
             menu.get("options") if menu else None, m.get("source")))
        hint = (menu or {}).get("hint") or ""
        chk("%s.%s.disclaimer" % (cid, path),
            "快捷参考信息" in hint and "ct.medstatstar.com" in hint,
            "菜单需含快捷参考免责声明与域名")

    # 参数层（prompt 路径直接读 predict；workbench 路径从菜单 plan 读）
    if qtype in ("SINGLE", "MULTI"):
        if path == "PROMPT":
            chk("%s.%s.params" % (cid, path),
                r["params"].get("cond") == "NSCLC"
                and r["params"].get("intr") == "PD-1",
                "params=%s" % r["params"])
        else:
            prefetch = m.get("prefetch") or {}
            chk("%s.%s.params" % (cid, path),
                prefetch.get("cond") == "NSCLC" and prefetch.get("intr") == "PD-1",
                "菜单 prefetch_params: %s (src=%s)" %
                (prefetch, m.get("source")))


def check_long_context():
    """跨路径抗污染：长上下文在两条路径都不得污染 cond。"""
    for tag, router in (("P", route_prompt), ("W", route_workbench)):
        r = router(LONG_CTX)
        chk("CTX.%s.long_route" % tag,
            set(r["need_tools"]) == {"ct-registry"},
            "长上下文仍判 registry: %s" % r["need_tools"])
        if tag == "P":
            p = r.get("params") or {}
            good = p.get("cond") == "NSCLC" and p.get("intr") == "PD-1"
            bad = "抗肿瘤" in (p.get("cond") or "") \
                or "按限定" in (p.get("intr") or "")
            chk("CTX.P.long_params", good and not bad,
                "cond=%s intr=%s" % (p.get("cond"), p.get("intr")))
        else:
            m = params_workbench(LONG_CTX, ["ct-registry"])
            prefetch = m.get("prefetch") or {}
            cond, intr = prefetch.get("cond") or "", prefetch.get("intr") or ""
            chk("CTX.W.long_params",
                cond == "NSCLC" and intr == "PD-1"
                and "抗肿瘤" not in cond and "按限定" not in intr,
                "菜单 prefetch_params: %s (src=%s)" %
                (prefetch, m.get("source")))


def check_coze_priority():
    """Coze 优先仲裁：两路径判断冲突时以 Coze 为准（单一真相源）。"""
    import orchestrate as O  # noqa: E402
    chk("ARB.coze_wins",
        O.resolve_need_tools(["ct-safety"], ["ct-registry"]) == ["ct-safety"],
        "冲突取 Coze")
    chk("ARB.local_fallback",
        O.resolve_need_tools([], ["ct-registry"]) == ["ct-registry"],
        "Coze 空取本地兜底")


def main():
    global PROXY_UP
    ap = argparse.ArgumentParser(description="CTQA 六组合矩阵门禁")
    ap.add_argument("--no-http", action="store_true", help="强制只走函数层")
    ap.add_argument("--json", help="额外写 JSON 报告")
    args = ap.parse_args()

    print("CTQA 六组合矩阵：调用方式(2) × 问题类型(3)")
    print("=" * 60)
    if not args.no_http:
        PROXY_UP = probe_proxy()
    print("工作台服务: %s（%s）" %
          ("在线 HTTP" if PROXY_UP else "离线/降级函数层",
           PROXY if PROXY_UP else "直接调 local_route_predict"))

    # workbench 目录进 path（降级调 proxy 模块）
    sys.path.insert(0, str(ADVISOR / "workbench"))

    for cid, path, qtype, q, exp_tools, exp_mode in CASES:
        print("\n--- %s [%s × %s] ---" % (cid, path, qtype))
        check_case(cid, path, qtype, q, exp_tools, exp_mode)

    print("\n--- 跨路径：长上下文抗污染 ---")
    check_long_context()
    print("\n--- 跨路径：Coze 优先仲裁 ---")
    check_coze_priority()

    results = get_results()
    total = len(results)
    n_passed = count_passed()
    print("\n" + "=" * 60)
    print("CTQA 六组合结果: %d/%d PASS, %d FAIL" % (n_passed, total, get_fail()))

    if args.json:
        Path(args.json).write_text(
            json.dumps({"summary": {"total": total, "passed": n_passed,
                                    "failed": get_fail(), "proxy_up": PROXY_UP},
                        "cases": results}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        print("JSON 报告: %s" % args.json)

    return 0 if get_fail() == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
