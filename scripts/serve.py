#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ct-advisor 常驻编排服务（L1, 2026-09-25）

目的：把 run_orchestrate 所需的全部重模块（adapters / refine_answer / handle_need_tool /
route_tool / orchestrate 等，冷导入合计约 24s）在进程启动期一次性预热，此后每个 /ask 请求
直接复用 sys.modules 缓存，使单次问答的本地开销从 ~24s 降到接近 0（仅首启与空闲超时重置时付费）。

安全边界：
  - 仅监听 127.0.0.1（回环），外部不可达，不接受任何代码执行或文件副作用。
  - 仅暴露 /health、/ask、/shutdown 三个端点；/ask 只接受 {payload, config} 并返回
    run_orchestrate 的原始字符串（含 <<<CT_ANSWER_START/END>>> + sha256），与 entry.py
    内联路径输出格式完全一致——HARD GATE 与输出契约不变。
  - 空闲超时自动退出（默认 600s），避免孤儿进程常驻。
"""
from __future__ import annotations
import json
import os
import sys
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
for _p in (SCRIPT_DIR, SKILL_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

PORT = int(os.environ.get("CT_ADVISOR_PORT", "18771"))
IDLE_TIMEOUT = int(os.environ.get("CT_ADVISOR_IDLE", "600"))

_last_request = [time.time()]
__version__ = "1.2.0"          # 技能版本，供 /version 探针
ORCH_MTIME = [0]                # 服务启动时采集的 orchestrate.py 修改时间


def _warmup():
    """一次性预热重模块。个别失败不应阻断启动（首个 /ask 内会再次导入）。"""
    import importlib
    for mod in ("route", "route_tool", "adapters", "refine_answer",
                "handle_need_tool", "orchestrate"):
        try:
            importlib.import_module(mod)
        except Exception as e:  # noqa: BLE001
            sys.stderr.write(f"[serve] 预热 {mod} 失败: {e}\n")
    sys.stderr.write("[serve] 预热完成\n")
    # 采集版本信息：记录 orchestrate.py 的 mtime，供 entry 版本探针比较
    try:
        import orchestrate as _orch
        ORCH_MTIME[0] = os.path.getmtime(_orch.__file__)
    except Exception:
        ORCH_MTIME[0] = 0


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _send(self, code, body: bytes, ctype="text/plain; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _touch(self):
        _last_request[0] = time.time()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._touch()
            self._send(200, b"ok")
        elif path == "/shutdown":
            self._send(200, b"shutting down")
            threading.Thread(target=lambda: (time.sleep(0.1), os._exit(0)),
                             daemon=True).start()
        elif path == "/version":
            self._touch()
            body = json.dumps({
                "version": __version__,
                "orchestrate_mtime": ORCH_MTIME[0],
                "port": PORT,
            }).encode("utf-8")
            self._send(200, body, "application/json")
        else:
            self._send(404, b"not found")

    def do_POST(self):
        path = urlparse(self.path).path
        self._touch()
        if path != "/ask":
            self._send(404, b"not found")
            return
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length) if length else b""
            data = json.loads(raw.decode("utf-8"))
            payload = data["payload"]
            config = data.get("config", os.path.join(SKILL_ROOT, "config.json"))
        except Exception as e:  # noqa: BLE001
            self._send(400, f"bad request: {e}".encode("utf-8"))
            return
        try:
            from orchestrate import run_orchestrate
            out = run_orchestrate(payload, config)
            self._send(200, out.encode("utf-8"))
        except Exception as e:  # noqa: BLE001
            self._send(500, f"orchestrate error: {e}".encode("utf-8"))


def _idle_watchdog():
    while True:
        time.sleep(15)
        if time.time() - _last_request[0] > IDLE_TIMEOUT:
            sys.stderr.write("[serve] 空闲超时，退出\n")
            os._exit(0)


def main():
    _warmup()
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError as e:
        sys.stderr.write(f"[serve] 端口 {PORT} 绑定失败（可能被旧服务占用）: {e}\n")
        sys.exit(1)
    sys.stderr.write(f"[serve] 监听 127.0.0.1:{PORT}\n")
    threading.Thread(target=_idle_watchdog, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
