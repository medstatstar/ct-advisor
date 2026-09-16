#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_deps.py -- probe which sibling ct-series skills are installed.

ct-advisor routes data_intel asks to these skills via the Skill tool but does NOT
re-implement their logic. If one is missing, the agent degrades gracefully (see
`knowledge/system_prompt.md` "Routing & total entry"). This script is a LOCAL-ONLY
capability probe: it scans known skill roots for each dependency slug and reports
installed / missing, with an install hint.

It NEVER installs anything and makes NO network calls.

Sibling list + A/B tier + install address all come from the SINGLE source of truth
`scripts/tool_mapping.json` → `tiers.registry` (2026-09-10). Do NOT hard-code a
second tier table here: the previous hard-coded copy mislabelled ct-registry /
ct-safety / ct-literature as tier B and ct-samplesize as tier A, contradicting
ct-base §11 (the authoritative axis) in three places.

Tier semantics (ct-base §11 + §13.1):
  A   = non-confidential input                        -> installable IF published
  B   = confidential input, NOT publicly released     -> nothing to install
  meta= base/governance layer, never published        -> nothing to install

`published` is orthogonal to the tier and is judged by **SkillHub listing**, not by
GitHub: an empty GitHub placeholder repo still answers HTTP 200 (the ct-pipeline case).
Re-verify with `python adapters/probe_publication.py`. So tier-A entries split in two:
  A + published      -> installable (hint points at SkillHub, GitHub as fallback)
  A + NOT published  -> not installable; routing yields `unpublished_a`, not a clone URL

Usage:
  python3 scripts/check_deps.py                 # human-readable capability card
  python3 scripts/check_deps.py --json          # machine-readable dict
  python3 scripts/check_deps.py --project <dir> # also scan <dir>/.workbuddy/skills
"""

import json
import os
import sys
from pathlib import Path

# i18n: install_hint 按当前系统 locale 取 en/zh
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from i18n import is_chinese_os
_LANG = "zh" if is_chinese_os() else "en"
# 技能根目录（与 handle_need_tool.SKILLS_DIR 同一约定），仅用于拼安装命令提示
_SKILLS_DIR = os.environ.get("CT_SKILLS_DIR", str(Path.home() / ".workbuddy" / "skills"))

MAPPING_PATH = Path(_HERE) / "tool_mapping.json"


def load_registry() -> dict:
    """读 tool_mapping.json 的 tiers.registry（档位与发布状态的单一事实来源）。"""
    try:
        data = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return (data.get("tiers") or {}).get("registry") or {}


def known_deps() -> list:
    """从 tiers 注册表派生依赖清单（保持旧 KNOWN_DEPS 的元组形状以便调用方兼容）。

    返回 [(slug, tier, purpose, github, install_hint, published), ...]。
    仅 tier=A 且 published 的技能才是「可安装」的探测对象；B 档 / meta 一并列出但标记
    为不可安装（让用户看到全貌，而不是误以为「缺了就去装」）。
    """
    out = []
    for slug, e in load_registry().items():
        tier = e.get("tier", "B")
        published = bool(e.get("published"))
        github = e.get("github") or f"https://github.com/medstatstar/{slug}"
        purpose = e.get("purpose", "")
        if tier == "A" and published:
            # 2026-09-10 修正：安装命令统一走本技能自带的 install_sibling.py
            # （先核验 SkillHub 上架再下载解压）。此前此处给的是裸 `skillhub install`
            # 与 `git clone` —— 两者实测都不可用，见 install_sibling.py 的模块说明。
            cmd = f"python adapters/install_sibling.py {slug} --dir {_SKILLS_DIR}"
            hint = {
                "en": f"Install (suggested - run by you or authorised): `{cmd}` "
                      f"(verifies the SkillHub listing before downloading)",
                "zh": f"建议安装：`{cmd}`（会先核验 SkillHub 上架状态再下载；"
                      f"默认只建议、由你执行或经你明确授权后代为执行）",
            }
        elif tier == "A":
            hint = {"en": "Tier A but NOT yet publicly released — not installable.",
                    "zh": "A 档但尚未对外发布——不属于可安装项（给出安装地址只会得到空仓库）。"}
        elif tier == "meta":
            hint = {"en": "Governance layer — never published, not installable.",
                    "zh": "元层（治理）——永不发布，不属于可安装项。"}
        else:
            hint = {"en": "Tier B (confidential input) — NOT publicly released, not installable.",
                    "zh": "B 档（输入涉密）——不对外发布，不属于可安装项。"}
        out.append((slug, tier, purpose, github, hint, published))
    return out


def _skill_roots(project=None):
    """Return candidate skill-root directories to scan (deduped, existing)."""
    roots = []
    # 1) user-level skills (ct-* are installed here)
    roots.append(Path.home() / ".workbuddy" / "skills")
    # 2) explicit project dir
    if project:
        p = Path(project)
        roots.append(p / ".workbuddy" / "skills")
        roots.append(p / "skills")
    # 3) env override
    if os.environ.get("CT_PROJECT_SKILLS"):
        roots.append(Path(os.environ["CT_PROJECT_SKILLS"]))
    seen = set()
    out = []
    for r in roots:
        try:
            rp = r.resolve()
        except Exception:
            continue
        if rp in seen:
            continue
        seen.add(rp)
        out.append(rp)
    return out


def check(roots, deps=None):
    deps = deps if deps is not None else known_deps()
    result = []
    for slug, tier, purpose, github, hint, published in deps:
        installable = (tier == "A" and published)
        found_in = None
        for root in roots:
            root = Path(root)  # tolerate string roots (e.g. direct check() calls)
            if (root / slug).is_dir():
                found_in = str(root / slug)
                break
        result.append({
            "slug": slug,
            "tier": tier,
            "published": published,
            "purpose": purpose,
            "github": github,
            "installable": installable,
            # 不可安装的技能（B 档 / meta / A 档未发布）不报 installed：
            # 它们压根不该出现在本地 skills 目录里，报 True/False 都会误导。
            "installed": (found_in is not None) if installable else None,
            "path": found_in,
            "install_hint": hint.get(_LANG, hint.get("en", "")),
        })
    return result


def render_human(report):
    print("ct-advisor · sibling skill capability card (local probe, installs nothing)")
    print("=" * 76)
    installable = [r for r in report if r["installable"]]
    installed = sum(1 for r in installable if r["installed"])
    for r in installable:
        mark = "OK  INSTALLED" if r["installed"] else "XX  MISSING"
        print("  [%s] %s  (tier %s, published)" % (mark, r["slug"], r["tier"]))
        print("           %s" % r["purpose"])
        if not r["installed"]:
            print("           GitHub: %s" % r["github"])
            print("           install: %s" % r["install_hint"])
        if r["path"]:
            print("           path: %s" % r["path"])
    print("-" * 76)
    print("  A 档（可安装）: %d/%d installed." % (installed, len(installable)))
    missing = [r["slug"] for r in installable if not r["installed"]]
    if missing:
        print("  Missing: %s" % ", ".join(missing))
        print("  A-tier missing skills: installation is SUGGESTED (never automatic) -")
        print("  run the command yourself or explicitly authorise it; it writes into the local")
        print("  skills dir and may trigger a security prompt (ct-base §5: never install silently);")
        print("  methodology knowledge")
        print("  (workflows A-J) is retrieved locally.")
    else:
        print("  All installable sibling skills present - full data_intel routing available.")

    # 不可安装项：只报数量与名单，避免用户误以为「缺了就去装」
    for tier, label in (("B", "B 档（输入涉密 · 不对外发布）"),
                        ("meta", "meta 元层（永不发布）")):
        group = [r["slug"] for r in report if r["tier"] == tier]
        if group:
            print("  %s: %d 个 —— %s" % (label, len(group), ", ".join(group)))
            print("     （无可安装项；如需深度分析请在其本地运行环境中执行，或联系作者定制）")
    notpub = [r["slug"] for r in report if r["tier"] == "A" and not r["published"]]
    if notpub:
        print("  A 档但尚未发布: %s" % ", ".join(notpub))
        print("     （当前不可安装 → 路由命中时走 unpublished_a：本地作答 + 标注未取数）")
    return report


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="Probe installed ct-advisor sibling skills")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    p.add_argument("--project", help="also scan a project .workbuddy/skills dir")
    args = p.parse_args(argv)
    roots = _skill_roots(args.project)
    deps = known_deps()
    report = check(roots, deps)
    if args.json:
        print(json.dumps(
            {"roots": [str(r) for r in roots], "deps": report},
            ensure_ascii=False, indent=2))
    else:
        render_human(report)
    # Always exit 0: this is a probe; missing skills are reported in the output,
    # not via the process exit code (so the agent never sees a false "failure").
    return 0


if __name__ == "__main__":
    sys.exit(main())
