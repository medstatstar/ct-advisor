"""答案精校适配层（第 4 个 seam）：本地草稿 → 外发 3 变量 → 回收最终答案。

设计要点（沿用 v0.8.2 审计后确立的「安全默认」范式）：
- CozeRefiner 是**唯一**的精校后端：将 3 变量 POST 到扣子服务器，≤timeout 秒回收 final_answer；
  任何超时 / 网络 / 解析 / 字段缺失异常都优雅回退到 draft_answer（绝不丢答案、绝不报错给用户）。
- 不再有「local 精校模式」：答案精校经唯一的 `fast` 模式控制，按难度自动分流——
  simple/middle 走 **race 竞速（早发 / 速度优先）**：agent 在 **step 2** 后台调用
  `--fire-only`（agent 仅发 original_question，difficulty/category/accuracy 未提供时由脚本补空串，draft 留空），
  Coze 用**完整 60s** HTTP 超时独立分析；成功后写入 race 缓存。
  agent 在 **step 3** 并行写本地草稿 + `--collect` 收集：缓存命中（Coze 先回）→ 采用
  Coze（中断本地）；否则直接采用本地草稿（速度优先——本地秒级先出、Coze 实测 9~25s 慢、
  常态本地胜出）。complex/vague 走 **串行**（前台等 Coze 完整返回、含 draft_answer 一并发送），
  两者都走 Coze、失败/超时回退本地草稿。
- 依赖保障：出站前 `_ensure_requests()` 确保 `requests` 可用。首次缺失时**提示用户手动安装后退出**——不自动执行 `pip install`，避免在用户环境静默引入外部依赖。

外发 payload（3 变量）：
- query_meta:   dict，包含 difficulty / category / accuracy 三字段 + query_origin 机器标识
                - difficulty: 问题难度 simple | middle | complex | vague（gate-0 分流结论）
                - category:   问题类别（如 methodology:B / methodology:C / design / compliance:D，或匹配的 A–J 工作流；样本量用 methodology:C）
                - accuracy:   自评准确度 good | normal（good = 精确，normal = 一般）
                - query_origin: 审计元数据——机器标识（sha256(hostname)，主机派生的稳定标识：不含明文主机名/IP，但同设备跨请求稳定；不可逆；《隐私段》已向用户披露），
                                由脚本在 normalize() 时自动盖章写入本 dict（不再另设顶层字段）
- original_question:  用户的原始问题（未加工原话）
- draft_answer:       本地生成的答案（草稿），供服务器参考/精校（允许空串）。
                      注意：accuracy 不再写入 draft_answer，而是放在 query_meta 中。

来源标记协议（v0.9.1+）：
- draft_answer 中来自其他 ct 技能的段落用 <source skill="ct-xxx">...</source> 标记。
- ct-advisor 自己整合的段落**不**带标签。
- 出站给 coze 时**不剥离**标签——原样发送，由 coze prompt 负责识别并跳过标记段落。
- 因此本模块不需要剥离/嵌入逻辑，标签会原样穿过 coze。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import copy

# i18n: user-facing prompts (EN/ZH) resolved by OS locale / config
import pathlib
_SKILL_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))
from scripts.i18n import t  # noqa: E402

# 公共凭据统一从 adapters/coze_token_embedded.py 导入（XOR+base64 混淆内嵌，ct-base §5 合规；
# .py 后缀不被 SkillHub 文件过滤删除；禁明文 JWT 落盘）。
from adapters.coze_token_embedded import get_token


class MissingDependencyError(Exception):
    """精校所需的第三方依赖缺失（如 requests），且自动安装失败。

    该异常**不**应被 refine() 的兜底逻辑静默吞掉——调用方须显式告知用户安装，
    否则用户会误以为拿到的答案来自 Coze 精校，实则是未精校的本地草稿。
    """


def _ensure_requests():
    """确保 ``requests`` 可用：先导入；缺失则提示用户手动安装并退出。

    出站精校（Coze）需要 ``requests`` 发起 HTTPS 请求。首次运行时若本地未装，
    **必须提示用户手动安装**（不自动执行 pip install，避免在用户环境静默引入外部依赖）。

    交互模式（stdin 为 TTY）：显示手动安装命令并退出；
    非交互模式（stdin 为管道 / 后台调用 --fire-only）：同样提示手动命令并退出。
    """
    try:
        import requests  # noqa: F401
        return requests
    except ImportError:
        pass

    # 缺失：用 i18n 输出随 locale 切换的安装提示，提示用户手动安装后退出
    install_cmd = 'python -m pip install "requests==2.32.3"'
    notice = t("error.requests_missing", cmd=install_cmd)

    # 两种模式均提示手动安装后退出（不自动执行 pip install）
    raise MissingDependencyError(notice)


# 展示前剥离 <source> 标签的正则（注意：用字符类 ["'] 避免 \" 在 raw string 中的解析问题）
_DISPLAY_TAG_RE = re.compile(r'''<source\s+skill=["'][^"]*["']>\s*''', re.IGNORECASE)
_DISPLAY_CLOSE_TAG_RE = re.compile(r'\s*</source>', re.IGNORECASE)


def strip_display_tags(text: str) -> str:
    """剥离 <source skill="xxx"> 标签，仅用于展示。
    保留标签内的内容，只移除标签本身。
    示例：'<source skill="ct-safety">内容</source>' → '内容'
    """
    s = _DISPLAY_TAG_RE.sub("", text)
    s = _DISPLAY_CLOSE_TAG_RE.sub("", s)
    return s

# difficulty 枚举（simple/middle/complex/vague）
DIFFICULTY_ENUM = ("simple", "middle", "complex", "vague")

# accuracy 枚举（good/normal）—— good = 精确，normal = 一般
ACCURACY_ENUM = ("good", "normal")

def compute_machine_id() -> str:
    """稳定、不可逆的机器标识，由脚本在调用时自动盖章（覆盖输入，agent 不应手写）。

    同一台机器每次返回相同值（便于 Coze 侧按机器做审计/归因/限流）——实现为
    sha256(hostname)，属**主机派生的稳定标识**：不含明文主机名/IP，但低熵主机名
    理论上可被暴力猜测；且稳定值意味着外部服务可跨请求关联同一设备（已在 README
    隐私段向用户披露，属接受的设计权衡——若要完全消除设备关联须改用每请求随机值，
    见 CHANGELOG 0.9.52 曾改随机后被回退的往复）。
    """
    return "sha256:" + hashlib.sha256(socket.gethostname().encode("utf-8")).hexdigest()


def _parse_query_meta(query_meta: Any) -> Dict[str, Any]:
    """解析 query_meta：支持 JSON 字符串或 dict；缺失字段给默认值空串。

    query_origin（机器标识）若已在输入中存在则原样保留，供 validate() 校验。
    """
    if isinstance(query_meta, str):
        try:
            meta = json.loads(query_meta)
        except Exception:
            meta = {}
    elif isinstance(query_meta, dict):
        meta = dict(query_meta)
    else:
        meta = {}
    result: Dict[str, Any] = {
        "difficulty": str(meta.get("difficulty", "")).strip(),
        "category": str(meta.get("category", "")).strip(),
        "accuracy": str(meta.get("accuracy", "")).strip(),
    }
    # query_origin 透传：若输入已含合法机器标识则保留，否则留空待 normalize() 盖章
    qo = meta.get("query_origin", "")
    result["query_origin"] = str(qo).strip() if qo else ""
    return result


@dataclass
class RefineResult:
    """Coze 单次调用的结构化结果（全量直发方案，2026-08-14）。

    兼容旧调用方：final_answer 始终有值（need_tool 分支下为 Coze 草稿），
    cache_hit 字段保留；新字段 need_tool / params 供本地执行器识别。
    """
    final_answer: str = ""            # Coze 最终答案；need_tool 分支下=Coze 草稿（缝合基底）
    cached_answer: str = ""           # 缓存命中答案（兼容旧字段）
    cache_hit: bool = False           # 是否命中缓存
    need_tool: Optional[str] = None   # 需要本地执行的技能标识（None=无需技能）
    params: dict = field(default_factory=dict)  # 技能入参
    run_id: str = ""                  # 追踪用


@dataclass
class RefineRequest:
    query_meta: dict = field(default_factory=dict)  # 包含 difficulty / category / accuracy / query_origin 的字典
    original_question: str = ""
    draft_answer: str = ""
    # 增量兼容字段（P0-A 本地澄清循环）：澄清子流程产出的问题画像与确认摘要。
    # 默认空 dict，下游（Coze 精校 / 本地草稿）忽略；原三字段契约完全不变。
    question_profile: dict = field(default_factory=dict)
    confirmation: dict = field(default_factory=dict)
    # 增量兼容字段（P0-B 语气写作）：tone_matcher.py 产出的风格 profile（仅风格、无事实）。
    # 默认空 dict；非空时随契约外发，Coze 按风格硬闸书写答案，绝不搬用样本事实。
    tone_profile: dict = field(default_factory=dict)
    # 增量兼容字段（P1-D 本地用户记忆）：memory_manager.py 产出的跨会话记忆上下文。
    # 默认空 dict；非空时随契约外发，仅作背景上下文，不得当作当前问题的事实。
    memory_context: dict = field(default_factory=dict)
    max_items: Optional[int] = None  # 已废弃且无操作：条目数量不再校验上限，统一直接发送 coze。

    def normalize(self) -> List[str]:
        """契约自愈（contract self-healing）。

        在 ``validate()`` 之前调用，将缺失/非法的可选字段补全为合法默认值，
        使 payload 在到达契约校验时一定合法——从根源上杜绝「契约校验失败 →
        静默兜底、远程根本没被调用」这一整类问题。

        自愈策略：
          - ``query_meta``：解析并修正枚举非法值；difficulty / category / accuracy
            缺失或非枚举合法值时统一补空串（``""``）；``query_origin`` 缺失则由脚本自动盖章
            （sha256 机器标识，写入 query_meta 字典）。
          - ``original_question``：若空，用 ``draft_answer`` 首行兜底。

        仅当 ``original_question`` 与 ``draft_answer`` 均为空（没有任何内容可兜底）
        时无法自愈；此时 ``validate()`` 会抛错，交由调用方（refine_answer.py）
        显式告警 + 兜底（而非静默）。

        返回本次被自动补全的字段/动作说明列表，供调用方在 stderr 做可见提示。
        """
        notes: List[str] = []

        # 1) query_meta：解析并补齐 / 修正枚举非法值（始终维持 dict 类型）
        if isinstance(self.query_meta, str):
            meta = _parse_query_meta(self.query_meta)
        elif isinstance(self.query_meta, dict):
            meta = dict(self.query_meta)
        else:
            meta = {}
        changed = False
        # difficulty 兜底（2026-08-12，2026-08-17 复核）：本地 route.py 的主用途是「拆分出 vague」
        # （vague 本地拦截、不转发），非 vague 转发时附带 simple/middle/complex 标签仅作提示；
        # 服务端 generate_organized_problems_node 会【一律用 LLM 重新估计】difficulty 并写回，
        # 因此此处兜底默认值不决定最终难度，仅保证出站 query_meta 非空（避免飞书收集空白）。
        # 缺失/非法一律默认 "complex"（宁保守，绝不空白）。
        if not meta.get("difficulty") or meta["difficulty"] not in DIFFICULTY_ENUM:
            meta["difficulty"] = "complex"
            changed = True
        # category：允许 string 或 string[]（多标签）；缺失/空补空串；多标签去重保序、不裁剪
        cat_raw = meta.get("category", "")
        if isinstance(cat_raw, list):
            cat_filtered = []
            cat_seen = set()
            for s in cat_raw:
                if isinstance(s, str) and s.strip():
                    s2 = s.strip()
                    if s2 not in cat_seen:
                        cat_seen.add(s2)
                        cat_filtered.append(s2)
            meta["category"] = cat_filtered if cat_filtered else ""
            changed = True
        elif isinstance(cat_raw, str) and cat_raw.strip():
            pass  # 合法 string，保留
        else:
            meta["category"] = ""
            changed = True
        if not meta.get("accuracy") or meta["accuracy"] not in ACCURACY_ENUM:
            meta["accuracy"] = ""
            changed = True
        if changed or not isinstance(self.query_meta, dict):
            self.query_meta = meta
            notes.append("query_meta(auto-filled/coerced, kept as dict)")

        # 2) original_question：若空，用 draft_answer 首行兜底
        if not self.original_question or not self.original_question.strip():
            if self.draft_answer and self.draft_answer.strip():
                self.original_question = self.draft_answer.strip().splitlines()[0][:200]
                notes.append("original_question(filled from draft_answer)")
            # 两者皆空时不兜底，留给 validate 显式报错

        # 4) question_profile / confirmation（P0-A 增量字段）：非 dict 一律归一为空 dict，
        #    保证 to_payload() 外发的 JSON 始终合法、下游兼容。
        if not isinstance(self.question_profile, dict):
            self.question_profile = {}
        if not isinstance(self.confirmation, dict):
            self.confirmation = {}
        # 5) tone_profile / memory_context（P0-B / P1-D 增量字段）：非 dict 一律归一为空 dict。
        if not isinstance(self.tone_profile, dict):
            self.tone_profile = {}
        if not isinstance(self.memory_context, dict):
            self.memory_context = {}

        # 3) query_origin：脚本会盖章，写入 query_meta 字典（不再另设顶层字段）
        qm = self.query_meta if isinstance(self.query_meta, dict) else {}
        if not qm.get("query_origin") or not str(qm.get("query_origin", "")).strip():
            qm["query_origin"] = compute_machine_id()
            notes.append("query_meta.query_origin(stamped)")
            self.query_meta = qm

        return notes
    def validate(self) -> None:
        """契约校验（contract-first）。

        经 ``normalize()`` 自愈后，除「original_question 与 draft_answer 均为空」
        这一极端情形外，应当总能通过。校验失败抛 ValueError；调用方负责捕获后
        显式告警 + 兜底，不再静默。

        字段约束（经 normalize() 自愈后）：
          - query_meta       : 非空 dict，包含 difficulty / category / accuracy / query_origin
                               difficulty ∈ {simple, middle, complex, vague}（允许为空串）
                               accuracy ∈ {good, normal}（允许为空串）
                               category   : 任意非空串，或为空串（允许未提供）
                               query_origin : 非空，格式 sha256:<64 hex>（机器标识，脚本盖章）
          - original_question  : 非空
          - draft_answer       : 允许为空
          - difficulty / category / accuracy 缺失时由 normalize() 补空串，不再强制非空；
            仅当「非空但枚举非法」时（difficulty / accuracy）才报错。
        校验失败抛 ValueError；调用方（refine_answer.py）捕获后兜底输出 draft_answer。
        """
        # 校验 query_meta
        if not self.query_meta or not str(self.query_meta).strip():
            raise ValueError("required field 'query_meta' is empty")
        meta = _parse_query_meta(self.query_meta)
        # difficulty / category / accuracy 允许为空串（agent 未提供时由 normalize() 补空串）；
        # 仅在「非空但枚举非法」时才报错。category 无枚举约束，非空即合法。
        if meta["difficulty"] and meta["difficulty"] not in DIFFICULTY_ENUM:
            raise ValueError(
                f"query_meta.difficulty must be one of {DIFFICULTY_ENUM}, got {meta['difficulty']!r}"
            )
        if meta["accuracy"] and meta["accuracy"] not in ACCURACY_ENUM:
            raise ValueError(
                f"query_meta.accuracy must be one of {ACCURACY_ENUM}, got {meta['accuracy']!r}"
            )
        qo = str(meta.get("query_origin", "")).strip()
        if not qo:
            raise ValueError("query_meta.query_origin is empty (set via compute_machine_id)")
        if not qo.startswith("sha256:"):
            raise ValueError("query_meta.query_origin must start with 'sha256:'")
        hexpart = qo[len("sha256:"):]
        if len(hexpart) != 64 or any(ch not in "0123456789abcdef" for ch in hexpart):
            raise ValueError("query_meta.query_origin must be 'sha256:' + 64 hex chars")
        if not self.original_question or not self.original_question.strip():
            raise ValueError("required field 'original_question' is empty")
        # draft_answer 允许为空，不做校验
    def to_payload(self) -> Dict[str, Any]:
        self.normalize()  # 出站前自愈：任何外发路径都先补全缺失/非法字段
        self.validate()  # 契约校验前置：经自愈后此处应当通过
        # 仅发送 3 变量（query_meta / original_question / draft_answer）：服务端 GraphInput
        # 只接收这三字段；question_profile / confirmation / tone_profile / memory_context
        # 保留在 RefineRequest 内但不再外发（服务端未实现，外发徒增数据面且 SkillSpector
        # 标"超过 3 变量契约"；待服务端补齐 v1.6 字段后再恢复发送）。
        return {
            "query_meta": self.query_meta,
            "original_question": self.original_question,
            "draft_answer": self.draft_answer,
        }
class Refiner(ABC):
    @abstractmethod
    def refine(self, req: RefineRequest, timeout: float = 60.0) -> str:
        """返回最终答案（服务器精校结果，或兜底回退的 draft_answer）。"""
        ...


class CozeRefiner(Refiner):
    """扣子服务器精校（唯一精校后端）：外发 3 变量，≤timeout 秒回收 final_answer；异常兜底草稿。

    超时策略（2026-08-16）：默认 timeout=60s；complex / 模板类问题放宽到 long_timeout
    （默认 120s）——服务端 full_analysis 完整输出模式（模板归纳 / 长文档生成）耗时长，
    60s 会被提前截断。服务端 main.py TIMEOUT_SECONDS=900，不会先于客户端砍断，放宽安全。
    由 build_refiner() 始终实例化。
    """

    def __init__(self, endpoint: str, token_env: str = "CT_ADVISOR_COZE_TOKEN",
                 timeout: float = 60.0, long_timeout: float = 120.0,
                 answer_mode: str = "fast", race_window: float = 2.0):
        self.endpoint = endpoint
        self.token_env = token_env
        self.timeout = timeout
        # long_timeout：complex / 模板类问题的等待上限（默认 120s）；其余问题用 timeout（60s）。
        # 详见 _resolve_timeout() / _is_long_running()。
        self.long_timeout = long_timeout
        # answer_mode 已固定为 fast（2026-08-05 删除 precise）；按难度分流：
        #   simple/middle = race 竞速（早发 / 速度优先，详见 refine_fire_only + collect_race）：
        #     agent 在 step 2 后台调用 --fire-only（draft_answer 留空、difficulty/category/accuracy 未提供→补空串），
        #     Coze 用**完整** HTTP 超时独立分析 original_question（默认 60s；complex/模板类走 long_timeout=120s），
        #     成功后写入 race 缓存文件；agent 在 step 3 并行写本地草稿 + 调用 --collect
        #     [--wait race_window] 收集：缓存命中（Coze 在 step 3→step 4 间已返回）→ 采用 Coze
        #     （中断本地、Coze 胜出）；否则直接采用本地草稿（速度优先——本地秒级先出、Coze 实测
        #     9~25s 慢，常态本地胜出）。
        #   complex/vague = 串行：前台等待 Coze 完整返回（单次调用 refine()；复杂/模板类 timeout=long_timeout 默认120s，其余 60s），
        #     且必须把本地已生成的 draft_answer 一并发送（作为 Coze 参考）。
        self.answer_mode = "fast"  # 2026-08-05 删除 precise，仅保留 fast 单一模式
        self.race_window = race_window  # race 竞速：step 4 收集 Coze 后台结果的等待上限（秒）；超时即放弃、用本地

    # ------------------------------------------------------------------ #
    # 条件化超时（2026-08-16）：complex / 模板类问题等待上限放宽到 long_timeout
    # （默认 120s）；其余问题维持默认 timeout（60s）。复杂/模板类问题服务端
    # full_analysis 走完整输出模式，生成耗时长，60s 会被提前截断 → 放宽。
    # 服务端 main.py TIMEOUT_SECONDS=900，不会先于客户端砍断，放宽安全。
    # ------------------------------------------------------------------ #
    _TEMPLATE_TOKENS = ("template", "模板", "doc", "document", "规范", "spec")

    def _is_long_running(self, req: "RefineRequest") -> bool:
        """长任务判定：complex 难度，或 category 命中模板类标记。

        长任务走服务端 full_analysis 完整输出模式（模板归纳 / 长文档生成），生成耗时长，
        需用 long_timeout（默认 120s）而非默认 60s。
        - difficulty == "complex"：明确长任务（串行路径前台等 Coze 完整返回）。
        - category（str 或 list）小写后含模板类 token：模板/文档/规范类问题。
        """
        meta = req.query_meta if isinstance(req.query_meta, dict) else {}
        diff = str(meta.get("difficulty", "")).strip().lower()
        if diff == "complex":
            return True
        cat = meta.get("category", "")
        if isinstance(cat, list):
            cat = " ".join(str(c) for c in cat)
        cat = str(cat).lower()
        return any(tok in cat for tok in self._TEMPLATE_TOKENS)

    def _resolve_timeout(self, req: "RefineRequest", timeout: Optional[float]) -> float:
        """解析本次 Coze 调用的有效超时：

        - 调用方显式传入 timeout → 优先采用（保留可覆盖旧行为）；
        - 否则长任务（complex / 模板类）→ long_timeout（默认 120s）；
        - 其余 → 默认 timeout（60s）。
        """
        if timeout is not None:
            return float(timeout)
        if self._is_long_running(req):
            return self.long_timeout
        return self.timeout

    def refine(self, req: RefineRequest, timeout: float = None) -> RefineResult:
        # 依赖保障：在出站 try 之外执行。缺失且自动安装失败 → 向上抛 MissingDependencyError，
        # 由 refine_answer.py 显式退出（绝不静默回退草稿，否则用户误以为答案经 Coze 精校）。
        _ensure_requests()
        timeout = self._resolve_timeout(req, timeout)
        # 全量直发（2026-08-14）：不再按难度分流，一律单次转发 Coze，返回结构化结果。
        # 兼容旧调用方：仍可通过 .final_answer 取文本；旧 fire-only/collect（race）保留不删。
        return self.refine_forward(req, timeout)

    def refine_fire_only(self, req: RefineRequest) -> str:
        """Race 早发模式（agent 在 step 3 调用，对应 SKILL.md step 3 Fire Gate）。

        与 ``refine()``（单发、draft 作兜底）不同，此方法：
          - 仅基于 ``original_question`` 独立分析 Coze
            （``draft_answer`` 留空不发送——调用方此时草稿尚未写出）；
          - HTTP 超时用 **完整** 时长（默认 60s；complex/模板类走 long_timeout=120s，不给 Coze 强加短帽，
            恢复 ops.md 文档意图）；
          - 成功后把 Coze 结果写入 race 缓存文件（供 step 4 ``--collect`` 读取）；
            超时 / 网络 / 解析异常返回**空串**且不写缓存——
            真正的兜底由 agent 在 step 4 用自己的本地草稿完成（此处不回退 draft，
            因为 step 3 时草稿为空，回退会得到空白答案）。

        agent 在 step 2 后台调用此法（run_in_background），step 3 并行写本地草稿 + 
        用 ``--collect`` 读取缓存：命中则 Coze 胜出、中断本地；否则用本地草稿（速度优先）。
        """
        _ensure_requests()
        coze_req = copy.copy(req)
        coze_req.draft_answer = ""
        cache = self._race_cache_path(req)
        try:
            text = self._call_coze(coze_req, self._resolve_timeout(coze_req, None))
        except MissingDependencyError:
            raise  # 致命依赖错误，向上传播（由 refine_answer.py 显式退出）
        except Exception:  # noqa: BLE001
            return ""
        if text:
            try:
                cache.write_text(text, encoding="utf-8")
            except Exception:
                pass
        return text

    # ------------------------------------------------------------------ #
    # race 缓存（step 3 写、step 4 读）——仅缓存 Coze 的「结果」，非 payload
    # （payload 仍走 stdin heredoc 内存管道，遵循 ops.md 禁止落盘规则；此缓存是
    # fire/collect 双调用跨进程传递 Coze 结果的必要机制，属显式例外）。
    # ------------------------------------------------------------------ #
    @staticmethod
    def _race_cache_dir() -> "Path":
        from pathlib import Path as _P
        import time as _t
        d = _P(__file__).resolve().parent.parent / ".coze_race_cache"
        d.mkdir(parents=True, exist_ok=True)
        # 轻量清理：删除超过 60 分钟的陈旧缓存（race collect 在数秒内完成，旧文件无用）
        try:
            now = _t.time()
            for f in d.iterdir():
                if f.is_file() and now - f.stat().st_mtime > 3600:
                    try:
                        f.unlink()
                    except Exception:
                        pass
        except Exception:
            pass
        return d

    def _race_cache_path(self, req: RefineRequest) -> "Path":
        """按 original_question + query_meta 生成确定性缓存路径（同 payload 同路径）。"""
        key = hashlib.sha256(
            (req.original_question + "|"
             + json.dumps(req.query_meta, ensure_ascii=False, sort_keys=True)).encode("utf-8")
        ).hexdigest()[:24]
        return self._race_cache_dir() / f"{key}.txt"

    def collect_race(self, req: RefineRequest, wait: float = None) -> str:
        """Race 收集（agent 在 step 4 调用，对应 ``--collect``）。

        读取 step 3 ``refine_fire_only`` 写入的 race 缓存：
          - 缓存命中（Coze 已在 step 3→step 4 间返回）→ 返回 Coze 结果（Coze 胜出、中断本地）；
          - 未命中 → 至多轮询 ``wait`` 秒（默认 ``self.race_window``）；仍无结果 → 返回空串
            （本地草稿胜出，agent 直接 ship 本地、不空等 Coze）。
        """
        import time
        wait = self.race_window if wait is None else wait
        cache = self._race_cache_path(req)
        deadline = time.time() + max(0.0, wait)
        while True:
            if cache.exists():
                try:
                    return cache.read_text(encoding="utf-8")
                except Exception:
                    return ""
            if time.time() >= deadline:
                return ""
            time.sleep(0.1)

    def _call_coze(self, req: RefineRequest, timeout: float) -> RefineResult:
        """真正发起一次 Coze 调用；任何失败都向上抛（由调用方决定回退/退出）。

        返回结构化 RefineResult（2026-08-14 全量直发改造）：
          - 普通路径：final_answer = Coze 答案；need_tool = None
          - need_tool 路径：final_answer = Coze 草稿（缝合基底）；need_tool/params 填充
          - 缓存命中：cache_hit=True，final_answer=cached_answer

        requests 已在 refine() 经 _ensure_requests() 保障可用。
        """
        import requests  # 延迟导入：仅在真正出站时才需要
        from .sanitize import sanitize

        # 保留 draft_answer 中的 <source skill="xxx"> 标签，原样发给 coze。
        # coze prompt 已配置为：识别 <source> 标签 → 跳过标记段落（不修改、不验证）。
        # sanitize() 只处理 PII（身份证/手机号/邮箱），不伤害 XML 标签。
        payload = sanitize(req.to_payload())  # 出站前脱敏（ct-base §11）
        # token 解析：统一从 adapters/coze_token_embedded.py 内嵌 obfuscated blob 取（XOR+base64 公开凭据，无参 get_token()）
        token = get_token()
        _headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(
                self.endpoint, json=payload, headers=_headers, timeout=timeout,
            )
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError) as e:
            # 系统代理残留（Windows：HTTP_PROXY/HTTPS_PROXY 指向无监听端口）→ requests 走死代理
            # → WinError 10061。自动绕过系统代理直连重试一次：直连可达即恢复（本端点实测直连正常）；
            # 直连也不可达则继续抛给上层 fallback。
            try:
                sys.stderr.write(
                    f"[ct-advisor] 代理连接失败({type(e).__name__})，尝试绕过系统代理直连重试...\n"
                )
            except Exception:  # noqa: BLE001
                pass
            resp = requests.post(
                self.endpoint, json=payload, headers=_headers, timeout=timeout,
                proxies={"http": None, "https": None},
            )
        # 显式暴露鉴权/服务错误：4xx/5xx 不应被上层 except 静默成「超时/没发」
        # （2026-08-08 加固：此前 TypeError 被静默吞掉，误判为未发送）
        if resp.status_code == 401:
            try:
                sys.stderr.write(t("error.coze_401") + "\n")
            except Exception:
                pass
        resp.raise_for_status()
        data = resp.json()
        # 全量直发（2026-08-14）：解析结构化返回，透出 need_tool 分支
        final = data.get("final_answer") or req.draft_answer
        result = RefineResult(
            final_answer=strip_display_tags(final),
            cached_answer=data.get("cached_answer") or "",
            cache_hit=bool(data.get("cache_hit", False)),
            need_tool=data.get("need_tool") or None,
            params=data.get("params") or {},
            run_id=str(data.get("run_id") or ""),
        )
        return result

    def refine_forward(self, req: RefineRequest, timeout: float = None) -> RefineResult:
        """全量直发主链路（2026-08-14）：单次调用 Coze，返回结构化结果。

        与旧 serial 的差异：
          - 不做难度分流（所有问题一律直发，difficulty 由本地 normalize 兜底 complex）；
          - 返回 RefineResult（可透出 need_tool 执行卡）而非纯文本；
          - 失败/超时仍回退（final_answer=req.draft_answer），由调用方判定走本地兜底。

        本地大模型原则上不回答——本方法只负责「转发 + 结果结构化」，不生成草稿。
        """
        _ensure_requests()
        timeout = self._resolve_timeout(req, timeout)
        try:
            return self._call_coze(req, timeout)
        except MissingDependencyError:
            raise  # 致命依赖错误，向上传播
        except Exception as e:  # noqa: BLE001
            self._log_fallback(e, timeout)
            return RefineResult(final_answer=req.draft_answer, need_tool=None)

    def _refine_serial(self, req: RefineRequest, timeout: float) -> RefineResult:
        """⚠️ 已废弃（2026-08-14 全量直发改造）：保留仅为旧调用方兼容，返回 RefineResult。

        串行路径（serial）：前台串行等待 Coze 完整返回（直到 timeout）；超时/失败才回退草稿。
        """
        try:
            return self._call_coze(req, timeout)
        except MissingDependencyError:
            raise  # 致命依赖错误，向上传播
        except Exception as e:  # noqa: BLE001
            self._log_fallback(e, timeout)
            return RefineResult(final_answer=req.draft_answer, need_tool=None)

    @staticmethod
    def _log_fallback(exc: Exception, timeout: float) -> None:
        """回退日志：仅打印异常类型与超时窗口，绝不输出 token / payload / draft 内容。"""
        try:
            sys.stderr.write(
                t("error.fallback_local", reason=type(exc).__name__, timeout=timeout) + "\n"
            )
        except Exception:
            pass
