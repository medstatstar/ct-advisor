#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_route_drift.py — 工具路由规则「两端独立实现」漂移检测（stdlib-only）

背景（2026-09-24 审计实测）：
    scripts/route_tool.py（本地，33.4 KB）与
    adapters/coze/src/graphs/nodes/tool_router_node.py（Coze 端，22.1 KB）
    是**两套独立演化**的实现：常量命名（TOOL_TRIGGERS vs TOOL_RULES）、
    函数命名（predict vs _match_tool）、正则字面量均不一致。
    SKILL.md 称二者 "enforced identically"，实测不成立。

风险：
    本地 orchestrate.py 用本地规则做**预取**预测，服务端用另一套规则做 need_tool
    权威判定 → 同一问题两端可能给出不同判断，预取与最终需求错位。

本脚本只做**检测与报告**，不自动统一（统一属行为变更，需人工决策）：
    - WEAK_TRIGGERS 按技能分组比对：共有技能严格门禁，一端独有技能列 INFO
      （2026-11-20：全局混合比对曾把本地独有的 ct-protocol/ct-sas2r 软建议
      误报为 58 词漂移，实测共有 4 技能词表零差异）
    - 各技能（ct-registry / ct-safety / ...）关键词集合的对称差

用法：
    python scripts/check_route_drift.py
    python scripts/check_route_drift.py --quiet

退出码：
    0 = 无显著差异
    1 = 检出显著差异（仅提示，不阻断）
    2 = 文件缺失 / 解析失败
"""

from __future__ import annotations

import argparse
import ast
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SKILL = os.path.dirname(_HERE)

LOCAL = os.path.join(_HERE, "route_tool.py")
COZE = os.path.join(_SKILL, "adapters", "coze", "src", "graphs", "nodes",
                    "tool_router_node.py")

# 两端对应的容器变量名（本地: Coze）
TOOL_NAMES = ("TOOL_TRIGGERS", "TOOL_RULES")

SKILLS = ("ct-samplesize", "ct-registry", "ct-safety", "ct-literature")


def _collect_strings(node):
    """递归收集 AST 子树中的字符串字面量。"""
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.append(n.value)
    return out


def _parse_assigns(path):
    """返回 {变量名: [字符串字面量]}，只取模块级与函数内的简单赋值。"""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read())
    res = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    res.setdefault(tgt.id, []).extend(_collect_strings(node.value))
    return res


def _tokens(strings):
    """从正则字面量里抽出可比较的『裸词』。

    关键：先剥离**正则词法前缀/后缀**再做切分，否则同一批词会因写法不同
    被误判为漂移（实测教训：本地写 `\bliterature`，Coze 写 `literature`，
    若不剥离 `\b` 会得到 5 对「伪差异」；Coze 的 `~在研` 同理）。
    """
    import re as _re
    toks = set()
    for s in strings:
        s = s.replace("\\b", " ").replace("~", " ")   # 词边界 / Coze 否定前缀
        for piece in _re.split(r"[|()\[\]{}?*+\\^$./\\s]+", s):
            p = piece.strip()
            if len(p) >= 2:
                toks.add(p.lower())
    return toks


def _weak_by_skill(path: str) -> dict:
    """按技能分组提取 WEAK_TRIGGERS 的 token（两端结构不同，分别解析）。

    本地 WEAK_TRIGGERS 是 dict[str, re.Pattern]；Coze 端是 list[(keywords, skill)]。
    全局混合 token 比对会把「本地独有的新技能词」误算成「共有规则漂移」——
    2026-11-20 实测：所谓 58 词差异实为本地独有的 ct-protocol/ct-sas2r 两个
    软建议技能（23+33 词），两端共有的 4 个技能词表其实 100% 一致。
    分组后：共有技能做严格门禁，一端独有技能另列 INFO，不再混淆两种维度。
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read())
    out: dict = {}
    weak_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "WEAK_TRIGGERS"
                for t in node.targets):
            weak_node = node.value
            break
    if weak_node is None:
        return out
    if isinstance(weak_node, ast.Dict):
        # 本地：{skill: re.compile(...)}
        for k, v in zip(weak_node.keys, weak_node.values):
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                out.setdefault(k.value, set()).update(_tokens(_collect_strings(v)))
    elif isinstance(weak_node, (ast.List, ast.Tuple)):
        # Coze：[(keywords_list, "skill"), ...]
        for elt in weak_node.elts:
            if isinstance(elt, (ast.Tuple, ast.List)) and len(elt.elts) == 2:
                kw_node, skill_node = elt.elts
                if isinstance(skill_node, ast.Constant) and isinstance(skill_node.value, str):
                    out.setdefault(skill_node.value, set()).update(
                        _tokens(_collect_strings(kw_node)))
    return out


INTENT_CONTRACT = os.path.join(_SKILL, "config", "intent_contract.json")
PLAN_CONTRACT = os.path.join(_SKILL, "config", "plan_contract.json")
_INTENT_VARS = (
    ("consult_depth", "_INTENT_CONSULT_DEPTH"),
    ("exec_intent", "_INTENT_EXEC"),
    ("retrieval_intent", "_INTENT_RETRIEVAL"),
)


def _plan_const(path, var):
    """AST 提取模块级字面量常量（list / dict / str / int，杜绝 import 云端依赖）。"""
    import ast as _ast
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        tree = _ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == var:
                    try:
                        return _ast.literal_eval(node.value)
                    except Exception:  # noqa: BLE001 - 非字面量按不可用处理
                        return None
    return None


def _intent_const(path, var):
    """AST 提取模块级字符串常量（杜绝 import 触发云端专有依赖）。"""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == var:
                    v = node.value
                    if isinstance(v, ast.Constant) and isinstance(v.value, str):
                        return v.value
    return None


def _check_intent_contract():
    """2026-11-09 阻断级门禁：契约 + 本地 + 云端三份意图词表逐字一致。

    Coze 包源码不能跨技能 import 本地 JSON，故两端各持内嵌副本；
    任何单边改动都必须在这里被拦下，否则会出现「本地不预判、云端仍委托」。
    """
    import json as _json
    problems = []
    try:
        with open(INTENT_CONTRACT, "r", encoding="utf-8") as f:
            patterns = _json.load(f)["patterns"]
    except Exception as e:  # noqa: BLE001
        return ["intent_contract.json 不可用: %s: %s" % (type(e).__name__, e)]
    for key, var in _INTENT_VARS:
        want = patterns.get(key)
        if not want:
            problems.append("契约缺 pattern %s" % key)
            continue
        for label, path in (("本地", LOCAL), ("云端", COZE)):
            try:
                got = _intent_const(path, var)
            except Exception as e:  # noqa: BLE001
                problems.append("%s %s AST 解析失败: %s" % (label, var, e))
                continue
            if got != want:
                problems.append("%s %s 与 intent_contract.json 不一致" % (label, var))
    return problems


def _check_plan_contract():
    """2026-11-18 阻断级门禁：plan 契约 ↔ 云端四份内嵌副本逐字一致。

    Coze 包源码不能跨技能 import 本地 JSON，故云端持内嵌副本；任何单边改动
    都必须在这里被拦下，否则云端产出的 plan 与本地 plan_runner 校验器对不上。
    """
    import json as _json
    problems = []
    try:
        with open(PLAN_CONTRACT, "r", encoding="utf-8") as f:
            spec = _json.load(f)
    except Exception as e:  # noqa: BLE001
        return ["plan_contract.json 不可用: %s: %s" % (type(e).__name__, e)]

    pairs = (
        ("skills", "_PLAN_SKILLS"),
        ("param_allowlist", "_PLAN_PARAM_ALLOWLIST"),
        ("plan.expect_enum", "_PLAN_EXPECT_ENUM"),
        ("plan.max_steps", "_PLAN_MAX_STEPS"),
        ("expect_by_skill", "_PLAN_EXPECT_BY_SKILL"),
    )
    for key, var in pairs:
        if "." in key:
            a, b = key.split(".", 1)
            want = (spec.get(a) or {}).get(b)
        else:
            want = spec.get(key)
        if want is None:
            problems.append("plan 契约缺 %s" % key)
            continue
        try:
            got = _plan_const(COZE, var)
        except Exception as e:  # noqa: BLE001
            problems.append("云端 %s AST 解析失败: %s" % (var, e))
            continue
        if got != want:
            problems.append("云端 %s 与 plan_contract.json 不一致" % var)
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="工具路由规则两端漂移检测")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not (os.path.isfile(LOCAL) and os.path.isfile(COZE)):
        if not args.quiet:
            print("  文件缺失: %s / %s" % (LOCAL, COZE))
        return 2

    try:
        a, b = _parse_assigns(LOCAL), _parse_assigns(COZE)
    except SyntaxError as e:
        if not args.quiet:
            print("  解析失败: %r" % (e,))
        return 2

    intent_problems = _check_intent_contract()
    if intent_problems:
        print("🔴 INTENT_CONTRACT_MISMATCH（阻断级，云端包发布前必须修复）")
        for p in intent_problems:
            print("    - %s" % p)
        return 2

    plan_problems = _check_plan_contract()
    if plan_problems:
        print("🔴 PLAN_CONTRACT_MISMATCH（阻断级，云端包发布前必须修复）")
        for p in plan_problems:
            print("    - %s" % p)
        return 2
    if not args.quiet:
        print("Plan 契约五副本 AST 一致性: ✅ 通过")

    problems = []

    if not args.quiet:
        print("意图契约三副本 AST 一致性: ✅ 通过")
        print("工具路由规则 两端漂移检测")
        print("=" * 66)
        print("  本地  %s" % os.path.relpath(LOCAL, _SKILL))
        print("  Coze  %s" % os.path.relpath(COZE, _SKILL))
        print("-" * 66)

    # 1) WEAK_TRIGGERS（2026-11-20 改为按技能分组比对）
    #    共有技能 = 真正可比的同一规则 → 严格门禁（差异即漂移）。
    #    一端独有技能 = 本地新增的软建议（如 ct-protocol/ct-sas2r）→ 仅 INFO，
    #    不计入 problems（云端设计性不带这些本地技能的弱规则，不是漂移）。
    wa = _weak_by_skill(LOCAL)
    wb = _weak_by_skill(COZE)
    common = sorted(set(wa) & set(wb))
    only_local = sorted(set(wa) - set(wb))
    only_coze = sorted(set(wb) - set(wa))
    if not args.quiet:
        print("  %-16s 共有技能 %d / 仅本地 %d / 仅Coze %d"
              % ("WEAK_TRIGGERS", len(common), len(only_local), len(only_coze)))
        print("  共有技能逐项严格比对（有差异即漂移）:")
    for sk in common:
        ta, tb = wa[sk], wb[sk]
        only_a, only_b = ta - tb, tb - ta
        if not args.quiet:
            flag = "✅" if not only_a and not only_b else "⚠️"
            print("    %-16s 本地%3d / Coze%3d / 仅本地%2d / 仅Coze%2d  %s"
                  % (sk, len(ta), len(tb), len(only_a), len(only_b), flag))
            if only_a:
                print("        仅本地: %s" % ", ".join(sorted(only_a)[:12]))
            if only_b:
                print("        仅Coze: %s" % ", ".join(sorted(only_b)[:12]))
        if only_a or only_b:
            problems.append("%s/%s: 差异 %d 词" %
                            (name, sk, len(only_a) + len(only_b)))
    if not args.quiet:
        if only_local:
            print("  仅本地技能（INFO，云端设计性不带，非漂移）:")
            for sk in only_local:
                print("    %-16s %d 词" % (sk, len(wa[sk])))
        if only_coze:
            print("  仅Coze技能（INFO）:")
            for sk in only_coze:
                print("    %-16s %d 词" % (sk, len(wb[sk])))

    # 2) 技能级关键词（两端容器内按技能名切分）
    if not args.quiet:
        print("-" * 66)
    for sk in SKILLS:
        ta = _tokens([s for s in a.get(TOOL_NAMES[0], []) if sk in s])
        tb = _tokens([s for s in b.get(TOOL_NAMES[1], []) if sk in s])
        n_local, n_coze = len(ta), len(tb)
        inter = len(ta & tb)
        if not args.quiet:
            print("  %-16s 本地 %2d 词 / Coze %2d 词 / 交集 %2d" % (sk, n_local, n_coze, inter))
        if n_local and n_coze and inter == 0:
            problems.append("%s: 关键词集合零交集" % sk)

    if not args.quiet:
        print("-" * 66)
        if problems:
            print("  结论: ⚠️ 检出 %d 处差异（本脚本只检测，不自动统一）" % len(problems))
            for p in problems:
                print("    - %s" % p)
            print("\n  说明: 本地规则只用于 orchestrate.py 的**高置信预取**；")
            print("        服务端 tool_router_node 才是 need_tool 的权威判定。")
            print("        差异不必然是故障，但需人工确认是否要收敛为单一真源。")
        else:
            print("  结论: ✅ 未检出显著差异")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
