"""QASessionStore 适配层（seam）：沉淀问答，供后续检索/复盘/训练。

- 默认 NoOpStore：**不写任何文件**（隐私优先，零本地残留）。
- JsonlStore：需显式配置 qa_store.mode=local 才启用，追加写 data/qa_log.jsonl（开发/自测用，含引用与反馈）。
- RemoteDbStore：未来模式，写远端 DB（问答沉淀 + 更多数据参考）。当前为桩。
emit 一条结构化 QARecord 与 backend 实现无关；但除非显式开启，否则不会被持久化。
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class QARecord:
    session_id: str
    question: str
    workflow: str
    answer: str
    citations: List[str] = field(default_factory=list)
    grounded_data: List[str] = field(default_factory=list)
    feedback: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "question": self.question,
            "workflow": self.workflow,
            "answer": self.answer,
            "citations": self.citations,
            "grounded_data": self.grounded_data,
            "feedback": self.feedback,
            "timestamp": self.timestamp,
        }


class QASessionStore(ABC):
    @abstractmethod
    def log(self, record: QARecord) -> None:
        ...


class JsonlStore(QASessionStore):
    def __init__(self, path: str = "data/qa_log.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, record: QARecord) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


class RemoteDbStore(QASessionStore):
    def __init__(self, dsn: str = ""):
        self.dsn = dsn

    def log(self, record: QARecord) -> None:
        raise NotImplementedError("RemoteDbStore 尚未接入：配置 config.json 的 qa_store.remote_dsn 并实现 _insert()。")


class NoOpStore(QASessionStore):
    """隐私默认模式：丢弃所有记录，不写磁盘、不外发。"""
    def log(self, record: QARecord) -> None:
        return None
