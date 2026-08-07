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
from .refiner import CozeRefiner, RefineRequest, Refiner, compute_machine_id, ACCURACY_ENUM, DIFFICULTY_ENUM, _parse_query_meta, strip_display_tags, MissingDependencyError
from .sanitize import sanitize

__all__ = [
    "AdvisorBackend", "AdvisorRequest", "AdvisorResponse", "LocalBackend", "CozeBackend",
    "DataContextProvider", "DataRef", "LocalDiskDataContext", "CozeApiDataContext",
    "QASessionStore", "QARecord", "JsonlStore", "NoOpStore", "RemoteDbStore", "sanitize",
    "Refiner", "RefineRequest", "CozeRefiner", "compute_machine_id",
    "ACCURACY_ENUM", "DIFFICULTY_ENUM", "_parse_query_meta",
    "build_backend", "build_data_context", "build_qa_store", "build_refiner", "MissingDependencyError",
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


def _resolve_token_path(config_path: str, rc: Dict[str, Any]) -> str:
    """解析 coze token 落盘路径，优先级：config.refiner.token_file > 技能默认绝对路径。

    - token_file 省略 → 用 adapters.coze_token.default_token_path()（绝对路径）。
    - token_file 以 ~ 或 / 开头 → 直接 expanduser / 按绝对路径。
    - 否则视为相对 config.json 目录的相对路径（如 "config/coze.dat"）。
    """
    import os
    from .coze_token import default_token_path

    tf = rc.get("token_file")
    if not tf:
        return default_token_path()
    if tf.startswith("~") or os.path.isabs(tf):
        return os.path.expanduser(tf)
    return os.path.join(os.path.dirname(os.path.abspath(config_path)), tf)


def build_refiner(config_path: str = "config.json",
                  cli_token: str = None, token_path: str = None) -> Refiner:
    """答案精校出口（第 4 个 seam）。

    Coze 是唯一的精校后端：按难度自动分流——simple/middle 后台竞速择优选、complex/vague 前台串行等待，都经此调用
    Coze 精校，两者都在失败/超时时由 CozeRefiner 内置回退到本地 draft_answer。

    token 解析：CLI(--token) > env(CT_ADVISOR_COZE_TOKEN) > 混淆落盘文件（见 adapters/coze_token.py）。
    token_path 参数（来自 refine_answer.py --token-path）可覆盖 config 中的 token_file。
    """
    cfg = _load_config(config_path)
    rc = cfg.get("refiner", {}) or {}
    answer_mode = cfg.get("answer_mode", "fast")
    if answer_mode != "fast":
        answer_mode = "fast"  # 2026-08-05 起仅保留 fast 模式（precise 已删除）
    return CozeRefiner(
        endpoint=rc.get("endpoint", ""),
        token_env=rc.get("token_env", "CT_ADVISOR_COZE_TOKEN"),
        timeout=float(rc.get("timeout", 60.0)),
        race_window=float(rc.get("race_window", 2.0)),
        cli_token=cli_token,
        token_path=token_path or _resolve_token_path(config_path, rc),
        answer_mode=answer_mode,
    )
