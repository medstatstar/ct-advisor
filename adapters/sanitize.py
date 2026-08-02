"""出站脱敏：payload 离开本地前剥离 PII / 保密字段 / token。

统一在所有出站调用（未来 Coze / 远端 DB）前执行；本地模式也跑（零成本），
守住 ct-base §11「绝不暴露 token 明文」与「不泄露个人信息/受试者信息」的红线。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

_SECRET_KEYS = (
    "token", "api_key", "apikey", "password", "secret",
    "access_key", "authorization", "cookie", "credential",
)
_PII_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"\b1[3-9]\d{9}\b"),            # 手机号
    re.compile(r"\b\d{17}[\dXx]\b"),          # 身份证
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),  # 邮箱
]
_SENSITIVE_KEYWORDS = ("受试者", "subject", "patient_name", "private_path")


def _scrub_value(v: Any) -> Any:
    if isinstance(v, dict):
        return _scrub_dict(v)
    if isinstance(v, list):
        return [_scrub_value(x) for x in v]
    if isinstance(v, str):
        s = v
        for p in _PII_PATTERNS:
            s = p.sub("***PII***", s)
        return s
    return v


def _scrub_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in d.items():
        kl = str(k).lower()
        if any(secret in kl for secret in _SECRET_KEYS):
            out[k] = "***REDACTED***"
            continue
        if any(kw in kl for kw in _SENSITIVE_KEYWORDS):
            out[k] = "***REDACTED***"
            continue
        out[k] = _scrub_value(v)
    return out


def sanitize(payload: Dict[str, Any]) -> Dict[str, Any]:
    """返回脱敏后的 payload 副本；不修改入参。"""
    return _scrub_dict(payload)
