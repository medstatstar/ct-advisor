#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_deps.py -- probe which sibling ct-series data/compute skills are installed.

ct-advisor routes data_intel asks to these skills via the Skill tool but does NOT
re-implement their logic. If one is missing, the agent degrades gracefully (see
`knowledge/system_prompt.md` "Routing & total entry"). This script is a LOCAL-ONLY
capability probe: it scans known skill roots for each dependency slug and reports
installed / missing, with an install hint.

It NEVER installs anything and makes NO network calls.

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

# (slug, tier, purpose, github_repo, install_hint)
# install_hint 为双语字典 {en, zh}；缺失时按当前 locale 给出 GitHub 安装地址（repo URL + 克隆命令）。
KNOWN_DEPS = [
    ("ct-registry", "B",
     "Trial-registry landscape (CT.gov / CDE / WHO ICTRP / EU-CTR / ChiCTR / ISRCTN / DRKS)",
     "https://github.com/medstatstar/ct-registry",
     {"en": "Install: https://github.com/medstatstar/ct-registry  |  or `git clone https://github.com/medstatstar/ct-registry ~/.workbuddy/skills/ct-registry`",
      "zh": "GitHub 安装地址: https://github.com/medstatstar/ct-registry ｜ 或 `git clone https://github.com/medstatstar/ct-registry ~/.workbuddy/skills/ct-registry`"}),
    ("ct-safety", "B",
     "Safety signals (FAERS PRR / ROR / IC)",
     "https://github.com/medstatstar/ct-safety",
     {"en": "Install: https://github.com/medstatstar/ct-safety  |  or `git clone https://github.com/medstatstar/ct-safety ~/.workbuddy/skills/ct-safety`",
      "zh": "GitHub 安装地址: https://github.com/medstatstar/ct-safety ｜ 或 `git clone https://github.com/medstatstar/ct-safety ~/.workbuddy/skills/ct-safety`"}),
    ("ct-literature", "B",
     "Published literature (OpenAlex / Europe PMC / Semantic Scholar)",
     "https://github.com/medstatstar/ct-literature",
     {"en": "Install: https://github.com/medstatstar/ct-literature  |  or `git clone https://github.com/medstatstar/ct-literature ~/.workbuddy/skills/ct-literature`",
      "zh": "GitHub 安装地址: https://github.com/medstatstar/ct-literature ｜ 或 `git clone https://github.com/medstatstar/ct-literature ~/.workbuddy/skills/ct-literature`"}),
    ("ct-samplesize", "A",
     "Sample-size & power computation (handoff from workflow C)",
     "https://github.com/medstatstar/ct-samplesize",
     {"en": "Install: https://github.com/medstatstar/ct-samplesize  |  or `git clone https://github.com/medstatstar/ct-samplesize ~/.workbuddy/skills/ct-samplesize`",
      "zh": "GitHub 安装地址: https://github.com/medstatstar/ct-samplesize ｜ 或 `git clone https://github.com/medstatstar/ct-samplesize ~/.workbuddy/skills/ct-samplesize`"}),
]


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


def check(roots):
    result = []
    for slug, tier, purpose, github, hint in KNOWN_DEPS:
        found_in = None
        for root in roots:
            root = Path(root)  # tolerate string roots (e.g. direct check() calls)
            if (root / slug).is_dir():
                found_in = str(root / slug)
                break
        result.append({
            "slug": slug,
            "tier": tier,
            "purpose": purpose,
            "github": github,
            "installed": found_in is not None,
            "path": found_in,
            "install_hint": hint.get(_LANG, hint.get("en", "")),
        })
    return result


def render_human(report):
    print("ct-advisor · sibling skill capability card (local probe, installs nothing)")
    print("=" * 72)
    installed = sum(1 for r in report if r["installed"])
    for r in report:
        mark = "OK  INSTALLED" if r["installed"] else "XX  MISSING"
        print("  [%s] %s  (tier %s)" % (mark, r["slug"], r["tier"]))
        print("           %s" % r["purpose"])
        if not r["installed"]:
            print("           GitHub: %s" % r["github"])
            print("           install: %s" % r["install_hint"])
    print("-" * 72)
    print("  %d/%d sibling skills installed." % (installed, len(report)))
    missing = [r["slug"] for r in report if not r["installed"]]
    if missing:
        print("  Missing skills are needed ONLY for data_intel asks;")
        print("  methodology knowledge (workflows A-J) is retrieved locally.")
        print("  ct-advisor gives the methodology prep and labels output")
        print("  'data not retrieved' (see 'Routing & total entry').")
    else:
        print("  All sibling skills present - full data_intel routing available.")
    return report


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="Probe installed ct-advisor sibling skills")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    p.add_argument("--project", help="also scan a project .workbuddy/skills dir")
    args = p.parse_args(argv)
    roots = _skill_roots(args.project)
    report = check(roots)
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
