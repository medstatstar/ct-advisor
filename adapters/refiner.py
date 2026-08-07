"""答案精校适配层（第 4 个 seam）：本地草稿 → 外发 3 变量 → 回收最终答案。

设计要点（沿用 v0.8.2 审计后确立的「安全默认」范式）：
- CozeRefiner 是**唯一**的精校后端：将 3 变量 POST 到扣子服务器，≤timeout 秒回收 final_answer；
  任何超时 / 网络 / 解析 / 字段缺失异常都优雅回退到 draft_answer（绝不丢答案、绝不报错给用户）。
- 不再有「local 精校模式」：答案精校经唯一的 `fast` 模式控制，按难度自动分流——
  simple/middle 走 **race 竞速（早发 / 速度优先）**：agent 在 **step 2** 后台调用
  `--fire-only`（仅发 difficulty/category/original_question，draft 留空、accuracy 空白→normal），
  Coze 用**完整 60s** HTTP 超时独立分析；成功后写入 race 缓存。
  agent 在 **step 3** 并行写本地草稿 + `--collect` 收集：缓存命中（Coze 先回）→ 采用
  Coze（中断本地）；否则直接采用本地草稿（速度优先——本地秒级先出、Coze 实测 9~25s 慢、
  常态本地胜出）。complex/vague 走 **串行**（前台等 Coze 完整返回、含 draft_answer 一并发送），
  两者都走 Coze、失败/超时回退本地草稿。
- 仅在真正发起出站时才 import requests，避免 phantom-outbound 误报。

外发 payload（3 变量）：
- query_meta:   dict，包含 difficulty / category / accuracy 三字段 + query_origin 机器标识
                - difficulty: 问题难度 simple | middle | complex | vague（gate-0 分流结论）
                - category:   问题类别（如 methodology:B / design / compliance:D，或匹配的 A–J 工作流）
                - accuracy:   自评准确度 good | normal（good = 精确，normal = 一般）
                - query_origin: 审计元数据——机器标识（sha256 哈希，不可逆、不含 IP/主机名明文），
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

from .coze_token import get_token


class MissingDependencyError(Exception):
    """精校所需的第三方依赖缺失（如 requests），且自动安装失败。

    该异常**不**应被 refine() 的兜底逻辑静默吞掉——调用方须显式告知用户安装，
    否则用户会误以为拿到的答案来自 Coze 精校，实则是未精校的本地草稿。
    """


def _try_install(pkg: str) -> bool:
    """用当前解释器自动安装缺失依赖；成功返回 True，任何失败返回 False。

    安全约束（供应链）：调用方传入的 pkg 必须**已固定版本**（如 ``requests==2.32.3``），
    禁止传入无版本号的裸包名，以免首次调用拉取被投毒的最新版本。
    """
    import subprocess
    import sys

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
        )
        return True
    except Exception:
        return False


def _ensure_requests():
    """确保 ``requests`` 可用：先导入；缺失则尝试自动安装；仍失败抛 MissingDependencyError。

    必须在 refine() 的出站 try 之外调用，使依赖缺失异常能向上传播、
    不被兜底逻辑静默回退为本地草稿。
    """
    try:
        import requests  # noqa: F401
        return requests
    except ImportError:
        # 固定版本安装，避免供应链投毒（见 _try_install 安全约束）
        if _try_install("requests==2.32.3"):
            import requests  # noqa: F401
            return requests
        raise MissingDependencyError(
            "缺少依赖 'requests' 且自动安装失败。请手动运行："
            'python -m pip install "requests==2.32.3"'
        )


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

# query_origin 的机器标识：sha256(hostname + 固定盐)，前缀标明算法；不可逆、不含明文。
# 固定盐仅用于命名空间隔离，非保密信息。
MACHINE_SALT = "ct-advisor-query-origin-v1"


def compute_machine_id() -> str:
    """稳定、不可逆的机器标识，由脚本在调用时自动盖章（覆盖输入，agent 不应手写）。

    同一台机器每次返回相同值（便于 Coze 侧按机器做审计/归因/限流），但拿不到真实主机名或 IP。
    """
    seed = f"{socket.gethostname()}|{MACHINE_SALT}"
    return "sha256:" + hashlib.sha256(seed.encode("utf-8")).hexdigest()


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
class RefineRequest:
    query_meta: dict = field(default_factory=dict)  # 包含 difficulty / category / accuracy / query_origin 的字典
    original_question: str = ""
    draft_answer: str = ""
    max_items: Optional[int] = None  # 已废弃且无操作：条目数量不再校验上限，统一直接发送 coze。

    def normalize(self) -> List[str]:
        """契约自愈（contract self-healing）。

        在 ``validate()`` 之前调用，将缺失/非法的可选字段补全为合法默认值，
        使 payload 在到达契约校验时一定合法——从根源上杜绝「契约校验失败 →
        静默兜底、远程根本没被调用」这一整类问题。

        自愈策略：
          - ``query_meta``：解析并补齐 / 修正枚举非法值（middle / normal），
            category 缺省补 ``general``；``query_origin`` 缺失则由脚本自动盖章
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
        if not meta.get("difficulty") or meta["difficulty"] not in DIFFICULTY_ENUM:
            meta["difficulty"] = "middle"
            changed = True
        # category：允许 string 或 string[]（多标签）；缺失补默认；多标签去重保序、不裁剪
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
            meta["category"] = cat_filtered if cat_filtered else "general"
            changed = True
        elif isinstance(cat_raw, str) and cat_raw.strip():
            pass  # 合法 string，保留
        else:
            meta["category"] = "general"
            changed = True
        if not meta.get("accuracy") or meta["accuracy"] not in ACCURACY_ENUM:
            meta["accuracy"] = "normal"
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

        除 draft_answer 允许为空外，其余字段均为必填：
          - query_meta       : 非空 dict，包含 difficulty / category / accuracy / query_origin
                               difficulty ∈ {simple, middle, complex, vague}
                               accuracy ∈ {good, normal}
                               query_origin : 非空，格式 sha256:<64 hex>（机器标识）
          - original_question  : 非空
        校验失败抛 ValueError；调用方（refine_answer.py）捕获后兜底输出 draft_answer。
        """
        # 校验 query_meta
        if not self.query_meta or not str(self.query_meta).strip():
            raise ValueError("required field 'query_meta' is empty")
        meta = _parse_query_meta(self.query_meta)
        if not meta["difficulty"]:
            raise ValueError("query_meta.difficulty is required (non-empty)")
        if meta["difficulty"] not in DIFFICULTY_ENUM:
            raise ValueError(
                f"query_meta.difficulty must be one of {DIFFICULTY_ENUM}, got {meta['difficulty']!r}"
            )
        if not meta["category"]:
            raise ValueError("query_meta.category is required (non-empty)")
        if not meta["accuracy"]:
            raise ValueError("query_meta.accuracy is required (non-empty)")
        if meta["accuracy"] not in ACCURACY_ENUM:
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

    由 build_refiner() 始终实例化。
    """

    def __init__(self, endpoint: str, token_env: str = "CT_ADVISOR_COZE_TOKEN",
                 timeout: float = 60.0, cli_token: str = None, token_path: str = None,
                 answer_mode: str = "fast", race_window: float = 2.0):
        self.endpoint = endpoint
        self.token_env = token_env
        self.timeout = timeout
        self.cli_token = cli_token
        self.token_path = token_path
        # answer_mode 已固定为 fast（2026-08-05 删除 precise）；按难度分流：
        #   simple/middle = race 竞速（早发 / 速度优先，详见 refine_fire_only + collect_race）：
        #     agent 在 step 2 后台调用 --fire-only（draft_answer 留空、accuracy 空白→normal），
        #     Coze 用**完整 60s**（self.timeout）HTTP 超时独立分析 original_question，
        #     成功后写入 race 缓存文件；agent 在 step 3 并行写本地草稿 + 调用 --collect
        #     [--wait race_window] 收集：缓存命中（Coze 在 step 3→step 4 间已返回）→ 采用 Coze
        #     （中断本地、Coze 胜出）；否则直接采用本地草稿（速度优先——本地秒级先出、Coze 实测
        #     9~25s 慢，常态本地胜出）。
        #   complex/vague = 串行：前台等待 Coze 完整返回（单次调用 refine()，timeout=60s），
        #     且必须把本地已生成的 draft_answer 一并发送（作为 Coze 参考）。
        self.answer_mode = "fast"  # 2026-08-05 删除 precise，仅保留 fast 单一模式
        self.race_window = race_window  # race 竞速：step 4 收集 Coze 后台结果的等待上限（秒）；超时即放弃、用本地

    def refine(self, req: RefineRequest, timeout: float = None) -> str:
        # 依赖保障：在出站 try 之外执行。缺失且自动安装失败 → 向上抛 MissingDependencyError，
        # 由 refine_answer.py 显式退出（绝不静默回退草稿，否则用户误以为答案经 Coze 精校）。
        _ensure_requests()
        timeout = timeout or self.timeout
        # 模式路由（2026-08-05 重构：删除 precise，仅保留难度驱动的单一 fast 模式）：
        # simple/middle → 后台竞速（race 并行，Coze 优先）；complex/vague → 前台串行（更慢但 Coze 优先）。
        # （与 SKILL.md:94 / references/ops.md:150 一致）
        diff = (req.query_meta or {}).get("difficulty", "") \
            if isinstance(req.query_meta, dict) else ""
        # 单发入口（refine_answer.py 非 --fire-only/--collect 时）：complex/vague 走此串行路径，
        # 前台等 Coze 完整返回（draft 兜底）；simple/middle 正常不走此处（agent 用 --fire-only
        # 早发 + --collect 收集）。此处对 simple/middle 也走串行仅作防御性兜底。
        return self._refine_serial(req, timeout)

    def refine_fire_only(self, req: RefineRequest) -> str:
        """Race 早发模式（agent 在 step 3 调用，对应 SKILL.md step 3 Fire Gate）。

        与 ``refine()``（单发、draft 作兜底）不同，此方法：
          - 仅基于 ``original_question`` 独立分析 Coze
            （``draft_answer`` 留空不发送——调用方此时草稿尚未写出）；
          - HTTP 超时用 **完整** ``self.timeout``（默认 60s，不给 Coze 强加短帽，
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
            text = self._call_coze(coze_req, self.timeout)
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

    def _call_coze(self, req: RefineRequest, timeout: float) -> str:
        """真正发起一次 Coze 调用；任何失败都向上抛（由调用方决定回退/退出）。

        requests 已在 refine() 经 _ensure_requests() 保障可用。
        """
        import requests  # 延迟导入：仅在真正出站时才需要
        from .sanitize import sanitize

        # 保留 draft_answer 中的 <source skill="xxx"> 标签，原样发给 coze。
        # coze prompt 已配置为：识别 <source> 标签 → 跳过标记段落（不修改、不验证）。
        # sanitize() 只处理 PII（身份证/手机号/邮箱），不伤害 XML 标签。
        payload = sanitize(req.to_payload())  # 出站前脱敏（ct-base §11）
        # token 解析优先级：CLI > env > 混淆落盘文件（详见 adapters/coze_token.py）
        token = get_token(self.cli_token, self.token_path, self.token_env)
        resp = requests.post(
            self.endpoint,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )
        data = resp.json()
        final = data.get("final_answer") or req.draft_answer
        # 展示前剥离 <source> 标签（标签仅用于 coze 端识别，用户不需要看到）
        return strip_display_tags(final)

    def _refine_serial(self, req: RefineRequest, timeout: float) -> str:
        """串行路径（serial）：前台串行等待 Coze 完整返回（直到 timeout）；超时/失败才回退草稿。
        complex/vague 走此路径（更慢，但 Coze 优先）。"""
        try:
            return self._call_coze(req, timeout)
        except MissingDependencyError:
            raise  # 致命依赖错误，向上传播
        except Exception as e:  # noqa: BLE001
            self._log_fallback(e, timeout)
            return req.draft_answer

    @staticmethod
    def _log_fallback(exc: Exception, timeout: float) -> None:
        """回退日志：仅打印异常类型与超时窗口，绝不输出 token / payload / draft 内容。"""
        try:
            sys.stderr.write(
                f"[ct-advisor][coze] FALLBACK_TO_LOCAL_DRAFT "
                f"reason={type(exc).__name__} timeout={timeout}s; "
                "not retrying coze; returning local draft_answer\n"
            )
        except Exception:
            pass
