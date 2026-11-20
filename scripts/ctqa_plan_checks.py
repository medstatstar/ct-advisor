#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CTQA  PLAN 层：本轮 Plan 驱动改造的专项门禁（stdlib-only，不触网）。

背景（2026-11-18）：
  CTQA 六层（W0/W1/W2I/W2B/P3/C0）无一覆盖本轮新增的 Plan 功能——
  C0 只扫描 adapters/coze/tests/ 下既有测试，scripts/test_plan_runner.py
  与 plan 契约五副本、真实信封提取、四元组解包都不在门禁范围。
  故新增本脚本，经 ctqa.config.json 的 skill_tests 桥接为 PLAN 层。

覆盖：
  A. 复用 scripts/test_plan_runner.py 已有 24 项（契约五副本 / 校验 / 出域 / 凭据）
  B. plan_endpoints._dig_samplesize_summary 对**真实 v5 嵌套信封**的提取
     （审查 P0：此前只认顶层扁平键，stats/narrative 全丢）
  C. tool_router_node._match_tool 四元组 ↔ 节点解包一致性
     （部署报告 bug：三元组 + defaults_map 未绑定 → UnboundLocalError）
  D. 云端包字段声明（state.py plan/tool_results）与零凭据
  E. 复杂调用端到端（test_plan_e2e.py，32 项）：简单直答 / plan+本地收集+
     二次发送 / 云端整合 /(本地出最终答案，含失败标注与硬失败变体
  F. plan_gate 入口判定前移（v1.75，test_plan_gate.py）：三路分流结构 / 二次调用
     零 LLM 识别 / 白名单过滤 / 模型声明与技能数冲突以技能数为准 / tool_router 透传
  G. 用户确认菜单两阶段（v1.76，test_confirm_menu_e2e.py + test confirm_menu.py）：
     direct 不弹 / single 出答案+菜单 / multi 出菜单 / resume 按勾选执行+二次综合 /
     取消保留初步答案 / 越权 fail-closed / 二次 Coze 不通无兜底 / 开关回退

逐条结果以 `CTQA-CASE\t<status>\t<name>\t<detail>` 输出到 stdout，
供 ctqa.adapters.legacy 的 emit 协议导入（跨解释器、逐条粒度）。

用法：python scripts/ctqa_plan_checks.py
退出码：0 全过 / 1 有 FAIL
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ADVISOR = Path(__file__).resolve().parents[1]
SKILLS = ADVISOR.parent
PY = sys.executable
# CTQA-CASE 输出协议公共件上收 ct-base（与六组合脚本共用单一真相源）
sys.path.insert(0, str(SKILLS / "ct-base" / "testing"))
from ctqa.case_emit import emit, chk, get_fail  # noqa: E402


def main() -> int:
    print("CTQA PLAN 层：Plan 驱动改造专项门禁")

    # ---- A. 复用既有 24 项一致性与纯函数测试 ----
    p = subprocess.run([PY, str(ADVISOR / "scripts" / "test_plan_runner.py")],
                       capture_output=True, text=True, cwd=str(ADVISOR))
    for line in (p.stdout or "").splitlines():
        s = line.strip()
        if s.startswith("[PASS] "):
            emit("pass", "T1 " + s[len("[PASS] "):])
        elif s.startswith("[FAIL] "):
            emit("fail", "T1 " + s[len("[FAIL] "):])
    chk("T1 test_plan_runner 整体退出码", p.returncode == 0,
        "exit=%d" % p.returncode)

    # ---- B. samplesize 真实 v5 嵌套信封提取（审查 P0）----
    sys.path.insert(0, str(ADVISOR / "adapters"))
    try:
        import plan_endpoints as pe
        # 真实 ct-samplesize v5 信封：核心数值在 stats / narrative
        real = {
            "status": "ok",
            "stats": {"test": "two_proportion", "n": 120, "power": 0.8,
                      "effect": 0.2, "alpha": 0.05},
            "narrative": "结论：每组 n=120，检验效能 0.80",
            "figures": ["base64blob..."], "notes": "", "test": "two_proportion",
        }
        dig = pe._dig_samplesize_summary(real)
        # 判定：至少拿到嵌套 stats 里的一个核心数值字段
        got_n = dig.get("n") == 120 or (isinstance(dig.get("stats"), dict)
                                        and dig["stats"].get("n") == 120)
        got_power = dig.get("power") == 0.8 or (isinstance(dig.get("stats"), dict)
                                                and dig["stats"].get("power") == 0.8)
        chk("B1 samplesize 嵌套 stats.n 提取", got_n, "dig=%s" % json.dumps(dig, ensure_ascii=False))
        chk("B2 samplesize 嵌套 stats.power 提取", got_power, "dig=%s" % json.dumps(dig, ensure_ascii=False))
        chk("B3 大对象 figures 被剔除",
            "figures" not in dig and all(
                not (isinstance(v, list) and len(v) > 50) for v in dig.values()),
            "dig=%s" % json.dumps(dig, ensure_ascii=False))
    except Exception as e:  # noqa: BLE001
        emit("error", "B plan_endpoints 可加载", "%s: %s" % (type(e).__name__, e))

    # ---- C. 四元组 ↔ 解包一致性（部署报告 bug）----
    tr = ADVISOR / "adapters/coze/src/graphs/nodes/tool_router_node.py"
    try:
        src = tr.read_text(encoding="utf-8")
        tree = ast.parse(src)
        # 找 _match_tool 的所有 return 元数
        fn = next((n for n in tree.body
                   if isinstance(n, ast.FunctionDef) and n.name == "_match_tool"), None)
        chk("C1 _match_tool 函数存在", fn is not None)
        if fn:
            returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)
                       and n.value is not None]
            tuple_lens = []
            for r in returns:
                if isinstance(r.value, ast.Tuple):
                    tuple_lens.append(len(r.value.elts))
                elif isinstance(r.value, ast.Name):
                    tuple_lens.append("name")  # return primary, ... 也是 Tuple（逗号表达式）
            # 三处有效返回（指南 early / 常规 / 无命中 None 不计）都应为 4
            chk("C2 _match_tool 有效 return 均为四元组",
                all(x == 4 for x in tuple_lens if x != "name"),
                "return_lens=%s" % tuple_lens)
        # 节点解包必须是四变量
        chk("C3 节点解包含 defaults_map",
            "tool, defaults, hits, defaults_map = matched" in src)
        chk("C4 _build_plan 消费 defaults_map",
            "plan=_build_plan(hits, defaults_map)" in src)
        chk("C5 无残留三元组解包",
            "tool, defaults, hits = matched" not in src)
    except Exception as e:  # noqa: BLE001
        emit("error", "C tool_router_node 可解析", "%s: %s" % (type(e).__name__, e))

    # ---- E. 复杂调用端到端（四点完整数据流）----
    p2 = subprocess.run([PY, str(ADVISOR / "scripts" / "test_plan_e2e.py")],
                        capture_output=True, text=True, cwd=str(ADVISOR))
    for line in (p2.stdout or "").splitlines():
        s = line.strip()
        if s.startswith("[PASS] "):
            emit("pass", "E2E " + s[len("[PASS] "):])
        elif s.startswith("[FAIL] "):
            emit("fail", "E2E " + s[len("[FAIL] "):])
    chk("E2E test_plan_e2e 整体退出码", p2.returncode == 0,
        "exit=%d" % p2.returncode)

    # ---- F. plan_gate 入口判定前移（v1.75，三路分流 / 零 LLM 二次识别 / 透传）----
    p3 = subprocess.run([PY, str(ADVISOR / "scripts" / "test_plan_gate.py")],
                        capture_output=True, text=True, cwd=str(ADVISOR))
    for line in (p3.stdout or "").splitlines():
        s = line.strip()
        if s.startswith("[PASS] "):
            emit("pass", "GATE " + s[len("[PASS] "):])
        elif s.startswith("[FAIL] "):
            emit("fail", "GATE " + s[len("[FAIL] "):])
    chk("GATE test_plan_gate 整体退出码", p3.returncode == 0,
        "exit=%d" % p3.returncode)

    # ---- G. 用户确认菜单两阶段（v1.76）----
    for _script, _tag in (("test_confirm_menu_e2e.py", "CONFIRM"),
                          ("confirm_menu.py", "CMUNIT")):
        if _script.startswith("test_"):
            _args = [PY, str(ADVISOR / "scripts" / _script)]
        else:
            _args = [PY, str(ADVISOR / "adapters" / _script), "--self-test"]
        p4 = subprocess.run(_args, capture_output=True, text=True, cwd=str(ADVISOR))
        for line in (p4.stdout or "").splitlines():
            s = line.strip()
            if s.startswith("[PASS] "):
                emit("pass", "%s " % _tag + s[len("[PASS] "):])
            elif s.startswith("[FAIL] "):
                emit("fail", "%s " % _tag + s[len("[FAIL] "):])
            elif s.strip().startswith("[PASS]"):  # 自测的 "  [PASS] label" 形态
                emit("pass", "%s " % _tag + s.strip()[len("[PASS]"):].strip())
            elif s.strip().startswith("[FAIL]"):
                emit("fail", "%s " % _tag + s.strip()[len("[FAIL]"):].strip())
        chk("%s %s 整体退出码" % (_tag, _script), p4.returncode == 0,
            "exit=%d" % p4.returncode)

    # ---- D. 云端字段声明 / 零凭据 ----
    st = ADVISOR / "adapters/coze/src/graphs/state.py"
    try:
        state_src = st.read_text(encoding="utf-8")
        chk("D1 state.plan 字段声明 ≥4",
            state_src.count("plan: List[Dict[str, Any]]") >= 4,
            "count=%d" % state_src.count("plan: List[Dict[str, Any]]"))
        chk("D2 state.tool_results 字段声明 ≥5",
            state_src.count("tool_results: Dict[str, Any]") >= 5,
            "count=%d" % state_src.count("tool_results: Dict[str, Any]"))
    except Exception as e:  # noqa: BLE001
        emit("error", "D state.py 可解析", "%s: %s" % (type(e).__name__, e))

    # 云端包零凭据（取最新 zip）
    try:
        coze_dir = ADVISOR / "adapters/coze"
        zips = sorted(coze_dir.glob("ct-advisor_coze_v*.zip"))
        chk("D3 存在云端部署包", bool(zips), "zips=%d" % len(zips))
        if zips:
            z = zipfile.ZipFile(zips[-1])
            tainted = [n for n in z.namelist()
                       if n.endswith(".py") and b"ct_samplesize_coze" in z.read(n)]
            chk("D4 云端包零凭据", not tainted, "tainted=%s" % tainted)
    except Exception as e:  # noqa: BLE001
        emit("error", "D 云端包可扫描", "%s: %s" % (type(e).__name__, e))

    print("\nCTQA PLAN 结论：FAIL %d" % get_fail())
    return 1 if get_fail() else 0


if __name__ == "__main__":
    sys.exit(main())
