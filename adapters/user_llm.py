#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ct-base · 用户自带大模型直连客户端（OpenAI 兼容 / Anthropic 原生双格式，纯标准库）
================================================================================
家族**单一真相源**（ct-base §29.13「用户自带大模型覆盖」）。

分发机制（与 coze_kernel.py 同源）：ct-base 持有本文件 → publish_inject 注入各技能
`adapters/user_llm.py` → 客户端 `import user_llm` 引用**注入副本**
（**禁止运行时跨技能 import**，技能是独立发布单元，用户机器未必装 ct-base）。

设计依据 / 安全边界（§29.13）：
- 用途：用户在「系统选项」页填入自己的 API Base URL / API Key / Model；
  后端在所有大模型调用处优先直连用户的端点，默认大模型（如 Coze 共用端点）作回退。
- 安全边界：密钥**绝不**写入磁盘/日志；密钥只来自前端随请求注入的 `llm_config`
  字段（内存态，用完即弃）。与「工作台应用发布」场景一致——共享/托管环境不落盘用户密钥。
- **两种 API 格式（2026-11-16 新增，§27.13「API 格式支持」）**：
  * `openai`（默认）：OpenAI 兼容 `/chat/completions`——OpenAI / DeepSeek / 通义 /
    Kimi / 本地 vLLM / ollama 等；鉴权 `Authorization: Bearer`；body 用 `messages` 数组，
    system 走 `role=system`；响应取 `choices[0].message.content`。
  * `anthropic`：Anthropic 原生 `/v1/messages`——Claude 官方端点或兼容代理；鉴权 `x-api-key`
    + `anthropic-version`；`system` 是**顶层字段**（不在 messages 内）、`max_tokens` **必填**；
    响应取 `content[]` 中 `type=="text"` 的片段拼接。
  格式判定 `resolve_api_format()`：显式 `api_format` 优先，缺省按 base_url 关键词
  （anthropic / claude）自动识别，否则 openai——老配置（无该字段）行为不变。
- base_url 容忍：`/v1`、裸域名、已含 `/chat/completions`（或 Anthropic 的 `/messages`）。
- 出站门控：`_resolve_url` 默认只允许 https；明文 http 仅放行回环
  （127.0.0.1 / localhost），防内网穿透与明文泄露。
- **与飞书 configtbl 默认配置的配合（优先级，§29.13.2）**：家族「发布为应用」的后台默认大模型
  由 `llm_config.resolve_llm_config()` 从飞书共享 configtbl（CT_LLM_*）解析（§12），这是**系统默认**
  模型（LongCat 等）。本模块承载的「用户自定义配置」是 **per-user override**：
  当且仅当用户在系统选项页填写了合法三要素（**配置即生效，无勾选框**，2026-11-16 裁定）时，
  前端随 `/api/proxy` 注入 `llm_config`，并**优先于飞书默认**直连用户的端点；用户未配置时回落飞书默认
  （→ 打包快照 backend.llm → 内置兜底）。二者键名不同（用户用 base_url/api_key/model；
  飞书默认用 baseUrl/model + apiKeyEnv/apiKeyFile），属不同调用路径，由路由层按优先级择一，
  而非合并为同一配置对象——详见 server.py `/api/proxy` 与 §29.13.2。
- 零第三方依赖（仅标准库），与家族「发布包零外部依赖」一致。

技能特有部分（action → 提示词翻译）**外置**为可注册钩子 `set_action_translator()`，
算法内核保持单一、差异外置（对齐 coze_kernel 的 CozeKernelConfig 思路）：
各技能在 server.py 中 `import user_llm; user_llm.set_action_translator(my_translate)`，
未注册时退回内置通用翻译（把 action+params 原样交给用户模型）。

用法示例（叶子 server.py）：
    import user_llm
    user_llm.set_action_translator(sas2r_translate)   # 注册本技能翻译层
    ...
    # 优先级（§29.13.2）：用户自定义配置优先；None → 飞书 configtbl 默认
    override = user_llm.user_override_config(user_cfg)
    if user_llm and override:
        msgs = user_llm.build_messages_from_action(action, params, lang)
        text = user_llm.call_chat(override, msgs)
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

__all__ = [
    "is_valid",
    "resolve_api_format",
    "resolve_url",
    "normalize_messages",
    "call_chat",
    "build_messages_from_action",
    "set_action_translator",
    "DEFAULT_TRANSLATOR",
    "user_override_config",
]

# 允许的出站协议白名单（仅 https，防明文/内网滥用）
_ALLOWED_SCHEMES = ("https",)
# 明文 http 仅放行的回环主机（本地 vLLM / ollama 等）
_LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "[::1]", "::1")
# 支持的 API 格式（§27.13「API 格式支持」）
API_FORMATS = ("openai", "anthropic")
DEFAULT_API_FORMAT = "openai"
# Anthropic 原生端点要求必填 max_tokens；缺省给足量以避免长方案被截断
_DEFAULT_MAX_TOKENS = 4096
_ANTHROPIC_VERSION = "2023-06-01"


def is_valid(cfg: dict | None) -> bool:
    """最小校验：base_url / api_key / model 三者齐备才视为可用（§29.13 三要素）。"""
    if not isinstance(cfg, dict):
        return False
    return bool(cfg.get("base_url")) and bool(cfg.get("api_key")) and bool(cfg.get("model"))


def user_override_config(user_cfg: dict | None) -> dict | None:
    """用户自定义覆盖层（§29.13.2 优先级判定入口）。

    返回合法的用户自定义配置；非法/缺失返回 None（表示回落飞书 configtbl 默认）。
    路由层（server.py `/api/proxy`）据此决定 engine：
      非 None → engine="user-llm"（直连用户端点）；
      None    → 默认后端（飞书 configtbl 解析的 LongCat 等，见 llm_config.resolve_llm_config）。
    """
    return user_cfg if is_valid(user_cfg) else None


def resolve_api_format(cfg: dict | None) -> str:
    """判定该配置该按哪种 API 格式发请求（§27.13「API 格式支持」）。

    显式 `api_format`（openai / anthropic）优先；缺省按 base_url 关键词自动识别
    （含 anthropic / claude → anthropic），否则回 DEFAULT_API_FORMAT。
    老配置没有该字段 → 行为与旧版完全一致（openai），不需要迁移。
    """
    fmt = str((cfg or {}).get("api_format") or "").strip().lower()
    if fmt in API_FORMATS:
        return fmt
    u = str((cfg or {}).get("base_url") or "").lower()
    if "anthropic" in u or "claude" in u:
        return "anthropic"
    return DEFAULT_API_FORMAT


def _check_scheme(u: str) -> None:
    """出站协议门控：https 一律放行；明文 http 仅回环；其它一律拒绝。"""
    if u.startswith("http://"):
        host = u[len("http://"):].split("/", 1)[0].split(":", 1)[0].lower()
        if host not in _LOOPBACK_HOSTS:
            raise ValueError("明文 http 仅允许回环（127.0.0.1 / localhost），外网请用 https")
    elif not u.startswith("https://"):
        raise ValueError("base_url 须以 https:// 开头（回环可用 http://127.0.0.1/localhost）")


def resolve_url(base_url: str, api_format: str = DEFAULT_API_FORMAT) -> str:
    """把用户给的 base_url 归一化为完整请求地址。

    - openai   → `/chat/completions`（已含则不重复拼）
    - anthropic→ `/v1/messages`（已含 `/messages` 原样；已带 `/v1` 只补 `/messages`）

    安全门控：https 一律放行；明文 http 仅允许回环（127.0.0.1/localhost）；
    其它协议/主机一律拒绝（防内网穿透与明文泄露，见 §29.13）。
    """
    u = (base_url or "").strip()
    if not u:
        raise ValueError("base_url 为空")
    _check_scheme(u)
    if api_format == "anthropic":
        if "/messages" in u:
            return u
        base = u.rstrip("/")
        return (base + "/messages") if base.endswith("/v1") else (base + "/v1/messages")
    if "/chat/completions" in u:
        return u
    return u.rstrip("/") + "/chat/completions"


def normalize_messages(cfg: dict, messages: list[dict]) -> list[dict]:
    """注入用户系统提示词（`system_prompt`）。

    2026-11-14 修正（沉淀自 ct-sas2r「配置项是否真生效」复核）：
    旧实现「首条已是 system 就整条跳过」，而各技能的 action 翻译层**恒定**自带一条
    领域 system 提示词（如 ct-sas2r 的「你是 SAS→R 迁移专家…」），导致用户在系统选项
    填的 system_prompt 在 `/api/proxy`（方案生成）路径上**静默失效**，只在
    `/api/llm`（测试连接/自由问答）路径生效——同一配置两套行为。

    现行口径：用户提示词**追加**到既有 system 消息尾部（领域约束在前、用户偏好在后），
    既保留技能领域约束，又让用户配置真实生效；无 system 消息时按原逻辑插入首条。
    """
    msgs = [dict(m) for m in (messages or [])]   # 浅拷贝，避免改到调用方列表
    sp = (cfg.get("system_prompt") or "").strip()
    if not sp:
        return msgs
    if msgs and msgs[0].get("role") == "system":
        base = str(msgs[0].get("content") or "").rstrip()
        msgs[0]["content"] = (base + "\n\n" + sp) if base else sp
    else:
        msgs.insert(0, {"role": "system", "content": sp})
    return msgs


def _temperature(cfg: dict, temperature: float | None, cap: float | None = None) -> float:
    """温度归一：cfg 优先 → 调用方 → 0.3；Anthropic 上限 1.0（超出会被端点拒绝）。"""
    try:
        tv = float(cfg.get("temperature", temperature if temperature is not None else 0.3))
    except (TypeError, ValueError):
        tv = 0.3
    if tv < 0:
        tv = 0.0
    if cap is not None and tv > cap:
        tv = cap
    elif cap is None and tv > 2:
        tv = 2.0
    return tv


def _anthropic_payload(cfg: dict, messages: list[dict], temperature: float | None) -> dict:
    """构造 Anthropic `/v1/messages` 请求体：system 提到顶层、其余消息保序。"""
    msgs = [dict(m) for m in (messages or [])]
    sys_parts = [str(m.get("content") or "").strip() for m in msgs if m.get("role") == "system"]
    sp = (cfg.get("system_prompt") or "").strip()
    if sp:
        sys_parts.append(sp)          # 与 OpenAI 路径同口径：领域约束在前、用户偏好在后
    conv = []
    for m in msgs:
        role = m.get("role")
        if role == "system":
            continue
        conv.append({"role": "user" if role not in ("user", "assistant") else role,
                     "content": m.get("content") or ""})
    if not conv:                       # Anthropic 要求 messages 非空
        conv = [{"role": "user", "content": "ping"}]
    try:
        max_tokens = int(cfg.get("max_tokens") or _DEFAULT_MAX_TOKENS)
    except (TypeError, ValueError):
        max_tokens = _DEFAULT_MAX_TOKENS
    body = {
        "model": cfg["model"],
        "max_tokens": max_tokens if max_tokens > 0 else _DEFAULT_MAX_TOKENS,
        "messages": conv,
        "temperature": _temperature(cfg, temperature, cap=1.0),
    }
    sys_txt = "\n\n".join([p for p in sys_parts if p])
    if sys_txt:
        body["system"] = sys_txt
    return body


def call_chat(cfg: dict, messages: list[dict], temperature: float | None = None,
              timeout: int = 120) -> str:
    """直连用户端点，返回助手消息文本（按 `api_format` 走 OpenAI 兼容或 Anthropic 原生）。

    参数:
      cfg: {base_url, api_key, model, api_format?, system_prompt?, temperature?, max_tokens?}
      messages: OpenAI 风格消息列表（Anthropic 路径内部自动转换 system / max_tokens）
    返回: 模型生成的文本（str）
    异常: ValueError（配置/URL 非法）/ RuntimeError（HTTP 错误、响应结构不符）——由调用方捕获。
    """
    if not is_valid(cfg):
        raise ValueError("用户大模型配置不完整（需 base_url / api_key / model）")
    fmt = resolve_api_format(cfg)
    url = resolve_url(cfg["base_url"], fmt)
    if fmt == "anthropic":
        body = _anthropic_payload(cfg, messages, temperature)
        headers = {"x-api-key": cfg["api_key"],
                   "anthropic-version": _ANTHROPIC_VERSION,
                   "Content-Type": "application/json"}
    else:
        body = {
            "model": cfg["model"],
            "messages": normalize_messages(cfg, messages),
            # cfg.temperature 优先，否则用调用方传入的 temperature，最后兜底 0.3
            "temperature": _temperature(cfg, temperature),
        }
        headers = {"Authorization": "Bearer " + cfg["api_key"],
                   "Content-Type": "application/json"}
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        raise RuntimeError("HTTP %d: %s" % (e.code, raw[:500])) from e
    if fmt == "anthropic":
        blocks = resp.get("content") if isinstance(resp, dict) else None
        if isinstance(blocks, list):
            text = "".join(str(b.get("text") or "") for b in blocks
                           if isinstance(b, dict) and b.get("type") in (None, "text"))
            if text:
                return text
        raise RuntimeError("端点响应缺少 content[].text（Anthropic /v1/messages 格式）：%s" % str(resp)[:300])
    try:
        return resp["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError("端点响应缺少 choices[0].message.content：%s" % str(resp)[:300]) from e


# ---------------------------------------------------------------------------
# action → 提示词翻译（技能特有，外置为可注册钩子）
# ---------------------------------------------------------------------------
def _default_translator(action: str, params: dict, lang: str) -> list[dict]:
    """通用兜底翻译：未注册本技能翻译层时使用——把 action + params 原样交给用户模型。"""
    zh = lang == "zh"
    sys = ("你是临床试验统计编程助手，服务于 ct- 技能族。" if zh
           else "You are a clinical-trial statistical programming assistant for the ct- skill family.")
    user = (f"请处理请求 action={action}。参数：\n"
            f"{json.dumps(params or {}, ensure_ascii=False, indent=2)}")
    return [{"role": "system", "content": sys}, {"role": "user", "content": user}]


# 当前生效的翻译层（默认通用兜底）；叶子 server.py 调 set_action_translator 覆盖
_ACTION_TRANSLATOR = _default_translator


def set_action_translator(fn) -> None:
    """注册本技能的 action → 提示词翻译函数 `fn(action, params, lang) -> list[dict]`。

    把技能特有知识（领域系统提示词、各 action 的自然语言意图）外置到叶子，
    内核保持单一（对齐 coze_kernel 的算法单一 / 差异外置原则）。
    """
    global _ACTION_TRANSLATOR
    if not callable(fn):
        raise TypeError("translator 必须是可调用对象 (action, params, lang) -> list[dict]")
    _ACTION_TRANSLATOR = fn


def build_messages_from_action(action: str, params: dict, lang: str = "zh") -> list[dict]:
    """把结构化 action + params 转成 OpenAI 消息列表，交给用户的模型产出等价结果。

    这是「全量直连替换」的翻译层：Coze 原本按 action 编排，这里把同样的意图
    以自然语言交给用户的 OpenAI 兼容模型。实际翻译委托给 `_ACTION_TRANSLATOR`
    （默认通用兜底；叶子注册后即为本技能专用）。
    """
    return _ACTION_TRANSLATOR(action, params or {}, lang)


def DEFAULT_TRANSLATOR(action: str, params: dict, lang: str) -> list[dict]:
    """对外暴露的通用兜底翻译（便于叶子参考 / 测试）。"""
    return _default_translator(action, params, lang)


if __name__ == "__main__":
    # 本地自测：仅验证 URL 归一化与三要素校验，不触网、不打印密钥
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        cases = [
            "https://api.openai.com/v1",
            "https://api.deepseek.com",
            "http://127.0.0.1:11434",
            "http://localhost:8080/v1",
            "http://example.com",
        ]
        for c in cases:
            try:
                print("OK  ", c, "->", resolve_url(c))
            except ValueError as e:
                print("BLOCK", c, "->", e)
        print("--- anthropic ---")
        for c in ["https://api.anthropic.com", "https://api.anthropic.com/v1",
                  "https://api.anthropic.com/v1/messages", "https://proxy.example.com/claude"]:
            print("OK  ", c, "->", resolve_url(c, "anthropic"))
        print("--- api_format 识别 ---")
        for c in [{"base_url": "https://api.anthropic.com"},
                  {"base_url": "https://api.openai.com/v1"},
                  {"base_url": "https://x/v1", "api_format": "Anthropic"},
                  {"base_url": "https://api.deepseek.com/v1"}]:
            print("fmt ", c["base_url"], "->", resolve_api_format(c))
        print("is_valid(full)=", is_valid({"base_url": "https://x/v1", "api_key": "k", "model": "m"}))
        print("is_valid(partial)=", is_valid({"base_url": "https://x/v1", "api_key": "k"}))
        print("anthropic body=", json.dumps(_anthropic_payload(
            {"model": "m", "system_prompt": "偏好", "temperature": 1.5},
            [{"role": "system", "content": "领域约束"}, {"role": "user", "content": "hi"}], None),
            ensure_ascii=False))
    else:
        print("用法: python user_llm.py selftest")
