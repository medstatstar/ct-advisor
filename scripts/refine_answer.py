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
import json
import re
import sys
from pathlib import Path
from typing import Set

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from adapters import build_refiner, RefineRequest, MissingDependencyError

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
    # 3. 未授权：输出拦截提示，agent 应展示给用户确认
    sys.stderr.write(
        f"[ct-advisor][AUTH-BLOCK] outbound to {endpoint} requires user confirmation.\n"
        f"  Add to config.json 'auto_approve_endpoints' list to skip confirmation.\n"
        f"  Local reference materials are limited; declining will disable cloud-based refinement "
        f"and significantly reduce answer quality/coverage.\n"
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
    ap.add_argument("--token", help="inline coze token (CLI precedence); not for daily use")
    ap.add_argument("--token-path", help="path to obfuscated token file (overrides config token_file)")
    ap.add_argument("--store-token", metavar="TOKEN",
                    help="store the given token (obfuscated) to the token file and exit")
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
    args = ap.parse_args()

    if args.store_token:
        # 公共凭据统一从 config/keys.py 导入
        import sys as _sys, importlib.util as _ilu
        _keys_spec = _ilu.spec_from_file_location("config.keys", "config/keys.py")
        _keys = _ilu.module_from_spec(_keys_spec)
        _keys_spec.loader.exec_module(_keys)
        path = _keys.store_token(args.store_token, args.token_path or _keys.default_token_path())
        sys.stdout.write(f"[ct-advisor] token stored (obfuscated) -> {path} / token 已存储（混淆）-> {path}\n")
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
        # query_origin is auto-stamped into query_meta by normalize(); no top-level field.
    except Exception as e:
        # JSON parse failed: distinguish --collect mode (cache lookup) from other modes
        if args.collect:
            # --collect mode: payload parse failure means the cache path cannot be located;
            # tell the agent explicitly "local wins", do NOT confuse it with "cache miss"
            sys.stderr.write(
                f"[ct-advisor] collect: payload parse failed ({type(e).__name__}), "
                "cannot locate race cache -> **LOCAL WINS**, agent should use local draft directly, do NOT wait for Coze / "
                "collect: payload 解析失败，无法查找 race 缓存 → **本地胜出**，agent 应直接采用本地草稿，禁止等 Coze\n"
            )
            sys.stdout.write("")
            sys.exit(0)
        # Other modes (fire-only / serial): cannot self-heal; warn clearly + fall back to draft
        sys.stderr.write(
            f"[ct-advisor] payload parse failed (invalid JSON): {type(e).__name__}; "
            "fell back to local draft, remote NOT called / "
            f"payload 解析失败（非合法 JSON）: {type(e).__name__}；已回退本地草稿，未调用远程\n"
        )
        sys.stdout.write(draft)
        sys.exit(0)

    # Contract self-heal: fill missing/invalid fields, eliminating the "invalid payload -> silent fallback" root cause
    heal_notes = req.normalize()
    if heal_notes:
        sys.stderr.write(
            "[ct-advisor] payload auto-healed (self-heal, remote called as usual): "
            + "; ".join(heal_notes) + " / "
            "payload 已自动补全（自愈，照常调用远程）: " + "; ".join(heal_notes) + "\n"
        )

    try:
        req.validate()  # Should pass after self-heal; only fails in extreme cases (both orgq and draft empty)
    except ValueError as e:
        sys.stderr.write(
            f"[ct-advisor] payload contract validation failed: {e}; "
            "fell back to local draft, remote NOT called / "
            f"payload 契约校验失败: {e}；已回退本地草稿，未调用远程\n"
        )
        # Fallback: when the draft is also empty, emit an explicit prompt instead of a silent empty answer
        if not draft or not draft.strip():
            sys.stdout.write(
                "[ct-advisor] cannot generate answer: the problem description is empty, please provide a specific clinical-trial question. / "
                "无法生成答案：问题描述为空，请提供具体的临床试验问题。\n"
            )
        else:
            sys.stdout.write(draft)
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
                cli_token=args.token,
                token_path=args.token_path,
            ).refine_fire_only(req)
        except MissingDependencyError as e:
            sys.stderr.write(
                f"[ct-advisor][FATAL] refiner dependency missing: {e}\n"
                "this issue will NOT silently fall back; install per the command above and retry. / "
                "精校依赖缺失；此问题不会静默回退；请按上述命令安装后重试。\n"
            )
            sys.exit(1)
        except Exception:  # noqa: BLE001
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
                cli_token=args.token,
                token_path=args.token_path,
            )
            final = refiner.collect_race(req, args.wait)
        except MissingDependencyError as e:
            sys.stderr.write(
                f"[ct-advisor][FATAL] refiner dependency missing: {e}\n"
                "this issue will NOT silently fall back; install per the command above and retry. / "
                "精校依赖缺失；此问题不会静默回退；请按上述命令安装后重试。\n"
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
        sys.stderr.write(
            f"[ct-advisor][AUTH-BLOCK] serial refine blocked — falling back to local draft.\n"
        )
        sys.stdout.write(draft)
        sys.exit(0)
    try:
        final = build_refiner(
            config_path=args.config,
            cli_token=args.token,
            token_path=args.token_path,
        ).refine(req)
    except MissingDependencyError as e:
        # Missing dependency: fail explicitly, never silently fall back to draft (else the user thinks the answer came from Coze)
        sys.stderr.write(
            f"[ct-advisor][FATAL] refiner dependency missing: {e}\n"
            "this issue will NOT silently fall back; install per the command above and retry. / "
            "精校依赖缺失；此问题不会静默回退；请按上述命令安装后重试。\n"
        )
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        # Any non-dependency exception (network/timeout/Coze 5xx etc.) is labelled as fallback to avoid being mistaken for a Coze-refined answer
        sys.stderr.write(
            f"[ct-advisor][coze] FALLBACK_TO_LOCAL_DRAFT "
            f"reason={type(e).__name__}; not retrying coze; returning local draft_answer\n"
        )
        final = draft
    sys.stdout.write(final or draft)
    sys.exit(0)


if __name__ == "__main__":
    main()
