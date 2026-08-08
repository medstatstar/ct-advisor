#!/usr/bin/env python3
"""
update_reference_index.py — 从 knowledge/ 全部 ref-*.md 参考文件生成文件级路由索引 reference-index.md
使用时机：每次新增 / 更新任一 ref-* 文件后运行 `python scripts/update_reference_index.py`
（2026-08-05 重写：适配知识库拆分，扫描多文件 frontmatter 生成紧凑路由表）
"""

import os
import re
from datetime import datetime

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge")


def extract_fm(path):
    """从 frontmatter 提取 (file, topics, workflows)；superseded 占位文件返回 None"""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    fm = text.split("---", 2)[1]
    status = re.search(r"status:\s*(\S+)", fm)
    if status and status.group(1).startswith("superseded"):
        return None
    file = re.search(r"file:\s*(\S+)", fm)
    topics = re.search(r"topics:\s*(.*)", fm)
    wfs = re.search(r"serves_workflows:\s*(\[[^\]]*\])", fm)
    return (file.group(1) if file else os.path.basename(path),
            topics.group(1).strip() if topics else "—",
            wfs.group(1) if wfs else "")


def build():
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "---",
        "file: reference-index.md",
        f"version: {today}",
        "purpose: knowledge 文件级路由表（拆分后）——先查此表定位主题文件，再用 search_refs.py 定位行段",
        "auto_generated: true  # 由 scripts/update_reference_index.py 生成，手动修改会被覆盖",
        "---",
        "",
        "# Reference Index — 文件级路由表",
        "",
        "> **用法**：收到提问 → 按关键词匹配下表「覆盖主题」列 → 用 `python3 scripts/search_refs.py \"<关键词>\" --context 3` 定位行段，或 Read 目标文件（单次 ≤60 行）。",
        "> Contract content is embedded in this file (auto-generated header + manual sections below).",
        "",
    ]
    entries = {}
    for path in sorted(os.listdir(KNOWLEDGE_DIR)):
        if not (path.startswith("ref-") and path.endswith(".md")):
            continue
        info = extract_fm(os.path.join(KNOWLEDGE_DIR, path))
        if info:
            entries[path] = info

    for series, title in (
        ("ref-ops-", "## Clinical Operations 系列（ref-ops-*，执行层）"),
        ("ref-reg-", "## Regulatory & Statistical 系列（ref-reg-*，依据层）"),
    ):
        lines.append(title)
        lines.append("")
        lines.append("| 文件 | 覆盖主题（workflows） |")
        lines.append("|---|---|")
        for name in sorted(entries):
            if not name.startswith(series):
                continue
            _, topics, wfs = entries[name]
            lines.append(f"| `{name}` | {topics} {wfs} |")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("> **维护说明**：本索引由 `scripts/update_reference_index.py` 自动生成；每次更新任一 `ref-*` 文件后运行该脚本重建。")
    return "\n".join(lines) + "\n"


def main():
    content = build()
    out_path = os.path.join(KNOWLEDGE_DIR, "reference-index.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] reference-index.md 已更新 → {out_path} ({len(content.encode('utf-8')) // 1024} KB)")


if __name__ == "__main__":
    main()
