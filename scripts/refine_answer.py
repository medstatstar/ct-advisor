#!/usr/bin/env python3
"""ct-advisor answer refiner entry point (called by the agent).

Reads 3 variables (JSON). Source priority (in-memory pipeline first, zero temp files):
  1) --payload-inline <JSON string> — zero file I/O, the agent's preferred path
  2) stdin pipe `echo '{...}' | python refine_answer.py` — no temp files, cross-platform safe
  3) positional arg (file path, legacy, avoid when possible)
Variables: query_meta (incl. query_origin machine id), original_question, draft_answer
Calls build_refiner().refine() to get the final answer, prints it to stdout.

query_meta is a JSON string with three fields:
  - difficulty: simple | middle | complex | vague
  - category:   question category (e.g. methodology:B / design / compliance:D)
  - accuracy:   self-rated accuracy good | normal (good = precise, normal = generic)

Robustness: any exception falls back to printing draft_answer and exits 0, so the agent
always gets a usable answer and the conversation never breaks due to a script crash.
By default it calls the Coze refiner (single call, 60s timeout; on Coze timeout/error it degrades to the local draft as a fault fallback — there is no local-only mode).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Set

# 代码旁路模式（--ship）最终答案定界符：脚本输出唯一权威答案，agent 只做原样透传。
ANSWER_START = "<<<CT_ANSWER_START>>>"
ANSWER_END = "<<<CT_ANSWER_END>>>"
NEED_PARAMS_MARKER = "<<<CT_NEED_PARAMS>>>"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from adapters import build_refiner, RefineRequest, RefineResult, MissingDependencyError
from scripts.i18n import t  # noqa: E402  (user-facing prompts EN/ZH, locale-resolved)
# 复用入口预判（模式 B 前端高置信预取）：--ship 的 need_tool 分支用其补全真实参数，
# 避免纯 --ship 路径下任意 need_tool 都 100% 落到 need_params（Coze 仅判类别、不抽真实入参）。
from route_tool import predict as _predict_tool  # noqa: E402

def _load_auto_approve_endpoints(config_path: str) -> Set[str]:
    """从 config.json 加载 auto_approve_endpoints 白名单。"""
    try:
        cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
        return set(cfg.get("auto_approve_endpoints", []) or [])
    except Exception:
        return set()


def _get_endpoint_from_config(config_path: str) -> str:
    """从 config.json 读取 refiner.endpoint。"""
    try:
        cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
        return (cfg.get("refiner", {}) or {}).get("endpoint", "")
    except Exception:
        return ""


# Session-scoped in-memory authorization (resets per script invocation).
_SESSION_AUTHORIZED_ENDPOINTS: Set[str] = set()


def _check_outbound_authorization(endpoint: str, config_path: str) -> bool:
    """检查出站授权：返回 True 表示已授权可继续，False 表示未授权需拦截。"""
    # 1. 会话内存中已授权
    if endpoint in _SESSION_AUTHORIZED_ENDPOINTS:
        return True
    # 2. config.json 白名单中
    if endpoint in _load_auto_approve_endpoints(config_path):
        return True
    # 3. 未授权：输出机器信号 + 随 locale 切换的用户提示，agent 应展示给用户确认
    sys.stderr.write(
        f"[ct-advisor][AUTH-BLOCK] outbound to {endpoint} requires user confirmation.\n"
        f"\n{t('auth.coze_outbound', endpoint=endpoint)}\n"
    )
    return False

# On Chinese Windows the console defaults to cp936:
#  - stdin decoded as cp936 would corrupt the UTF-8 JSON piped in (the agent's main usage is piping JSON);
#  - stdout encoded as cp936 may raise UnicodeEncodeError on CJK/emoji/℃, and the consumer decoding as UTF-8 would get garbage.
# Fix all three standard streams to UTF-8 for consistent cross-platform, cross-console encoding behaviour.
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass


def _detect_lang(text: str) -> str:
    """按 CJK 占比检测提问语言（≥15% → 'zh-CN'，否则 'en'）。

    2026-08-21：语言参数化——表格表头 / 来源标签随提问语言切换，
    保证英文提问交付全英文（结构化单元格数据保持原文不翻译）。
    """
    if not text:
        return "zh-CN"
    import re as _re
    cjk = len(_re.findall(r"[\u4e00-\u9fff]", text))
    return "zh-CN" if cjk >= max(1, len(text) * 0.15) else "en"


def _render_registry_landscape(res: dict, lang: str = "zh-CN") -> str:
    """把 ct-registry 聚合结果（landscape）渲染为用户友好 markdown 表格。

    2026-08-21：README 示例 2 实测——裸 JSON 块对用户不友好；改为
    「试验数汇总 + 分期/地域/申办方 三张两列表格 + xlsx 提示」。
    **表头/文案随提问语言（lang）切换，单元格检索数据（PHASE 3 / United States /
    Novo Nordisk 等）保持原文不翻译**（用户明确口径，2026-08-21）。
    """
    ls = res.get("landscape") or {}
    parts: list = []
    zh = lang == "zh-CN"
    n = ls.get("n_trials")
    if n is not None:
        raw = ls.get("raw_total")
        if zh:
            dedup = f"（去重后 {n} 条原始记录）" if raw is not None and raw != n else ""
            parts.append(f"**检索到 {n} 项注册试验**{dedup}")
        else:
            dedup = f" ({n} raw records)" if raw is not None and raw != n else ""
            parts.append(f"**{n} registered trials found**{dedup}")
    for field, (zh_t, en_t) in (
            ("phase_mix", ("**分期分布**", "**Phase distribution**")),
            ("region_mix", ("**地域分布**", "**Region distribution**")),
            ("top_sponsors", ("**主要申办方**", "**Top sponsors**"))):
        arr = ls.get(field)
        if isinstance(arr, list) and arr:
            rows = "\n".join(
                f"| {str(it.get('k', ''))} | {it.get('n', '')} |"
                for it in arr if isinstance(it, dict))
            title = zh_t if zh else en_t
            head = "| 类别 | 数量 |" if zh else "| Category | Count |"
            parts.append(f"{title}\n\n{head}\n|---|---|\n{rows}")
    excel = res.get("excel")
    if excel:
        parts.append(
            f"📊 完整试验清单（名称 / 阶段 / 地区 / 申办方）已导出：`{excel}`"
            if zh else
            f"📊 Full trial list (name / phase / region / sponsor) exported: `{excel}`")
    note = res.get("note")
    if note:
        parts.append(f"> {note}")
    if parts:
        return "\n\n".join(parts)
    # 无结构化字段可渲染时回退裸 JSON
    try:
        return json.dumps(res, ensure_ascii=False, indent=2)
    except Exception:
        return str(res)


def _render_skill_result(result, lang: str = "zh-CN") -> str:
    """把 need_tool 技能主产物渲染为可读文本（确定性，无 LLM）。"""
    # 2026-08-21：ct-registry 聚合 → 用户友好表格（README 示例 2 实测，替代裸 JSON）
    if isinstance(result, dict) and isinstance(result.get("landscape"), dict):
        return _render_registry_landscape(result, lang)
    if isinstance(result, (dict, list)):
        try:
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception:
            return str(result)
    return str(result) if result is not None else ""


def _merge_answer(coze_answer: str, tool_out: dict, lang: str = "zh-CN") -> str:
    """确定性缝合：Coze 原答案 + 补充信息（含来源标签）。纯代码，不依赖 LLM。

    lang（2026-08-21）：来源标签 / 文案随提问语言切换（zh-CN → 中文，en → 英文），
    结构化数据内容（表格单元格等）保持原文。
    """
    tool = tool_out.get("tool") or "ct-tool"
    status = tool_out.get("status")
    if status == "ok":
        res = _render_skill_result(tool_out.get("result"), lang)
        if lang == "zh-CN":
            return f"{coze_answer}\n\n---\n\n## 补充信息（来源：{tool}）\n\n{res}"
        return f"{coze_answer}\n\n---\n\n## Supplementary data (Source: {tool})\n\n{res}"
    if status == "need_params":
        mp = tool_out.get("result") or {}
        missing = mp.get("missing", []) if isinstance(mp, dict) else []
        miss_txt = "\n".join(f"- {m}" for m in missing) or "(详见执行器输出)"
        if lang == "zh-CN":
            return (f"{coze_answer}\n\n---\n\n{NEED_PARAMS_MARKER}\n"
                    f"以下补充信息需要先由你向用户追问并补齐参数后才能获取：\n{miss_txt}")
        return (f"{coze_answer}\n\n---\n\n{NEED_PARAMS_MARKER}\n"
                f"Additional data requires you to ask the user for these missing params first:\n{miss_txt}")
    err = tool_out.get("result") or ""
    if lang == "zh-CN":
        return (f"{coze_answer}\n\n---\n\n## 补充信息获取失败（来源：{tool}）\n\n"
                f"Coze 建议调用的本地技能执行出错，已保留 Coze 原答案：\n{err}")
    return (f"{coze_answer}\n\n---\n\n## Supplementary data retrieval failed (Source: {tool})\n\n"
            f"The local skill Coze requested failed; Coze's original answer is kept:\n{err}")


def _run_handle_need_tool(card: dict) -> dict:
    """在代码内机械执行 need_tool 执行卡（subprocess 调 handle_need_tool.py）。"""
    try:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "handle_need_tool.py"),
             "--card", json.dumps(card, ensure_ascii=False)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=300,
        )
        if proc.returncode != 0:
            return {"tool": card.get("need_tool"), "status": "error",
                    "result": f"rc={proc.returncode}: {(proc.stderr or '')[:1500]}"}
        return json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        return {"tool": card.get("need_tool"), "status": "error",
                "result": "技能执行超时（>300s）"}
    except Exception as e:  # noqa: BLE001
        return {"tool": card.get("need_tool"), "status": "error",
                "result": f"{type(e).__name__}: {e}"}


def _emit_wrapped(text: str) -> None:
    """把最终答案用定界符包裹 + sha256 校验和输出，供 agent 原样透传并自检。"""
    checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    sys.stdout.write(f"{ANSWER_START}\n{text}\n{ANSWER_END}\nchecksum: {checksum}\n")


def _extract_draft(raw: str) -> str:
    """Best-effort extract draft_answer from raw input, for fallback on parse failure."""
    try:
        return json.loads(raw).get("draft_answer", "") or ""
    except Exception:
        m = re.search(r'"draft_answer"\s*:\s*"((?:[^"\\]|\\.)*)"', raw, re.S)
        return m.group(1) if m else ""


def main() -> None:
    ap = argparse.ArgumentParser(description="ct-advisor answer refiner (Coze polish, single call)")
    ap.add_argument("payload", nargs="?", help="path to JSON file with the 3 variables (deprecated: use stdin or --payload-inline)")
    ap.add_argument("--payload-inline", help="inline JSON payload string (highest priority, avoids temp files)")
    ap.add_argument("--config", default=str(ROOT / "config.json"),
                     help="path to config.json (defaults to the skill package config.json, "
                          "independent of the current working directory)")
    ap.add_argument("--fire-only", action="store_true",
                    help="race early-fire mode: step 2 background call, sends only original_question, "
                         "returns Coze result or empty string (no draft fallback on Coze failure), writes race cache on success")
    ap.add_argument("--collect", action="store_true",
                    help="race collect mode: step 3 call, reads the race cache written by --fire-only; "
                         "hit returns Coze result (Coze wins, local interrupted), miss returns empty (local wins)")
    ap.add_argument("--wait", type=float, default=None,
                    help="--collect gather wait cap in seconds; defaults to config refiner.race_window")
    ap.add_argument("--forward", action="store_true",
                    help="全量直发主链路（2026-08-14）：单次调用 Coze，返回结构化 RefineResult JSON。"
                         "本地大模型原则上不回答——本模式只转发；need_tool 分支透出执行卡供本地执行技能。"
                         "失败/超时回退 draft_answer（final_answer 字段），由调用方判定本地兜底")
    ap.add_argument("--ship", action="store_true",
                    help="代码旁路主链路（2026-08-15）：单次调用 Coze，若 need_tool 则在代码内直接调 "
                         "handle_need_tool.py 执行并对结果做确定性缝合；最终答案以 <<<CT_ANSWER_START>>> "
                         "定界包裹输出。本地大模型只做原样透传（pipe），不重写/重排/补充。此模式用于跳过大模型重组。")
    ap.add_argument("--card-inline", default=None,
                    help="need_params 重试路径（与 --ship 配合）：跳过 Coze 直发，直接用给定执行卡 JSON 运行 "
                         "handle_need_tool.py 并缝合（用于补齐参数后重试，避免重复调用 Coze）")
    # P0-B 语气写作：注入 tone_matcher.py 生成的 tone_profile.json（仅风格、无事实）
    ap.add_argument("--tone", default=None,
                    help="path to tone_profile.json (from scripts/tone_matcher.py); injects style-only tone into Coze prompt")
    # P1-D 本地用户记忆：注入 memory_manager.py 维护的 ct-advisor-memory.json 上下文
    ap.add_argument("--memory", default=None,
                    help="path to ct-advisor-memory.json (from scripts/memory_manager.py); injects local user memory context")
    args = ap.parse_args()

    # --card-inline 重试路径（与 --ship 配合）：跳过 Coze 直发，直接用执行卡在代码内跑 handle_need_tool 并缝合。
    # 必须在读 payload 之前处理，避免空 stdin 触发 payload 解析回退。
    if args.card_inline:
        try:
            card = json.loads(args.card_inline)
        except Exception as e:  # noqa: BLE001
            sys.stderr.write(f"[ct-advisor] card-inline JSON 解析失败: {e}\n")
            sys.exit(1)
        coze_answer = card.get("draft_answer") or ""
        tool_out = _run_handle_need_tool(card)
        _emit_wrapped(_merge_answer(coze_answer, tool_out))
        sys.exit(0)

    # Read priority (in-memory pipeline first, zero temp files):
    #   1) --payload-inline: pass the JSON string directly, zero file I/O
    #   2) stdin pipe: `echo '{...}' | python refine_answer.py`
    #   3) file path (positional, legacy, avoid when possible)
    if args.payload_inline:
        raw = args.payload_inline
    elif args.payload:
        p = Path(args.payload)
        if not p.exists():
            # Explicit path given but missing: fail loudly, do NOT silently fall back to stdin
            # (otherwise it would hang or misread an empty payload)
            sys.stderr.write(f"[ct-advisor] payload file not found: {args.payload} / payload 文件未找到: {args.payload}\n")
            sys.exit(2)
        raw = p.read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()

    draft = _extract_draft(raw)
    try:
        obj = json.loads(raw)
        req = RefineRequest(
            query_meta=obj.get("query_meta", ""),
            original_question=str(obj.get("original_question", "")),
            draft_answer=str(obj.get("draft_answer", "")),
        )
        # P0-B 语气写作 / P1-D 本地记忆：注入 tone_profile / memory_context（CLI 优先，其次 payload 内联）。
        # 两者均为纯本地生成的风格/上下文，仅随契约外发给 Coze，符合风格硬闸与记忆 TTL 设计。
        if args.tone:
            try:
                tp = json.loads(Path(args.tone).read_text(encoding="utf-8"))
                if isinstance(tp, dict):
                    req.tone_profile = tp
                    sys.stderr.write(f"[ct-advisor] tone profile injected: {args.tone}\n")
            except Exception as e:  # noqa: BLE001
                sys.stderr.write(f"[ct-advisor] tone profile load failed: {e}\n")
        elif isinstance(obj.get("tone_profile"), dict):
            req.tone_profile = obj["tone_profile"]
        if args.memory:
            try:
                mc = json.loads(Path(args.memory).read_text(encoding="utf-8"))
                if isinstance(mc, dict):
                    req.memory_context = mc
                    sys.stderr.write(f"[ct-advisor] memory context injected: {args.memory}\n")
            except Exception as e:  # noqa: BLE001
                sys.stderr.write(f"[ct-advisor] memory context load failed: {e}\n")
        elif isinstance(obj.get("memory_context"), dict):
            req.memory_context = obj["memory_context"]
        # query_origin is auto-stamped into query_meta by normalize(); no top-level field.
        # 类型 B 追问自包含化（2026-08-15）：非 --collect 模式（真实转发路径）下，若当前问题是
        # 隐式承接追问且本地有上一轮上下文摘要，则拼接为自包含问题再转发，避免 Coze 因无上下文
        # 重复追问已给参数。纯本地代码（scripts/context_stitch.py），无 LLM、无新增出域。
        if not args.collect:
            try:
                sys.path.insert(0, str(ROOT / "scripts"))
                import context_stitch as _cs
                _orig = req.original_question or ""
                _raw_orig = _orig  # 保留原始问题（供缓存，防多轮嵌套）
                if _cs.is_followup(_orig):
                    _cache = _cs.load_cache()
                    _prev = _cache.get("summary", "")
                    if _prev and int(_cache.get("rounds", 4)) <= _cs.TTL_ROUNDS:
                        _stitched = _cs.stitch(_orig, _prev)
                        sys.stderr.write(f"[ct-advisor] follow-up stitched: {_stitched}\n")
                        req.original_question = _stitched
            except Exception as _e:  # noqa: BLE001  # 拼接失败不影响主流程
                sys.stderr.write(f"[ct-advisor] context stitch skipped: {_e}\n")
    except Exception as e:
        # JSON parse failed: distinguish --collect mode (cache lookup) from other modes
        if args.collect:
            # --collect mode: payload parse failure means the cache path cannot be located;
            # tell the agent explicitly "local wins", do NOT confuse it with "cache miss"
            sys.stderr.write(
                t("error.payload_invalid",
                  error=f"{type(e).__name__}; collect: cache path cannot be located -> LOCAL WINS, do NOT wait for Coze")
                + "\n"
            )
            sys.stdout.write("")
            sys.exit(0)
        # Other modes (fire-only / serial): cannot self-heal; warn clearly + fall back to draft
        sys.stderr.write(
            t("error.payload_invalid", error=f"{type(e).__name__} (invalid JSON)") + "\n"
        )
        sys.stdout.write(draft)
        sys.exit(0)

    # Contract self-heal: fill missing/invalid fields, eliminating the "invalid payload -> silent fallback" root cause
    heal_notes = req.normalize()
    if heal_notes:
        sys.stderr.write(
            t("error.payload_healed", notes="; ".join(heal_notes)) + "\n"
        )

    try:
        req.validate()  # Should pass after self-heal; only fails in extreme cases (both orgq and draft empty)
    except ValueError as e:
        sys.stderr.write(
            t("error.payload_invalid", error=f"contract validation failed: {e}") + "\n"
        )
        # Fallback: when the draft is also empty, emit an explicit prompt instead of a silent empty answer
        if not draft or not draft.strip():
            sys.stdout.write(t("error.empty_question") + "\n")
        else:
            sys.stdout.write(draft)
        sys.exit(0)

    if args.ship:
        # 代码旁路主链路（2026-08-15）：单次调用 Coze；need_tool 分支在代码内执行 + 确定性缝合；
        # 最终答案以 <<<CT_ANSWER_START>>> 定界包裹输出，本地大模型只做原样透传（pipe）。
        if not _check_outbound_authorization(
            _get_endpoint_from_config(args.config), args.config
        ):
            # 未授权出站：无法获取 Coze 答案，明确告知 agent 走本地兜底
            _emit_wrapped(
                "⚠️ 未授权出站到 Coze，无法获取精校答案。请基于本地知识库作答，并明确告知用户"
                "「答案未经过 Coze 精校，请谨慎使用」。"
            )
            sys.exit(0)
        try:
            result = build_refiner(config_path=args.config).refine_forward(req)
        except MissingDependencyError:
            sys.stderr.write(
                t("error.dependency_fatal",
                  cmd='python -m pip install "requests==2.32.3"') + "\n"
            )
            sys.exit(1)
        except Exception as e:  # noqa: BLE001
            # Coze 失败：无精校答案，交给本地兜底，包裹明确警告
            sys.stderr.write(
                f"[ct-advisor] ship 失败（{type(e).__name__}）：Coze 不可用，需本地兜底\n"
            )
            _emit_wrapped(
                "⚠️ 无法连接 Coze 服务，答案未经过精校。请基于本地知识库作答，并明确告知用户此警告。"
            )
            sys.exit(0)
        coze_answer = result.final_answer or ""
        need_tool = result.need_tool
        if need_tool:
            # P1 修复（2026-08-15）：Coze 仅判工具类别、不抽真实入参（只给 max/top 等默认值）。
            # 用本地 route_tool 预判补全真实参数（cond/drug/topic/test/p1/p2），覆盖 Coze 默认值，
            # 使「代码跳过大模型」在 need_tool 场景也成立——避免任意 need_tool 都 100% 弹参数追问。
            params = dict(result.params or {})
            pred = _predict_tool(req.original_question)
            if pred.get("need_tool") == need_tool:
                for k, v in (pred.get("params") or {}).items():
                    if v not in (None, ""):
                        params.setdefault(k, v)
            card = {
                "need_tool": need_tool,
                "params": params,
                "draft_answer": coze_answer,
                "original_question": req.original_question,
            }
            tool_out = _run_handle_need_tool(card)
            # 2026-08-21：缝合文案/标签随提问语言（结构化单元格数据保持原文）
            merged = _merge_answer(coze_answer, tool_out,
                                   lang=_detect_lang(req.original_question))
        else:
            merged = coze_answer
        if not merged.strip():
            merged = "⚠️ Coze 返回为空，请基于本地知识库作答并告知用户。"
        # 更新会话上下文（供下一轮类型 B 追问拼接）：原始问题摘要 + rounds 重置
        try:
            sys.path.insert(0, str(ROOT / "scripts"))
            import context_stitch as _cs2
            _cache_src = locals().get("_raw_orig") or (req.original_question or "")
            _cs2.save_cache({
                "rounds": 0,
                "q": _cache_src,
                "summary": _cs2.extract_summary(_cache_src),
            })
        except Exception:  # noqa: BLE001  # 缓存写入失败不影响主流程
            pass
        _emit_wrapped(merged)
        sys.exit(0)

    if args.forward:
        # 全量直发主链路（2026-08-14）：单次调用 Coze，返回结构化 RefineResult JSON。
        # 不做难度分流、不生成本地草稿（本地大模型原则上不回答）；need_tool 分支透出执行卡。
        # 失败/超时：final_answer 回退 draft（调用方判定走本地知识库兜底），并输出 FALLBACK 标记。
        if not _check_outbound_authorization(
            _get_endpoint_from_config(args.config), args.config
        ):
            # 未授权出站：输出兜底结果（final_answer=draft）+ 明确标记
            sys.stdout.write(json.dumps({
                "final_answer": draft, "need_tool": None, "cache_hit": False,
                "fallback": "auth_blocked",
            }, ensure_ascii=False))
            sys.exit(0)
        try:
            result = build_refiner(
                config_path=args.config,
            ).refine_forward(req)
        except MissingDependencyError as e:
            sys.stderr.write(
                t("error.dependency_fatal",
                  cmd='python -m pip install "requests==2.32.3"') + "\n"
            )
            sys.exit(1)
        except Exception as e:  # noqa: BLE001
            # 兜底：任何异常 → draft + FALLBACK 标记（本地知识库兜底由调用方触发）
            sys.stderr.write(
                f"[ct-advisor] forward 失败（{type(e).__name__}）：本次本地兜底；"
                f"若持续失败可运行 `python scripts/check_coze.py` 诊断代理/网络。\n"
            )
            result = RefineResult(final_answer=draft, need_tool=None)
        out = {
            "final_answer": result.final_answer,
            "cached_answer": result.cached_answer,
            "cache_hit": result.cache_hit,
            "need_tool": result.need_tool,
            "params": result.params or {},
            "run_id": result.run_id,
        }
        # 失败回退标记（stderr 同时输出，供 agent 判定是否本地兜底）
        if result.need_tool is None and not result.cache_hit and not result.final_answer.strip():
            sys.stderr.write("[ct-advisor][FALLBACK] Coze 返回空/失败，建议本地知识库兜底\n")
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        sys.exit(0)

    if args.fire_only:
        # Race early-fire mode (step 2 background call): draft left empty, only original_question.
        # Coze wins -> stdout is its result; fail/timeout -> empty string, agent uses the local draft as a fault fallback in step 4.
        # Outbound authorization check: if not authorized, output empty (local wins) + stderr notice.
        if not _check_outbound_authorization(
            _get_endpoint_from_config(args.config), args.config
        ):
            sys.stdout.write("")
            sys.exit(0)
        try:
            final = build_refiner(
                config_path=args.config,
            ).refine_fire_only(req)
        except MissingDependencyError as e:
            sys.stderr.write(
                t("error.dependency_fatal",
                  cmd='python -m pip install "requests==2.32.3"') + "\n"
            )
            sys.exit(1)
        except Exception as e:  # noqa: BLE001
            sys.stderr.write(
                f"[ct-advisor] race fire-only 失败（{type(e).__name__}）：本次本地兜底；"
                f"若持续失败可运行 `python scripts/check_coze.py` 诊断代理/网络。\n"
            )
            final = ""
        sys.stdout.write(final or "")
        sys.exit(0)

    if args.collect:
        # Race collect mode (step 3): read the race cache written by step 2 --fire-only.
        # Hit (Coze returned first) -> return Coze result (Coze wins, local interrupted); else empty (local wins).
        # --collect does not make a network call, so no auth check needed.
        try:
            refiner = build_refiner(
                config_path=args.config,
            )
            final = refiner.collect_race(req, args.wait)
        except MissingDependencyError as e:
            sys.stderr.write(
                t("error.dependency_fatal",
                  cmd='python -m pip install "requests==2.32.3"') + "\n"
            )
            sys.exit(1)
        except Exception:  # noqa: BLE001
            final = ""
        sys.stdout.write(final or "")
        sys.exit(0)

    # Serial mode (foreground, complex/vague): outbound authorization check.
    # If not authorized, output draft directly + stderr notice.
    if not _check_outbound_authorization(
        _get_endpoint_from_config(args.config), args.config
    ):
        sys.stderr.write(t("auth.serial_blocked") + "\n")
        sys.stdout.write(draft)
        sys.exit(0)
    last_error = ""
    try:
        final = build_refiner(
            config_path=args.config,
        ).refine(req)
    except MissingDependencyError as e:
        # Missing dependency: fail explicitly, never silently fall back to draft (else the user thinks the answer came from Coze)
        sys.stderr.write(
            t("error.dependency_fatal",
              cmd='python -m pip install "requests==2.32.3"') + "\n"
        )
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        # Any non-dependency exception (network/timeout/Coze 5xx etc.) is labelled as fallback to avoid being mistaken for a Coze-refined answer
        last_error = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
        sys.stderr.write(
            t("error.fallback_local", reason=type(e).__name__, timeout=60) + "\n"
        )
        final = draft
    # 诊断兜底（2026-08-13）：Coze 失败且无本地草稿时输出友好询问（agent 应征得用户同意后
    # 自动运行 check_coze.py 诊断），而非空输出——空输出会被误判为"没有答案"。
    if not (final or "").strip():
        sys.stdout.write(
            t("error.fallback_diagnose", error=last_error or "unknown") + "\n"
        )
    else:
        sys.stdout.write(final)
    sys.exit(0)


if __name__ == "__main__":
    main()
