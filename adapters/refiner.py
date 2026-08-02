"""答案精修适配层（第 4 个 seam）：本地草稿 → 外发 5 变量 → 回收最终答案。

设计要点（沿用 v0.8.2 审计后确立的「安全默认 + 显式 opt-in」范式）：
- LocalRefiner（默认）：直接返回 draft_answer，零网络、零第三方依赖。= 现在的反馈模式。
- CozeRefiner：将 5 变量 POST 到扣子服务器，≤timeout 秒回收 final_answer；
  任何超时 / 网络 / 解析 / 字段缺失异常都优雅回退到 draft_answer（绝不丢答案、绝不报错给用户）。
- 开启 coze 需在 config.json 显式配置 refiner.mode=coze + endpoint；默认 LocalRefiner 执行路径
  里没有任何网络代码、不导入 requests，避免上次审计的 phantom-outbound 误报。

外发 payload（5 变量）：
- category:            问题所属类别（如 methodology:B / design / compliance:D，或匹配的 A–J 工作流）
- original_question:  用户的原始问题
- organized_problems: 归纳整理后的问题列表（JSON 数组）
- draft_answer:       本地生成的答案（草稿）
- difficulty:         问题难度 simple | complex（gate-0 分流结论；仍模糊可标 vague）
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class RefineRequest:
    category: str = ""
    original_question: str = ""
    organized_problems: List[Dict[str, Any]] = field(default_factory=list)
    draft_answer: str = ""
    difficulty: str = ""  # simple | complex | vague

    def to_payload(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "original_question": self.original_question,
            "organized_problems": self.organized_problems,
            "draft_answer": self.draft_answer,
            "difficulty": self.difficulty,
        }


class Refiner(ABC):
    @abstractmethod
    def refine(self, req: RefineRequest, timeout: float = 15.0) -> str:
        """返回最终答案（服务器精修结果，或兜底回退的 draft_answer）。"""
        ...


class LocalRefiner(Refiner):
    """默认模式：零网络、零依赖，直接回传草稿。行为与原先完全一致。"""

    def refine(self, req: RefineRequest, timeout: float = 15.0) -> str:
        return req.draft_answer


class CozeRefiner(Refiner):
    """扣子服务器精修模式：外发 5 变量，≤timeout 秒回收 final_answer；异常兜底草稿。

    仅当 config.json 显式配置 refiner.mode=coze 且 endpoint 非空时才实例化。
    """

    def __init__(self, endpoint: str, token_env: str = "COZE_TOKEN", timeout: float = 15.0):
        self.endpoint = endpoint
        self.token_env = token_env
        self.timeout = timeout

    def refine(self, req: RefineRequest, timeout: float = None) -> str:
        timeout = timeout or self.timeout
        try:
            import os
            import requests  # 延迟导入：本地模式完全不依赖 requests
            from .sanitize import sanitize

            payload = sanitize(req.to_payload())  # 出站前脱敏（ct-base §11）
            token = os.environ.get(self.token_env, "")
            resp = requests.post(
                self.endpoint,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=timeout,
            )
            data = resp.json()
            return data.get("final_answer") or req.draft_answer
        except Exception:
            # 超时 / 连接失败 / 解析失败 / 字段缺失 → 兜底返回本地草稿
            return req.draft_answer
