#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ct-advisor — 单命令封装（2026-10-16）

背景（来自 log.docx 性能诊断）：
  旧流程要求本地大模型在拿到 entry.py 的 stdout 后，**自己**把
  <<<CT_ANSWER_B64_START>>> 与 <<<CT_ANSWER_B64_END>>> 之间那段约 2600 字符的
  base64 载荷**逐字复制**进另一条命令里解码 + 校验。LLM 没有可靠的「长随机串
  搬运」通道，log 中 agent 自己确认了失败原因：

      "I introduced a typo 5Lzd instead of 5L+d! That's the corruption."

  校验失败后 agent 又按 SKILL.md 的决策表走「修复捕获 → 重发一次」分支，
  而主链路的本地去重实际并不生效（见 answer_cache.py 说明），于是变成
  真实的重复 Coze 调用 —— 一次问答被拖到几分钟。

本脚本把「运行 → 解码 → 校验 → 打印明文」合并为**一次调用**：
  - 校验在脚本内部完成（re.search + b64decode + sha256），零人工搬运；
  - stdout 直接是明文答案，agent 原样透传即可（体积也回落到明文大小，
    远离 PowerShell 约 20k 字符的回传截断线）；
  - entry.py 的 stderr 原样透传到本进程 stderr，**不再丢弃**诊断信号
    （dedup / 常驻服务复用 / 答案缓存命中等）。

用法：
  python scripts/ask.py --q "用户问题" [--attach "路径"] [--raw] [--timeout 300]

输出约定：
  stdout  = 校验通过的明文答案（--raw 时改为 entry.py 原始输出）
  stderr  = entry.py 的诊断行 + 本脚本的失败原因
  退出码  = 0 成功；2 完整性校验失败（stdout 为空）；其余为 entry.py 的退出码

契约不变：本脚本不生成、不改写任何答案内容，只是把 entry.py 的产物解包后透传。
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent

# UTF-8 强制（与 entry.py 同口径，2026-10-16）：entry.py 的 base64 出口本来就是为了
# 绕开中文 Windows（cp936）控制台回传乱码，但 ask.py 输出的是**明文答案**——若不强制
# UTF-8，Python 会按 locale（cp936）编码 stdout，agent 侧按 UTF-8 捕获时中文必乱码，
# 而 HARD GATE 又禁止 agent 改写答案 → 死锁。故此处必须与 entry.py 保持同一纪律。
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    except Exception:  # noqa: BLE001
        pass

B64_START = "<<<CT_ANSWER_B64_START>>>"
B64_END = "<<<CT_ANSWER_B64_END>>>"

_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


def _hidden_kwargs() -> dict:
    """抑制子进程控制台弹窗（非 Windows 返回 {}）。"""
    if not sys.platform.startswith("win"):
        return {}
    kw = {"creationflags": _CREATE_NO_WINDOW}
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        kw["startupinfo"] = si
    except Exception:  # noqa: BLE001
        pass
    return kw


def unwrap(stdout: str) -> tuple[str, bool, str]:
    """从 entry.py 的 stdout 解出明文答案并校验 sha256。

    返回 (answer, ok, detail)：
      - ok=True  → answer 为校验通过的明文答案
      - ok=False → answer 可能为空，detail 为失败原因（人读）
    """
    if not stdout:
        return "", False, "empty stdout from entry.py"

    m = re.search(
        re.escape(B64_START) + r"\s*\n(.*?)\n\s*" + re.escape(B64_END)
        + r"\r?\nchecksum:\s*([0-9a-fA-F]{16})",
        stdout,
        re.DOTALL,
    )
    if not m:
        return "", False, (
            "no <<<CT_ANSWER_B64_START/END>>> block with checksum found "
            "(stdout structure destroyed or truncated)"
        )

    # b64 载荷可能被捕获通道按显示宽度折行，解码前统一剥离所有空白
    payload = re.sub(r"\s+", "", m.group(1))
    try:
        answer = base64.b64decode(payload, validate=False).decode("utf-8")
    except Exception as e:  # noqa: BLE001
        return "", False, f"base64 decode failed: {type(e).__name__}: {e}"

    expected = m.group(2).strip().lower()
    actual = hashlib.sha256(
        answer.replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()[:16]
    if actual != expected:
        return answer, False, (
            f"checksum mismatch: expected={expected} actual={actual}"
        )
    return answer, True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="ct-advisor 单命令封装：跑 entry.py + 脚本内解码校验 + 输出明文答案"
    )
    ap.add_argument("--q", required=True, help="用户问题")
    ap.add_argument("--attach", default=None, help="附件路径")
    ap.add_argument("--q-meta", default=None, help="可选 query_meta JSON（透传给 entry.py）")
    ap.add_argument("--timeout", type=float, default=900.0,
                    help="entry.py 超时秒数（默认 900）。必须大于 entry.py 内部的最坏耗时："
                         "Coze long_timeout 300s + 委托 card-inline 300s，留足余量")
    ap.add_argument("--raw", action="store_true",
                    help="不做解包，直接透传 entry.py 的原始 stdout（调试用）")
    args = ap.parse_args()

    # 2026-10-16：空问题直接拦在本层，避免把空串送进 entry.py 后走成「vague → 澄清」
    # 这类语义上无意义的往返（agent 侧拿到明确失败信号，而不是一个奇怪的反问）。
    if not (args.q or "").strip():
        sys.stderr.write("[ask] --q 不能为空（未收到有效问题）\n")
        return 4

    cmd = [sys.executable, str(SCRIPT_DIR / "entry.py"), "--q", args.q]
    if args.attach:
        cmd += ["--attach", args.attach]
    if args.q_meta:
        cmd += ["--q-meta", args.q_meta]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=args.timeout,
            **_hidden_kwargs(),
        )
    except subprocess.TimeoutExpired:
        sys.stderr.write(f"[ask] entry.py 超时（>{args.timeout:.0f}s），已终止\n")
        return 3

    # 诊断信号一律透传，不再被 2>$null 之类丢弃
    if proc.stderr:
        sys.stderr.write(proc.stderr)

    stdout = proc.stdout or ""
    if args.raw:
        sys.stdout.write(stdout)
        return proc.returncode

    answer, ok, detail = unwrap(stdout)
    if not ok:
        sys.stderr.write(f"[ask] integrity check FAILED: {detail}\n")
        sys.stderr.write(
            "[ask] 不要重跑 entry.py。请把上面这行 stderr 原样报告给用户；\n"
            "[ask] 若确需排查：--raw 查看 entry.py 原始输出，\n"
            "[ask] 或查看常驻服务日志 config/serve.log（服务端 stderr 落盘处）。\n"
        )
        return 2

    sys.stdout.write(answer if answer.endswith("\n") else answer + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
