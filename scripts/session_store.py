#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ct-advisor — 统一会话存储（会话上下文 + 答案缓存 + 幂等去重），2026-10-22

背景（来自 advisorlog 近 30 天诊断）：
  - 会话上下文曾从未被主链路注入：context_stitch.pack_history_for_coze() 虽存在，
    但 entry.py / proxy 两条真实入口都没调用它 → Coze 永远只拿到单轮问题，
    用户被迫在「承接上一轮 / 继续调研」里手工复述背景（实测 18% 提问含此类回指）。
  - answer_cache / dedup_guard 只在 refine_answer.py 的 CLI 路径生效，entry.py 与
    workbench proxy 直连 Coze 时完全绕开 → 21% 的重复发送（11 个簇）白烧云端耗时。

本模块把三类能力按 session_id 聚合到**同一存储**，entry.py 与 proxy 共用，确保跨入口一致：
  1) history      多轮问答（conversation_history），注入 payload 供 Coze 判相关性
  2) global_cache 问题指纹 → 答案（跨 session 通用，同问题同答案）
  3) dedup        同 session 近窗近似重复（difflib quick_ratio），命中直回上轮答案

存储：{ROOT}/config/session_store.json（单文件，按 session_id 分组 + 顶层 global_cache）。
并发：跨进程用文件锁（Win msvcrt / POSIX fcntl），临界区短；锁失败静默降级（不阻断主流程）。
一切异常静默回退为「不命中 / 不记录」——永不阻断主流程（与 answer_cache / dedup_guard 约定一致）。

依赖：stdlib-only（hashlib / json / os / time / difflib / pathlib）。
"""

from __future__ import annotations

import contextlib
import difflib
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE_PATH = ROOT / "config" / "session_store.json"
LOCK_PATH = ROOT / "config" / ".session_store.lock"

# ── 上下文裁剪口径（对齐 context_stitch 模式 B：OR + 24h 硬上限）─────────────
HIST_TTL_ROUNDS = 10       # 有效轮数（OR：≤10 条即保留）
HIST_TTL_SECONDS = 7200    # 软时间窗 2h（OR：2h 内全留）
HIST_HARD_CAP = 86400      # 硬上限 24h（任何超 24h 必丢）
HIST_MAX_PREV_LEN = 200    # 单条 answer_summary 上限（防膨胀）

# ── 答案缓存 ────────────────────────────────────────────────────────────────
CACHE_TTL = int(os.environ.get("CT_ADVISOR_ANSWER_TTL", "1800"))  # 默认 30 分钟

# ── 幂等去重（近窗近似重复）─────────────────────────────────────────────────
DEDUP_WINDOW = 600         # 10 分钟（覆盖实测重发间隔 12~232s）
DEDUP_SIM = 0.90           # 近似相似度阈值（quick_ratio）
DEDUP_MAX_PER_SESSION = 20 # 每 session 保留条数（滚动）


# ── 跨平台文件锁 ──────────────────────────────────────────────────────────────
def _lock_ctx():
    """返回上下文管理器：进入临界区前获取文件锁，退出释放。失败静默降级。"""
    if sys.platform.startswith("win"):
        import msvcrt

        @contextlib.contextmanager
        def _cm():
            fh = None
            try:
                fh = open(LOCK_PATH, "a+")
                msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
                yield
            except Exception:  # noqa: BLE001
                yield
            finally:
                try:
                    if fh is not None:
                        fh.seek(0)
                        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                        fh.close()
                except Exception:  # noqa: BLE001
                    pass
        return _cm()
    else:
        import fcntl

        @contextlib.contextmanager
        def _cm():
            fh = None
            try:
                fh = open(LOCK_PATH, "a+")
                fcntl.flock(fh, fcntl.LOCK_EX)
                yield
            except Exception:  # noqa: BLE001
                yield
            finally:
                try:
                    if fh is not None:
                        fcntl.flock(fh, fcntl.LOCK_UN)
                        fh.close()
                except Exception:  # noqa: BLE001
                    pass
        return _cm()


def _load() -> dict:
    try:
        with open(STORE_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(data: dict) -> None:
    try:
        STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = STORE_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, STORE_PATH)  # 原子替换，避免半写损坏
    except Exception:  # noqa: BLE001
        pass


# ── 指纹 / 相似度 ──────────────────────────────────────────────────────────────
def cache_key(question: str, doc_context: str = "", difficulty: str = "",
              output_format: str = "") -> str:
    """问题指纹。同问题 + 同附件载荷 + 同难度 + 同输出形态 → 同 key。

    2026-10-22：纳入 output_format——doc 与 auto 答案必须分区缓存，否则选 doc 会命中
    auto 缓存拿到被截断的短文（见 answer_length_format_deviation_20261022.md F2）。
    """
    raw = f"{(question or '').strip()}|{doc_context or ''}|{difficulty or ''}|{output_format or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _similar(a: str, b: str) -> float:
    a, b = (a or "").strip(), (b or "").strip()
    if not a or not b:
        return 0.0
    if abs(len(a) - len(b)) > max(len(a), len(b)) * 0.5:
        return 0.0  # 长度悬殊过大 → 0（防长文 vs 短文误判）
    return difflib.SequenceMatcher(None, a, b).quick_ratio()


def _prune_history(history: list, now: float) -> list:
    """按「OR + 24h 硬上限」语义裁剪（与 context_stitch.prune_history 一致）。"""
    if not history:
        return []
    kept = []
    for h in history:
        h = h or {}
        ts = h.get("ts")
        if ts is None:
            if len(kept) < HIST_TTL_ROUNDS:
                kept.append(h)
            continue
        try:
            age = now - float(ts)
        except (TypeError, ValueError):
            if len(kept) < HIST_TTL_ROUNDS:
                kept.append(h)
            continue
        if age > HIST_HARD_CAP:
            continue
        if age <= HIST_TTL_SECONDS:
            kept.append(h)
        elif len(kept) < HIST_TTL_ROUNDS:
            kept.append(h)
    return kept


def _summarize(answer: str, max_len: int = HIST_MAX_PREV_LEN) -> str:
    """从整段答案取首段摘要（无 LLM，规则化），供 Coze 注入历史上下文。"""
    ans = (answer or "").strip()
    if not ans:
        return ""
    first_para = ans.split("\n\n")[0].strip()
    if len(first_para) > max_len:
        first_para = first_para[:max_len] + "…"
    return first_para


# ── 对外 API ───────────────────────────────────────────────────────────────────
def history(session_id: str, now: float = None) -> list:
    """导出有界历史给 Coze（conversation_history 字段）。

    返回 [{question, answer_summary}, ...] 时间升序；无活跃会话或空 → []。
    session_id 为空 → 视为无会话（单轮模式），返回 []（不退化旧行为）。
    """
    if not session_id:
        return []
    if now is None:
        now = time.time()
    with _lock_ctx():
        data = _load()
        sess = (data.get("sessions") or {}).get(session_id)
        if not sess:
            return []
        raw_hist = sess.get("history") or []
        pruned = _prune_history(raw_hist, now)
        out = []
        for h in pruned:
            h = h or {}
            q = (h.get("q") or "").strip()
            ans = (h.get("answer_summary") or "").strip()
            if not q and not ans:
                continue
            out.append({"question": q, "answer_summary": ans})
        return out


def record(session_id: str, question: str, answer: str,
           answer_summary: str = "", difficulty: str = "",
           doc_context: str = "", output_format: str = "") -> None:
    """记录一轮真实产生的问答（出站成功后调用，非命中短路时）。

    - 写入 history（供后续轮次注入上下文）
    - 写入 global_cache（问题指纹 → 答案，跨 session 复用）
    - 写入本 session dedup 库（近窗近似重复短路）
    session_id 为空 → 仍写 global_cache，但不写 history/dedup（单轮模式）。
    任何异常静默忽略。
    """
    if not (answer or "").strip():
        return
    now = time.time()
    summ = (answer_summary or "").strip() or _summarize(answer)
    key = cache_key(question, doc_context, difficulty, output_format)
    with _lock_ctx():
        data = _load()
        gcache = data.setdefault("global_cache", {})
        gcache[key] = {"ts": now, "answer": answer}
        # 全局缓存只保留最近 200 条，防无限膨胀
        if len(gcache) > 200:
            oldest = sorted(gcache.items(), key=lambda kv: kv[1].get("ts", 0))[:50]
            for k, _ in oldest:
                gcache.pop(k, None)

        if session_id:
            sessions = data.setdefault("sessions", {})
            sess = sessions.setdefault(session_id, {"history": [], "dedup": [], "ts": 0})
            # history
            sess["history"] = _prune_history(
                sess.get("history", []) + [{
                    "ts": now, "q": (question or "").strip(),
                    "answer_summary": summ,
                }], now)
            sess["history"] = sess["history"][-HIST_TTL_ROUNDS:]
            # dedup 库
            dup = sess.get("dedup", [])
            dup.append({"ts": now, "q": (question or "").strip(),
                        "answer": answer, "key": key, "fmt": output_format})
            dup = [e for e in dup if now - (e.get("ts") or 0) <= DEDUP_WINDOW]
            sess["dedup"] = dup[-DEDUP_MAX_PER_SESSION:]
            sess["ts"] = now
        _save(data)


def cache_get(question: str, doc_context: str = "", difficulty: str = "",
              output_format: str = "") -> str:
    """全局精确指纹缓存命中 → 返回答案；否则空串。"""
    key = cache_key(question, doc_context, difficulty, output_format)
    if not key:
        return ""
    try:
        data = _load()
        obj = (data.get("global_cache") or {}).get(key)
        if not obj:
            return ""
        if time.time() - float(obj.get("ts") or 0) > CACHE_TTL:
            return ""
        return obj.get("answer") or ""
    except Exception:  # noqa: BLE001
        return ""


def dedup_check(session_id: str, question: str,
                window: int = DEDUP_WINDOW, output_format: str = "") -> tuple:
    """同 session 近窗近似重复检测。

    返回 (is_dup, prev_answer, secs_ago)：is_dup 且 prev_answer 非空 → 调用方应短路直回。
    session_id 为空 → 不查（单轮模式），返回 (False, None, 0)。
    output_format：仅当两侧均显式指定且不一致时跳过（doc 不短路到 auto 答案）。
    """
    if not session_id:
        return False, None, 0
    try:
        now = time.time()
        data = _load()
        sess = (data.get("sessions") or {}).get(session_id)
        if not sess:
            return False, None, 0
        best, best_sim = None, 0.0
        for e in sess.get("dedup", []):
            ts = e.get("ts") or 0
            if now - ts > window:
                continue
            # 输出形态不同 → 视为不同请求（doc 不应复用 auto 答案）
            if output_format and e.get("fmt") and e.get("fmt") != output_format:
                continue
            sim = _similar(question or "", e.get("q") or "")
            if sim >= DEDUP_SIM and sim > best_sim:
                best_sim, best = sim, e
        if best and (best.get("answer") or "").strip():
            secs = max(0, int(now - (best.get("ts") or now)))
            return True, best["answer"], secs
        return False, None, 0
    except Exception:  # noqa: BLE001
        return False, None, 0


def clear_session(session_id: str) -> None:
    """清空某 session 的 history + dedup（保留 global_cache）。新会话时调用。"""
    if not session_id:
        return
    with _lock_ctx():
        data = _load()
        sess = (data.get("sessions") or {}).pop(session_id, None)
        if sess is not None:
            _save(data)


# ── 离线自测 ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile

    _tmp = tempfile.mkdtemp()
    os.environ["CT_ADVISOR_DATA_ROOT"] = _tmp  # 不污染生产（本模块用固定 STORE_PATH，
    # 故额外覆盖：自测时改 STORE_PATH 指向临时目录）
    # 直接改模块级常量指向临时目录（仅自测用）
    STORE_PATH = Path(_tmp) / "session_store.json"
    LOCK_PATH = Path(_tmp) / ".session_store.lock"

    sid = "sha256:selftest"
    q1 = "多中心研究中如果一个中心突然要退出怎么处理"
    q1b = "多中心研究如果一个中心突然退出怎么处理"   # 近似重复
    q2 = "样本量怎么估算"
    ans1 = "答：先评估对统计效能影响，与申办方/CRO 协商退出或保留已入组数据，按方案偏离处理并上报伦理。"
    ans2 = "答：按主要终点、效应量、α、power 估算。"

    # history 初始空
    assert history(sid) == [], "history 初始应为空"
    # record 一轮
    record(sid, q1, ans1)
    assert len(history(sid)) == 1, "record 后 history 应有 1 条"
    # dedup 近似命中
    hit, prev, ago = dedup_check(sid, q1b)
    assert hit and prev == ans1, "近窗近似重复应命中"
    # 精确缓存
    assert cache_get(q1) == ans1, "全局精确缓存应命中"
    assert cache_get(q2) == "", "不同问题不应命中"
    # 第二轮 record 后 history 增至 2
    record(sid, q2, ans2)
    assert len(history(sid)) == 2, "两轮后 history 应为 2"
    # 清空 session
    clear_session(sid)
    assert history(sid) == [], "clear 后 history 应空"
    assert cache_get(q1) == ans1, "clear 不清全局缓存"
    print("session_store self-test: ALL PASSED")
