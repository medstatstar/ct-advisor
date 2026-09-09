#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ct-advisor — 兄弟技能 CLI 契约测试（F4, 2026-09-03）

动机：orchestrate / route_tool 自测与 test_seven_flows.py 全程用 mock 桩
（`_pf` 返回假 status/result），**从不真正 subprocess 调用兄弟技能**。而 PREVIEW/KW-GATE
守卫正是踩坑后补的，未来某兄弟技能改默认 CLI（如重命名 --margin、删 --yes、改 --run
语义）会**静默再破**执行链路——mock 桩完全侦测不到。

本测试（真实调用，零网络）：
  - 对 tool_mapping.json 中每个自动执行技能，解析 cmd + args（{SKILLS_DIR} 展开），
    先校验脚本文件存在 + 路径落在 SKILLS_DIR 内（防 ../ 逃逸）；
  - 真实 subprocess 跑 `<cmd> <args> --help`（argparse 解析即退出，不联网 / 不触发 coze）；
  - 断言 rc == 0；
  - 断言 tool_mapping 声明的每个 flag（params / extra_args / conditional_args）都出现在
    兄弟技能 --help 文本里——即契约漂移（兄弟改了 CLI 没同步映射表）会被立刻抓出。

运行：
  python scripts/test_sibling_contract.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # scripts/
SKILL = HERE.parent                             # ct-advisor/
MAPPING_PATH = HERE / "tool_mapping.json"
SKILLS_DIR = Path(os.environ.get(
    "CT_SKILLS_DIR",
    str(Path.home() / ".workbuddy" / "skills")))

_FLAG_RE = re.compile(r"--[a-zA-Z0-9][a-zA-Z0-9_-]*")


def _interpreter() -> str:
    """兄弟技能执行用解释器。

    按用户环境规则（Python 必须用 Anaconda ``C:\\Tools\\anaconda3\\python.exe``，
    不用 WorkBuddy 自带 managed 3.13.12），优先 Anaconda；缺失时回退到运行本测试的
    解释器。ct-safety / ct-literature 在模块顶层 ``import xlsxwriter``，managed 环境
    未预装会导致 ``--help`` 即 rc=1——用 Anaconda 才能真实跑通契约检查。
    """
    cand = r"C:\Tools\anaconda3\python.exe"
    if os.path.isfile(cand):
        return cand
    return sys.executable


def _load_mapping() -> dict:
    return json.loads(MAPPING_PATH.read_text(encoding="utf-8"))


def _declared_flags(cfg: dict) -> list:
    """汇集映射表声明的全部 CLI flag（params + extra_args + conditional_args）。"""
    flags: list = []
    for spec in (cfg.get("params") or {}).values():
        f = spec.get("flag")
        if f and f.startswith("--"):
            flags.append(f)
    for a in (cfg.get("extra_args") or []):
        if a.startswith("--"):
            flags.append(a)
    for rule in (cfg.get("conditional_args") or []):
        for a in rule.get("args", []):
            if isinstance(a, str) and a.startswith("--"):
                flags.append(a)
    # 去重保序
    seen, out = set(), []
    for f in flags:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def _run_help(cmd: list, timeout: int = 30) -> tuple:
    """真实跑 --help；返回 (rc, combined_stdout_stderr)。"""
    try:
        proc = subprocess.run(
            cmd + ["--help"],
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        return proc.returncode, (proc.stdout or "") + "\n" + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "[timeout] --help 超时"
    except FileNotFoundError as e:
        return -2, f"[notfound] {e}"


def run() -> int:
    print("ct-advisor 兄弟技能 CLI 契约测试（真实 subprocess，零网络）")
    print("=" * 78)
    print(f"  SKILLS_DIR = {SKILLS_DIR}")
    mapping = _load_mapping()
    skills = mapping.get("skills", {})
    print(f"  自动执行技能数 = {len(skills)}")
    interp = _interpreter()
    print(f"  兄弟技能解释器 = {interp}")
    print("=" * 78)

    ok = 0
    for tool, cfg in skills.items():
        problems: list = []
        # 1) 解析 cmd + args，校验脚本存在 + 路径白名单
        raw_args = [a.replace("{SKILLS_DIR}", str(SKILLS_DIR)) for a in cfg.get("args", [])]
        script = Path(raw_args[-1]) if raw_args else None
        if script is None or not script.is_file():
            problems.append(f"脚本不存在: {script}")
        else:
            try:
                script.resolve().relative_to(SKILLS_DIR.resolve())
            except ValueError:
                problems.append(f"脚本路径越界（非 SKILLS_DIR 内）: {script}")
        # 2) 真实跑 --help（用 _interpreter()：Anaconda 优先，含 xlsxwriter 等兄弟依赖）
        help_rc, help_txt = _run_help([interp] + raw_args)
        if help_rc != 0:
            problems.append(f"--help rc={help_rc}（argparse 解析失败 / 导入错误）")
        # 3) 契约 flag 检查
        help_flags = set(_FLAG_RE.findall(help_txt))
        declared = _declared_flags(cfg)
        missing = [f for f in declared if f not in help_flags]
        if missing:
            problems.append("契约 flag 缺失: " + ", ".join(missing))
        # 4) engine 字段存在性（F5 要求）
        if "engine" not in cfg:
            problems.append("缺 engine 字段（local/coze）")

        passed = not problems
        if passed:
            ok += 1
        mark = "✓" if passed else "✗"
        print(f"\n  {mark} {tool}  (engine={cfg.get('engine', '?')}, 声明 flag={len(declared)})")
        if passed:
            print(f"      --help rc=0，全部 {len(declared)} 个契约 flag 命中")
        else:
            for p in problems:
                print(f"      ✗ {p}")

    total = len(skills)
    print("\n" + "=" * 78)
    print(f"  契约测试通过: {ok}/{total} = {ok / total * 100:.1f}%" if total else "  无技能")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(run())
