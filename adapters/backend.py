"""Backend 适配层（关键 seam）：方法学推理的出口。

- LocalBackend：本地模式。返回可移植知识包（system_prompt + workflows + references），
  由 agent 结合本文件作答；本类不自行做 LLM 推理（agent 即后端）。
- CozeBackend：未来模式。把同一知识包 + 结构化 payload 发到 Coze Bot，返回结构化响应。
  当前为桩实现，advise() 与 _post() 均抛 NotImplementedError，**未激活、不读 token、不出站**；
  配置就绪并显式实现后切换，无需重写方法学内容。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


@dataclass
class AdvisorRequest:
    workflow: str
    question: str
    context: str = ""
    jurisdiction: str = ""
    data_refs: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass
class AdvisorResponse:
    answer: Optional[str] = None
    citations: List[str] = field(default_factory=list)
    workflow: str = ""
    grounded_data: List[Dict[str, Any]] = field(default_factory=list)
    needs_more: bool = False
    stop_reason: str = ""
    delegate_to_agent: bool = False          # 本地模式：标记由 agent 用知识包作答
    pack: Dict[str, Any] = field(default_factory=dict)


class AdvisorBackend(ABC):
    @abstractmethod
    def advise(self, req: AdvisorRequest) -> AdvisorResponse:
        ...


class LocalBackend(AdvisorBackend):
    def __init__(self, knowledge_dir: Path = KNOWLEDGE_DIR):
        self.knowledge_dir = Path(knowledge_dir)

    def load_pack(self) -> Dict[str, Any]:
        """组装可移植知识包（本地与 Coze 共用）。"""
        pack: Dict[str, Any] = {
            "system_prompt": (self.knowledge_dir / "system_prompt.md").read_text(encoding="utf-8"),
            "workflows": (SCRIPTS_DIR / "workflows.json").read_text(encoding="utf-8"),
        }
        refs: Dict[str, str] = {}
        ref_dir = self.knowledge_dir / "references"
        if ref_dir.exists():
            for f in sorted(ref_dir.glob("*.md")):
                refs[f.name] = f.read_text(encoding="utf-8")
        pack["references"] = refs
        return pack

    def advise(self, req: AdvisorRequest) -> AdvisorResponse:
        return AdvisorResponse(
            workflow=req.workflow,
            delegate_to_agent=True,
            pack=self.load_pack(),
        )


class CozeBackend(AdvisorBackend):
    def __init__(self, bot_id: str = "", endpoint: str = "", token_env: str = "COZE_TOKEN"):
        self.bot_id = bot_id
        self.endpoint = endpoint or "https://api.coze.cn/v1/chat"
        self.token_env = token_env

    def advise(self, req: AdvisorRequest) -> AdvisorResponse:
        raise NotImplementedError(
            "CozeBackend 尚未接入：在 config.json 配置 coze.bot_id/endpoint 并实现 _post() 后即可切换。"
        )

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """未激活：Coze 后端尚未接入，禁止任何真实出站。启用前需显式实现并移除本异常。"""
        raise NotImplementedError(
            "CozeBackend._post 尚未激活：在 config.json 配置 coze.bot_id/endpoint 并实现本方法前，"
            "不会读取 token 或发起任何 HTTP 请求。当前默认走 LocalBackend，完全本地执行。"
        )
