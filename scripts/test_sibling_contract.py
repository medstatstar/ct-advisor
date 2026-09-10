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


def _path_under(raw: str) -> bool:
    """判断技能脚本路径是否落在 SKILLS_DIR 之内（兼容软链接安装）。

    2026-09-10 修复：本机 / 常见部署把 `~/.workbuddy/skills/<slug>` 做成软链接指向
    另一处（如网络盘 \\\\filesrv\\...\\skills\\<slug>）。此时 `script.resolve()` 落到**真实路径**，
    与 `SKILLS_DIR.resolve()` 不同根 → 旧实现一律误报「脚本路径越界」，契约测试直接 0/4。
    改为两级判定：① 解析后在内 → 通过；② 否则按**未解析**路径判（须在 SKILLS_DIR 下
    且不含 `..`，保留原防逃逸语义）→ 通过。两者皆不满足才算越界。
    """
    raw_path = Path(raw)
    try:
        raw_path.resolve().relative_to(SKILLS_DIR.resolve())
        return True
    except ValueError:
        pass
    try:
        raw_path.absolute().relative_to(Path(str(SKILLS_DIR)).absolute())
        return ".." not in raw_path.parts
    except ValueError:
        return False


def run_tier_gate() -> tuple:
    """A/B 档门控断言（2026-09-10）。

    覆盖用户要求的两条基本规则：
      A 类：先检查是否安装 → 未装则**建议安装**（默认绝不自动安装；安装会写入本地技能目录、
      可能触发本机安全提示）→ 用户**明确授权**后代为安装再执行 / 拒绝则自身能力作答；
      B 类：直接提示「需调 B 档技能但不对外发布」→ 用自身能力作答。
    全部走真实 subprocess（CLI + CT_SKILLS_DIR 隔离），零网络。
    """
    import tempfile
    sys.path.insert(0, str(HERE))
    from handle_need_tool import _load_mapping, _resolve_tier, _skill_installed

    checks: list = []

    def _run(card: dict, skills_dir: str | None = None) -> dict:
        env = dict(os.environ)
        if skills_dir:
            env["CT_SKILLS_DIR"] = skills_dir
        proc = subprocess.run(
            [_interpreter(), str(HERE / "handle_need_tool.py"),
             "--card", json.dumps(card, ensure_ascii=False)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60, env=env,
        )
        return json.loads(proc.stdout)

    empty = tempfile.mkdtemp(prefix="ct_empty_skills_")
    mapping = _load_mapping()

    # 1) B 档技能 → unreleased_b（不再是「未映射」硬错）
    r = _run({"need_tool": "ct-protocol", "params": {}, "draft_answer": "d", "original_question": "审查方案"})
    checks.append(("B 档 ct-protocol → unreleased_b",
                   r.get("status") == "unreleased_b" and "不对外发布" in json.dumps(r, ensure_ascii=False)))

    # 2) 未登记技能 → 按 B 档保守处理（不硬错卡死）
    r = _run({"need_tool": "ct-nope-xyz", "params": {}, "draft_answer": "d", "original_question": "q"})
    ok = r.get("status") == "unreleased_b"
    if isinstance(r.get("result"), dict):
        ok = ok and r["result"].get("registered") is False
    checks.append(("未登记技能 → unreleased_b（保守按 B 档）", bool(ok)))

    # 3) A 档未安装 → install_required（含 github / install_hint）
    r = _run({"need_tool": "ct-registry", "params": {"cond": "PD-1"},
              "draft_answer": "d", "original_question": "PD-1 三期试验"}, skills_dir=empty)
    res = r.get("result") if isinstance(r.get("result"), dict) else {}
    checks.append(("A 档未安装 → install_required",
                   r.get("status") == "install_required"
                   and res.get("github", "").startswith("https://github.com/")
                   and bool(res.get("install_hint"))))

    # 3b) 安装通道可用性（2026-09-10 修）：install_command 必须指向自带的
    #     install_sibling.py，且是正斜杠非 UNC 路径、显式带 --dir。
    #     此前该字段给的是裸 `skillhub install <slug>`，实测三重不可用：
    #       · PATH 中无 skillhub 命令；
    #       · 本机 ~/.skillhub 的是精简版 CLI，下载端点走内网 LB 返回非 zip；
    #       · 完整版 CLI 在网络盘，UNC 路径经 bash 传递被二次拼接而打不开。
    cmd = res.get("install_command") or ""
    checks.append(("install_required → 安装命令指向 install_sibling.py（非裸 skillhub）",
                   "install_sibling.py" in cmd
                   and "skillhub install" not in cmd))
    checks.append(("install_required → 安装命令为绝对路径 + 显式 --dir（含正确技能目录）",
                   cmd.startswith('"') and '--dir' in cmd
                   and Path(empty).as_posix() in cmd))
    checks.append(("install_required → 安装命令不含 UNC 路径（// 开头会被 shell 改写）",
                   "//" not in cmd))
    from handle_need_tool import _helper_path
    checks.append(("install_required → 命令引用的安装器文件确实存在",
                   _helper_path() is not None))

    # 3c) 安装姿态（2026-09-10 第二轮，用户要求）：**默认只「建议安装」，不得自动安装**
    #     —— 安装会从 SkillHub 下载技能包并写入本地技能目录，可能触发本机安全提示。
    #     仅当用户给出**明确授权**（install_consent=approved）才转 authorized（可代办执行）；
    #     含糊 / 未知取值一律保持 suggest。
    checks.append(("install_required 默认姿态 = 建议安装（install_mode=suggest，未授权）",
                   res.get("install_mode") == "suggest"
                   and res.get("install_authorized") is False))
    _hint = res.get("hint") or ""
    checks.append(("suggest 指引含「只建议」+「不得代为执行」+「明确授权」",
                   "只建议" in _hint and "不得代为执行" in _hint and "授权" in _hint))
    checks.append(("suggest 指引不含「执行 install_command」式自动安装指令",
                   "执行 install_command" not in _hint))
    checks.append(("suggest 提示安装会写入本地目录 / 可能触发安全提示",
                   "安全提示" in (res.get("install_note") or "")))
    for vague in ("", "maybe", "later", "ask-me-tomorrow", "sure?"):
        r = _run({"need_tool": "ct-registry", "params": {"cond": "PD-1"},
                  "draft_answer": "d", "original_question": "q",
                  "install_consent": vague}, skills_dir=empty)
        rr = r.get("result") if isinstance(r.get("result"), dict) else {}
        checks.append((f"含糊表态 install_consent={vague!r} → 仍为 suggest（不升级为已授权）",
                       r.get("status") == "install_required"
                       and rr.get("install_mode") == "suggest"))

    # 3d) 用户**明确授权** → install_mode=authorized（此时才允许 agent 代办执行）
    r_auth = _run({"need_tool": "ct-registry", "params": {"cond": "PD-1"},
                   "draft_answer": "d", "original_question": "q",
                   "install_consent": "approved"}, skills_dir=empty)
    res_auth = r_auth.get("result") if isinstance(r_auth.get("result"), dict) else {}
    checks.append(("A 档未安装 + 用户明确授权 → install_mode=authorized",
                   r_auth.get("status") == "install_required"
                   and res_auth.get("install_mode") == "authorized"
                   and res_auth.get("install_authorized") is True))
    checks.append(("authorized 指引允许执行安装命令（含执行 install_command）",
                   "执行 install_command" in (res_auth.get("hint") or "")))

    # 3e) 缝合层渲染：suggest 与 authorized 的**措辞必须可区分**（面向 agent 的指引）
    sys.path.insert(0, str(HERE))
    import refine_answer
    zh_s = refine_answer._merge_answer(
        "COZE", {"tool": "ct-registry", "status": "install_required", "result": res}, lang="zh-CN")
    en_s = refine_answer._merge_answer(
        "COZE", {"tool": "ct-registry", "status": "install_required", "result": res}, lang="en")
    zh_a = refine_answer._merge_answer(
        "COZE", {"tool": "ct-registry", "status": "install_required", "result": res_auth}, lang="zh-CN")
    _cmd = res.get("install_command") or "\x00"
    checks.append(("渲染(suggest·zh)：标注建议安装、命令原样给出、「只建议、不执行」",
                   "建议安装" in zh_s and "只建议、不执行" in zh_s and _cmd in zh_s))
    checks.append(("渲染(suggest·zh)：含安全提示与「授权安装」回执路径",
                   "安全提示" in zh_s and "install_consent" in zh_s))
    checks.append(("渲染(suggest·en)：'Suggest only' / 'do not execute' 齐备",
                   "Suggest only" in en_s and "do not execute" in en_s))
    checks.append(("渲染(authorized·zh)：改为「已明确授权」并允许执行命令",
                   "已明确授权" in zh_a and "只建议、不执行" not in zh_a))

    # 4) A 档未安装 + 用户拒绝 → local_fallback（自身能力作答）
    r = _run({"need_tool": "ct-registry", "params": {"cond": "PD-1"},
              "draft_answer": "d", "original_question": "PD-1 三期试验",
              "install_consent": "declined"}, skills_dir=empty)
    checks.append(("A 档拒绝安装 → local_fallback", r.get("status") == "local_fallback"))

    # 4b) A 档「已登记但尚未发布」（ct-pipeline，2026-09-10 用户确认未发布）→ unpublished_a
    #     🔴 不得落到「未在 tool_mapping 中找到技能映射」硬错，也不得给出安装地址
    #     （SkillHub 未上架 / GitHub 仅空占位仓库，装了也是空目录）。
    r = _run({"need_tool": "ct-pipeline", "params": {},
              "draft_answer": "d", "original_question": "PD-1 竞品格局"})
    res = r.get("result") if isinstance(r.get("result"), dict) else {}
    checks.append(("A 档未发布 ct-pipeline → unpublished_a（非硬错、不给安装地址）",
                   r.get("status") == "unpublished_a"
                   and res.get("published") is False
                   and "install_hint" not in res
                   and "未在 tool_mapping" not in json.dumps(r, ensure_ascii=False)))

    # 4c) 同上，ct-synthdata（库内夹具，同样未上架）→ 同一分支
    r = _run({"need_tool": "ct-synthdata", "params": {},
              "draft_answer": "d", "original_question": "造一份测试数据"})
    checks.append(("A 档未发布 ct-synthdata → unpublished_a",
                   r.get("status") == "unpublished_a"))

    # 5) A 档已安装 → 不得误判为 install_required / unreleased_b（探测函数直测，不真跑联网技能）
    reg_cfg = mapping["skills"]["ct-registry"]
    checks.append(("A 档已安装 → 探测为 True（不误报待安装）", _skill_installed(reg_cfg) is True))

    # 6) A 档 + referral → referral（不被档位门吞掉）
    r = _run({"need_tool": "meta-analysis", "params": {}, "draft_answer": "d", "original_question": "做个 meta"})
    checks.append(("A 档 referral-only → referral", r.get("status") == "referral"))

    # 7) 注册表自洽：自动执行技能必须全为 A 档；B 档一律 published=false
    auto = mapping.get("skills", {}).keys()
    ok = all(_resolve_tier(mapping, t)["tier"] == "A" for t in auto)
    checks.append(("注册表自洽：自动执行技能全为 A 档", ok))
    ok = all(not v.get("published") for k, v in (mapping.get("tiers", {}).get("registry") or {}).items()
             if v.get("tier") == "B")
    checks.append(("注册表自洽：B 档一律 published=false", ok))
    # 7b) 注册表自洽：tier 与 published 正交——A 档可未发布，但未发布者必须**不**在
    #     自动执行表里（否则 unpublished_a 与正常执行冲突）；已发布者必须有 github 地址
    reg = mapping.get("tiers", {}).get("registry") or {}
    bad = [k for k, v in reg.items()
           if v.get("tier") == "A" and v.get("published") and not v.get("github")]
    checks.append(("注册表自洽：已发布的 A 档均带 github 地址", not bad))
    unpub = [k for k, v in reg.items() if v.get("tier") == "A" and not v.get("published")]
    checks.append(("注册表自洽：存在未发布 A 档（ct-pipeline），且确为 false",
                   "ct-pipeline" in unpub))

    # 8) check_deps 档位标注（旧版曾把 ct-registry 误标 tier B）
    sys.path.insert(0, str(HERE))
    import check_deps
    deps = {d[0]: d[1] for d in check_deps.known_deps()}
    checks.append(("check_deps 档位正确（ct-registry/ct-safety/ct-literature = A）",
                   deps.get("ct-registry") == "A" and deps.get("ct-safety") == "A"
                   and deps.get("ct-literature") == "A" and deps.get("ct-protocol") == "B"))

    return checks


def run_install_helper() -> tuple:
    """install_sibling.py 的**离线**分支断言（2026-09-10）。

    只覆盖不触网的路径（拒绝类判定排在核验/下载之前），故本函数仍是零网络的：
      · 非法 slug（含 .. 或路径分隔符）→ 拒装，退出码 2（防目录穿越）；
      · 目标目录已存在且未加 --force → 拒装，退出码 4（不覆盖既有安装）；
      · 拒绝分支**必须早于**网络核验 —— 用「不存在的 slug + 已存在目录」验证：
        若先联网，该用例会因网络失败而超时/报错，而非稳定返回 4。
    联网路径（核验上架 → 下载解压）由 e2e 手工验证，不进单元测试。
    """
    import tempfile
    helper = HERE / "install_sibling.py"
    interp = _interpreter()
    checks: list = []

    if not helper.is_file():
        checks.append(("install_sibling.py 存在", False))
        return checks
    checks.append(("install_sibling.py 存在", True))

    def _run(args: list, env_extra: dict | None = None) -> tuple:
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
        p = subprocess.run([interp, str(helper)] + args,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60, env=env)
        return p.returncode, (p.stdout or "") + (p.stderr or "")

    # 1) 非法 slug → 2（目录穿越防护）
    for bad in ("../evil", "a/b", "..", ".hidden"):
        rc, out = _run([bad, "--dir", tempfile.mkdtemp(prefix="ct_inst_")])
        checks.append((f"非法 slug {bad!r} → 拒装 (rc=2)", rc == 2 and "非法 slug" in out))

    # 2) 目标已存在且无 --force → 4，且**不触网**（用一个必然查不到的 slug；
    #    若实现把联网核验放在前面，这里会返回 3/5 而非 4）
    d = tempfile.mkdtemp(prefix="ct_inst_")
    (Path(d) / "ct-zzz").mkdir()
    rc, out = _run(["ct-zzz", "--dir", d])
    checks.append(("已存在目标且无 --force → 拒装 (rc=4，且早于联网核验)",
                   rc == 4 and "已存在" in out))

    # 3) --dry-run 与 --help 的离线可用性（--help 不触网）
    rc, out = _run(["--help"])
    checks.append(("--help 可解析（rc=0，argparse 正常）", rc == 0 and "--dry-run" in out))

    return checks


def render_tier_gate(checks: list) -> int:
    print("\n" + "=" * 78)
    print("  A/B 档门控断言（2026-09-10）")
    print("=" * 78)
    ok = 0
    for name, passed in checks:
        mark = "✓" if passed else "✗"
        if passed:
            ok += 1
        print(f"  {mark} {name}")
    print("-" * 78)
    print(f"  档位门控通过: {ok}/{len(checks)}" + ("" if not checks else f" = {ok / len(checks) * 100:.1f}%"))
    return ok, len(checks)


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
    skipped = 0
    for tool, cfg in skills.items():
        problems: list = []
        # 1) 解析 cmd + args，校验脚本存在 + 路径白名单
        raw_args = [a.replace("{SKILLS_DIR}", str(SKILLS_DIR)) for a in cfg.get("args", [])]
        script = Path(raw_args[-1]) if raw_args else None
        if script is None or not script.is_file():
            # 未安装 = 合法状态（2026-09-10 A/B 档门控：A 档缺失会走 install_required），
            # 不是契约漂移，故 SKIP 而非 FAIL，避免半装环境下测试恒红。
            skipped += 1
            print(f"\n  ⊘ {tool}  (未安装 → SKIP；契约检查待安装后生效)")
            continue
        if not _path_under(raw_args[-1]):
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

    checked = len(skills) - skipped
    print("\n" + "=" * 78)
    if checked:
        print(f"  契约测试通过: {ok}/{checked} = {ok / checked * 100:.1f}%"
              + (f"（另 {skipped} 个未安装，SKIP）" if skipped else ""))
    else:
        print(f"  无已安装的自动执行技能可检（{skipped} 个未安装，全部 SKIP）")

    gate_ok, gate_total = render_tier_gate(run_tier_gate())

    # 安装器离线分支（2026-09-10）：让「同意 → 安装」这一步有回归保护
    print("\n" + "=" * 78)
    print("  install_sibling.py 离线分支断言（2026-09-10）")
    print("=" * 78)
    helper_checks = run_install_helper()
    h_ok = 0
    for name, passed in helper_checks:
        print(f"  {'✓' if passed else '✗'} {name}")
        if passed:
            h_ok += 1
    print("-" * 78)
    print(f"  安装器断言通过: {h_ok}/{len(helper_checks)}")

    all_ok = (ok == checked) and (gate_ok == gate_total) and (h_ok == len(helper_checks))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(run())
