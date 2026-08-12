#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""memory_manager.py — ct-advisor 本地用户记忆机制（D 档）。

纯本地、零网络出域，仅依赖 Python 标准库（json / re / argparse / sys / pathlib）。
将用户的**稳定偏好 / 已确认决定 / 项目术语**写入本地记忆文件，供
``refine_answer.py --memory`` 注入 Coze 精校 prompt，实现跨会话记忆。

🔴 安全设计：
  - 记忆文件默认 ``~/.workbuddy/ct-advisor-memory.json``，**刻意避开**用户级
    ``~/.workbuddy/MEMORY.md``（避免与通用记忆机制冲突）。
  - **TTL（默认 90 天）**：超过 TTL 的条目在 list / load 时自动标记为过期，
    由 ``prune`` 清理；防止过时记忆污染答案。
  - **用户确认机制**：``add`` 在非交互（agent 调用）模式下必须显式传 ``--confirm``；
    交互模式下会二次确认。``clear`` 为破坏性操作，必须 ``--confirm``。
  - **零联网**：所有读写均在本地，符合 D 档数据安全要求。

调用方式：
  python scripts/memory_manager.py add --category pref --content "样本量默认 power=0.9" [--confirm]
  python scripts/memory_manager.py list [--show-expired]
  python scripts/memory_manager.py load [--as-prompt]     # 输出可注入上下文
  python scripts/memory_manager.py prune                   # 清理过期条目
  python scripts/memory_manager.py clear --confirm         # 清空（需确认）
  python scripts/memory_manager.py --self-test            # 最小内联自测

条目结构：
  {
    "id": "m_xxx",
    "category": "pref|decision|term|context",
    "content": "稳定偏好/已确认决定/项目术语",
    "created_at": "ISO-8601",
    "ttl_days": 90
  }
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

DEFAULT_TTL_DAYS = 90

CATEGORIES = ("pref", "decision", "term", "context")


def _default_path() -> Path:
    return Path(os.path.expanduser("~")) / ".workbuddy" / "ct-advisor-memory.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_store(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("entries"), list):
            return data["entries"]
    except Exception:
        pass
    return []


def _save_store(path: Path, entries: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"entries": entries}, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_expired(entry: Dict[str, Any], now: Optional[datetime] = None) -> bool:
    now = now or datetime.now(timezone.utc)
    ttl = entry.get("ttl_days", DEFAULT_TTL_DAYS)
    created = entry.get("created_at")
    if not created:
        return False
    try:
        ct = datetime.fromisoformat(created)
        if ct.tzinfo is None:
            ct = ct.replace(tzinfo=timezone.utc)
    except Exception:
        return False
    return (now - ct) > timedelta(days=ttl)


def add_entry(path: Path, category: str, content: str, ttl_days: int = DEFAULT_TTL_DAYS,
              confirm: bool = False) -> Dict[str, Any]:
    """新增一条记忆。返回新增条目 dict。"""
    category = (category or "context").strip().lower()
    if category not in CATEGORIES:
        category = "context"
    content = (content or "").strip()
    if not content:
        raise ValueError("content 不能为空")

    interactive = sys.stdin.isatty()
    if not confirm and not interactive:
        raise PermissionError(
            "非交互模式下 add 必须显式传 --confirm（避免 agent 静默写入记忆）"
        )
    if interactive and not confirm:
        try:
            ans = input(f"将写入记忆 [{category}]: {content}\n确认？(y/N) ").strip().lower()
            if ans not in ("y", "yes"):
                raise PermissionError("用户未确认，已取消")
        except (EOFError, OSError):
            raise PermissionError("无法交互确认，已取消")

    entry = {
        "id": "m_" + uuid.uuid4().hex[:10],
        "category": category,
        "content": content,
        "created_at": _now_iso(),
        "ttl_days": ttl_days,
    }
    entries = _load_store(path)
    entries.append(entry)
    _save_store(path, entries)
    return entry


def list_entries(path: Path, show_expired: bool = False) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    out = []
    for e in _load_store(path):
        exp = _is_expired(e, now)
        if exp and not show_expired:
            continue
        e = dict(e)
        e["_expired"] = exp
        out.append(e)
    return out


def load_memory(path: Path) -> str:
    """返回可注入 Coze prompt 的紧凑上下文串（仅未过期条目）。"""
    entries = list_entries(path, show_expired=False)
    if not entries:
        return ""
    lines: List[str] = ["[USER MEMORY · 本地记忆，仅作背景上下文，不得当作当前问题的事实]"]
    for e in entries:
        cat = e.get("category", "context")
        lines.append(f"- （{cat}）{e.get('content','')}")
    lines.append("[MEMORY TTL] 记忆默认 90 天有效；过期条目由 prune 清理。")
    return "\n".join(lines)


def prune(path: Path) -> int:
    """清理过期条目，返回删除数。"""
    now = datetime.now(timezone.utc)
    entries = _load_store(path)
    kept = [e for e in entries if not _is_expired(e, now)]
    removed = len(entries) - len(kept)
    if removed:
        _save_store(path, kept)
    return removed


def clear(path: Path, confirm: bool = False) -> int:
    if not confirm:
        raise PermissionError("clear 为破坏性操作，必须显式传 --confirm")
    n = len(_load_store(path))
    _save_store(path, [])
    return n


def _self_test() -> int:
    ok = True
    import tempfile
    tmp = Path(tempfile.mkdtemp()) / "mem_test.json"

    # add (interactive=False 必须 confirm)
    try:
        add_entry(tmp, "pref", "样本量默认 power=0.9", confirm=False)
        cond = False
    except PermissionError:
        cond = True
    print(f"[self-test] add requires confirm -> {cond} : {'PASS' if cond else 'FAIL'}")
    ok = ok and cond

    e = add_entry(tmp, "pref", "样本量默认 power=0.9", confirm=True)
    l = list_entries(tmp)
    cond2 = len(l) == 1 and l[0]["category"] == "pref"
    print(f"[self-test] add+list -> {cond2} : {'PASS' if cond2 else 'FAIL'}")
    ok = ok and cond2

    m = load_memory(tmp)
    cond3 = "power=0.9" in m and "[USER MEMORY" in m
    print(f"[self-test] load_memory -> {cond3} : {'PASS' if cond3 else 'FAIL'}")
    ok = ok and cond3

    n = clear(tmp, confirm=True)
    cond4 = n == 1 and len(_load_store(tmp)) == 0
    print(f"[self-test] clear -> {cond4} : {'PASS' if cond4 else 'FAIL'}")
    ok = ok and cond4

    print(f"[self-test] overall: {'ALL PASS' if ok else 'FAILED'}")
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="ct-advisor local user memory manager (pure-local)")
    ap.add_argument("action", nargs="?", choices=["add", "list", "load", "prune", "clear"],
                    help="memory operation")
    ap.add_argument("--category", default="context", help="pref|decision|term|context")
    ap.add_argument("--content", help="memory content (for add)")
    ap.add_argument("--ttl-days", type=int, default=DEFAULT_TTL_DAYS, help="TTL in days (default 90)")
    ap.add_argument("--path", default=str(_default_path()), help="memory json path")
    ap.add_argument("--confirm", action="store_true", help="explicit confirmation for add/clear")
    ap.add_argument("--show-expired", action="store_true", help="list also shows expired")
    ap.add_argument("--as-prompt", action="store_true", help="load outputs Coze-injectable context")
    ap.add_argument("--self-test", action="store_true", help="run minimal inline self-test")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(_self_test())

    path = Path(os.path.expanduser(args.path))
    action = args.action or "list"

    try:
        if action == "add":
            if not args.content:
                sys.stderr.write("[memory_manager] --content 必填\n")
                sys.exit(2)
            e = add_entry(path, args.category, args.content, args.ttl_days, args.confirm)
            sys.stdout.write(json.dumps(e, ensure_ascii=False) + "\n")
        elif action == "list":
            out = list_entries(path, args.show_expired)
            sys.stdout.write(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
        elif action == "load":
            ctx = load_memory(path)
            sys.stdout.write(ctx + ("\n" if ctx else ""))
        elif action == "prune":
            n = prune(path)
            sys.stdout.write(f"[memory_manager] pruned {n} expired entr(ies)\n")
        elif action == "clear":
            n = clear(path, args.confirm)
            sys.stdout.write(f"[memory_manager] cleared {n} entries\n")
        else:
            sys.stderr.write(f"[memory_manager] unknown action: {action}\n")
            sys.exit(2)
    except PermissionError as e:
        sys.stderr.write(f"[memory_manager] {e}\n")
        sys.exit(3)
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"[memory_manager] error: {type(e).__name__}: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
