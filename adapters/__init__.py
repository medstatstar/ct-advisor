"""ct-advisor 适配层统一出口 + 后端工厂。

默认零出站 + 零本地残留：
- build_backend() 在未配置 Coze 时回退 LocalBackend（不读 token、不发请求）。
- build_qa_store() 在未显式配置 qa_store.mode=local/remote 时返回 NoOpStore（不写任何文件）。
切换后端只需改 config.json 的 backend 字段 + 填 coze.bot_id；启用 QA 日志同理需显式开启。
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
from .qa_store import JsonlStore, NoOpStore, QARecord, QASessionStore, RemoteDbStore
from .sanitize import sanitize

__all__ = [
    "AdvisorBackend", "AdvisorRequest", "AdvisorResponse", "LocalBackend", "CozeBackend",
    "DataContextProvider", "DataRef", "LocalDiskDataContext", "CozeApiDataContext",
    "QASessionStore", "QARecord", "JsonlStore", "NoOpStore", "RemoteDbStore", "sanitize",
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
    mode = qs.get("mode")
    # 隐私默认：未显式开启则不持久化任何内容（NoOpStore）。
    if mode == "remote" and qs.get("remote_dsn"):
        return RemoteDbStore(dsn=qs.get("remote_dsn", ""))
    if mode == "local":
        return JsonlStore(path=qs.get("local_path", "data/qa_log.jsonl"))
    return NoOpStore()
