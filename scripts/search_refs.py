#!/usr/bin/env python3
"""Search distilled Markdown references with regex terms.

Upgraded 2026-08-05 (knowledge split):
- default --context 3 (hit + context lines), returns content directly so the
  agent usually does NOT need a second Read
- --max-len truncates over-long lines (some ref lines are 2k+ chars)
- --files filters to a comma-separated subset of ref-*.md
- prints hit count summary to stderr for latency debugging
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


def load_aliases():
    """Load bilingual term-alias table; return list of synonym-groups.

    Degrades silently to [] when the file is missing or malformed, so search
    still works as before (pure regex, no expansion).
    """
    path = Path(__file__).resolve().parent.parent / "knowledge" / "term_aliases.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(data, dict):
        aliases = data.get("aliases")
        return aliases if isinstance(aliases, list) else []
    return data if isinstance(data, list) else []


def expand_pattern(user_pattern, aliases):
    """Expand user pattern with bilingual synonyms from the alias table.

    If any term of a synonym-group appears (case-insensitive substring) in the
    user pattern, the whole group is appended to the regex via `|`. The original
    pattern is preserved inside a non-capturing group, so complex regexes still
    work. Returns (expanded_pattern, fired_group_count).
    """
    if not aliases:
        return user_pattern, 0
    term2groups = defaultdict(set)
    for grp in aliases:
        s = frozenset(grp)
        for t in grp:
            term2groups[t.lower()].add(s)
    extra = set()
    fired = 0
    for term, grps in term2groups.items():
        if not term:
            continue
        if re.search(re.escape(term), user_pattern, re.IGNORECASE):
            fired += 1
            for g in grps:
                extra.update(g)
    if extra:
        joined = "|".join(sorted(extra, key=len, reverse=True))
        return f"(?:{user_pattern})|(?:{joined})", fired
    return user_pattern, 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Search skill reference notes (split knowledge)")
    parser.add_argument("pattern", help="Regex, for example: 估计目标|伴发事件 / estimand|intercurrent event")
    parser.add_argument("--context", type=int, default=3, help="Context lines before/after each hit (default 3)")
    parser.add_argument("--max-len", type=int, default=600, help="Truncate output lines longer than N chars (default 600)")
    parser.add_argument("--files", default="", help="Comma-separated subset of ref-*.md filenames to search (default: all)")
    args = parser.parse_args()

    aliases = load_aliases()
    try:
        expanded, fired = expand_pattern(args.pattern, aliases)
    except re.error:
        expanded, fired = args.pattern, 0
    try:
        expression = re.compile(expanded, re.IGNORECASE)
    except re.error as exc:
        parser.error(f"invalid regex: {exc}")

    if aliases:
        sys.stderr.write(
            f"[ct-advisor] alias table: {len(aliases)} groups; {fired} fired / 别名表: {len(aliases)} 组; 本次命中 {fired} 组; "
            f"pattern len {len(expanded)} / 检索式长度 {len(expanded)} chars\n"
        )

    reference_dir = Path(__file__).resolve().parent.parent / "knowledge"
    wanted = {f.strip() for f in args.files.split(",") if f.strip()} if args.files else None

    files = sorted(reference_dir.glob("ref-*.md"))
    if wanted:
        files = [p for p in files if p.name in wanted]

    total_hits = 0
    matched = False
    for path in files:
        lines = path.read_text(encoding="utf-8").splitlines()
        hit_indexes = [i for i, line in enumerate(lines) if expression.search(line)]
        if not hit_indexes:
            continue
        matched = True
        total_hits += len(hit_indexes)
        print(f"\n## {path.name} ({len(hit_indexes)} hits)")
        shown: set[int] = set()
        for index in hit_indexes:
            start = max(0, index - args.context)
            end = min(len(lines), index + args.context + 1)
            for current in range(start, end):
                if current in shown:
                    continue
                shown.add(current)
                marker = ">" if current == index else " "
                line = lines[current]
                if len(line) > args.max_len:
                    line = line[:args.max_len] + " …[truncated]"
                print(f"{marker}{current + 1}: {line}")
    if not matched:
        print(
            f"no match for pattern {args.pattern!r} in {reference_dir.name}/ref-*.md "
            f"(searched {len(files)} files)"
        )
        print(
            "[ct-advisor] no match → do NOT brute-force synonym swaps (historical: 14 searches, 12 empty, ~2 min wasted) / 搜索无命中 → 禁止换词穷举（历史实测 14 次搜索 12 次无结果，浪费 ~2 分钟）"
        )
        print(
            "[ct-advisor] correct fallback: ① retry once with a semantically-equivalent term; ② still empty → Read reference-index.md to locate the target file → Read the target file (≤60 lines) / 正确退避：① 换语义等价词重试 1 次；② 仍无命中 → Read reference-index.md 定位目标文件 → Read 目标文件（≤60行）"
        )
    else:
        print(f"\n[{total_hits} hits in {len(files)} files]")
    return 0 if matched else 1


if __name__ == "__main__":
    sys.exit(main())
