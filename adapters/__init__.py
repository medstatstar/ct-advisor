"""ct-advisor 适配层统一出口 + 后端工厂。

本地默认零出站：build_backend() 在未配置 Coze 时回退 LocalBackend。
切换后端只需改 config.json 的 backend 字段 + 填 coze.bot_id。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .backend import (
    AdvisorBackend,
    AdvisorRequest,
    AdvisorResponse,
    CozeBackend,
    LocalBackend,
)
from .data_context import (
    CozeApiDataContext,
    DataContextProvider,
    DataRef,
    LocalDiskDataContext,
)
from .qa_store import JsonlStore, QARecord, QASessionStore, RemoteDbStore
from .sanitize import sanitize

__all__ = [
    "AdvisorBackend", "AdvisorRequest", "AdvisorResponse", "LocalBackend", "CozeBackend",
    "DataContextProvider", "DataRef", "LocalDiskDataContext", "CozeApiDataContext",
    "QASessionStore", "QARecord", "JsonlStore", "RemoteDbStore", "sanitize",
    "build_backend", "build_data_context", "build_qa_store",
]


def _load_config(config_path: str = "config.json") -> Dict[str, Any]:
    # Stdlib-only loader (no PyYAML dependency). Missing/excluded file falls
    # back to defaults (= local backend, zero outbound).
    p = Path(config_path)
    if p.exists():
        try:
            import json
            return json.loads(p.read_text(encoding="utf-8")) or {}
        except Exception:
            return {}
    return {}


def build_backend(config_path: str = "config.json") -> AdvisorBackend:
    cfg = _load_config(config_path)
    coze = cfg.get("coze", {}) or {}
    if cfg.get("backend") == "coze" and coze.get("bot_id"):
        return CozeBackend(
            bot_id=coze.get("bot_id", ""),
            endpoint=coze.get("endpoint", ""),
            token_env=coze.get("token_env", "COZE_TOKEN"),
        )
    return LocalBackend()


def build_data_context(config_path: str = "config.json") -> DataContextProvider:
    cfg = _load_config(config_path)
    dc = cfg.get("data_context", {}) or {}
    if dc.get("mode") == "coze":
        return CozeApiDataContext()
    return LocalDiskDataContext(sibling_outputs=dc.get("sibling_outputs"))


def build_qa_store(config_path: str = "config.json") -> QASessionStore:
    cfg = _load_config(config_path)
    qs = cfg.get("qa_store", {}) or {}
    if qs.get("mode") == "remote" and qs.get("remote_dsn"):
        return RemoteDbStore(dsn=qs.get("remote_dsn", ""))
    return JsonlStore(path=qs.get("local_path", "data/qa_log.jsonl"))
