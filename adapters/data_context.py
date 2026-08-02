"""DataContext 适配层（seam）：为方法学建议收集真实数据接地。

- LocalDiskDataContext：本地扫盘，读兄弟技能 out_live 下的 JSON，抽取少量关键字段。
- CozeApiDataContext：未来模式，走 Coze 侧数据 API / RAG。当前为桩。
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent  # .../skills/


@dataclass
class DataRef:
    skill: str
    path: str
    summary: str = ""
    fields: Dict[str, Any] = field(default_factory=dict)


class DataContextProvider(ABC):
    @abstractmethod
    def collect(self, skill: str, query: str = "") -> List[DataRef]:
        ...


class LocalDiskDataContext(DataContextProvider):
    def __init__(self, sibling_outputs: Dict[str, str] | None = None):
        self.sibling_outputs: Dict[str, str] = sibling_outputs or {
            "ct-registry": "ct-registry/out_live",
            "ct-safety": "ct-safety/out_live",
            "ct-literature": "ct-literature/out_live",
        }

    def collect(self, skill: str, query: str = "") -> List[DataRef]:
        rel = self.sibling_outputs.get(skill)
        if not rel:
            return []
        d = SKILLS_DIR / rel
        if not d.exists():
            return []
        refs: List[DataRef] = []
        for j in sorted(d.glob("*.json"))[:5]:   # 最多取 5 个最新文件
            try:
                data = json.loads(j.read_text(encoding="utf-8"))
            except Exception:
                continue
            refs.append(
                DataRef(
                    skill=skill,
                    path=str(j),
                    summary=f"{j.name} ({len(json.dumps(data, ensure_ascii=False))} bytes)",
                    fields=self._peek(data),
                )
            )
        return refs

    @staticmethod
    def _peek(data: Any) -> Dict[str, Any]:
        if isinstance(data, dict):
            return {k: type(data[k]).__name__ for k in list(data.keys())[:8]}
        if isinstance(data, list) and data:
            return {"__len__": len(data), "__item0_type__": type(data[0]).__name__}
        return {}


class CozeApiDataContext(DataContextProvider):
    def collect(self, skill: str, query: str = "") -> List[DataRef]:
        raise NotImplementedError("CozeApiDataContext 尚未接入：配置 config.json 的 data_context 模式并实现数据 API 调用。")
