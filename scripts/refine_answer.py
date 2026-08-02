#!/usr/bin/env python3
"""ct-advisor 答案精修入口（agent 调用）。

读取 5 变量（JSON，来自文件参数或 stdin）：
  category, original_question, organized_problems, draft_answer, difficulty
调用 build_refiner().refine() 得到最终答案，打印到 stdout。

健壮性：任何异常都兜底打印 draft_answer 并 exit 0，保证 agent 永远拿到可用答案、
不会因脚本崩溃而中断对话。默认 refiner.mode=local 时直接回传 draft_answer（零网络）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from adapters import build_refiner, RefineRequest


def _extract_draft(raw: str) -> str:
    """尽力从原始输入里取出 draft_answer，供解析失败时的兜底。"""
    try:
        return json.loads(raw).get("draft_answer", "") or ""
    except Exception:
        m = re.search(r'"draft_answer"\s*:\s*"((?:[^"\\]|\\.)*)"', raw, re.S)
        return m.group(1) if m else ""


def main() -> None:
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        raw = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()

    draft = _extract_draft(raw)
    try:
        obj = json.loads(raw)
        req = RefineRequest(
            category=str(obj.get("category", "")),
            original_question=str(obj.get("original_question", "")),
            organized_problems=obj.get("organized_problems", []) or [],
            draft_answer=str(obj.get("draft_answer", "")),
            difficulty=str(obj.get("difficulty", "")),
        )
    except Exception:
        sys.stdout.write(draft)
        sys.exit(0)

    try:
        final = build_refiner().refine(req)
    except Exception:
        final = draft
    sys.stdout.write(final or draft)
    sys.exit(0)


if __name__ == "__main__":
    main()
