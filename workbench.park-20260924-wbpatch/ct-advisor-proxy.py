#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ct-advisor 同源本地服务 / 代理（workbench 配套）

为什么需要它
------------
workbench/index.html 设计为「同源本地服务」架构：网页本体由本脚本在
http://127.0.0.1:8900 托管，浏览器直连同源的 /run，从而绕过 Coze 端点
(ct-advisor.coze.site/run) 的浏览器跨域(CORS)限制。若本服务未启动，网页
发送就会报「浏览器被跨域策略拦截，或本地代理未启动」。

职责
----
1) 以同源方式托管 workbench/ 下的 index.html 及静态资源（.js/.css/.json 等）；
2) POST /run 把网页发来的 payload 原样转发到 https://ct-advisor.coze.site/run
   （携带公开共享 Bearer token，取自 adapters/coze_token_embedded.py）；
3) 提供 /api/health、/api/config 等轻量端点，满足网页启动自检。

安全
----
默认监听 0.0.0.0（满足云端部署需被外部访问；本地若只想回环可设 CT_PROXY_HOST=127.0.0.1）。
转发的 token 为技能随包发布的
**公开共享**凭据（XOR+base64 混淆，非私有 key），符合 coze_token_embedded.py 约定。

依赖
----
仅 Python 3 标准库（http.server / urllib / importlib），无需 requests。
"""
import os
import sys
import json
import importlib.util
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# 端口：云端部署时平台注入 PORT；本地可用 CT_PROXY_PORT 覆盖；默认 8900。
PORT = int(os.environ.get("PORT", os.environ.get("CT_PROXY_PORT", "8900")))
# 绑定地址：云端必须 0.0.0.0 才能被外部访问；本地若只想回环可设 CT_PROXY_HOST=127.0.0.1。
HOST = os.environ.get("CT_PROXY_HOST", "0.0.0.0")
ROOT = os.path.dirname(os.path.abspath(__file__))          # workbench 目录
SKILL_ROOT = os.path.dirname(ROOT)                          # 技能根目录
COZE_ENDPOINT = "https://ct-advisor.coze.site/run"

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


def _load_get_token():
    """定位 coze_token_embedded.py 并取出 get_token。

    搜索顺序（部署后 workbench 目录即项目根，token 文件可能不在 ../adapters）：
      1) 环境变量 CT_COZE_TOKEN（直接给 token，最优先）
      2) ROOT/coze_token_embedded.py                  # 随包拷贝进 workbench（云端部署）
      3) SKILL_ROOT/adapters/coze_token_embedded.py   # 本地技能目录
      4) ROOT/../adapters/coze_token_embedded.py
    该 token 为技能随包发布的「公开共享」凭据（XOR+base64 混淆），非私有 key。
    """
    env_tok = os.environ.get("CT_COZE_TOKEN", "").strip()
    if env_tok:
        return lambda: env_tok
    candidates = [
        os.path.join(ROOT, "coze_token_embedded.py"),
        os.path.join(SKILL_ROOT, "adapters", "coze_token_embedded.py"),
        os.path.join(ROOT, "..", "adapters", "coze_token_embedded.py"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                spec = importlib.util.spec_from_file_location("coze_token_embedded", path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod.get_token
            except Exception as e:  # noqa: BLE001
                print("[warn] 加载 token 失败（%s）：" % path, e)
    print("[warn] 未找到 coze_token_embedded.py，/run 将以无 token 方式转发（Coze 可能 401）。")
    return lambda: ""


get_token = _load_get_token()


def forward_to_coze(payload_bytes):
    """转发 payload 到 Coze，返回响应对象（http.client.HTTPResponse / HTTPError），供分块直传。"""
    token = get_token()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(COZE_ENDPOINT, data=payload_bytes, headers=headers, method="POST")
    try:
        return urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        return e  # HTTPError 兼具 .code/.headers/.read()，可继续分块读取
    except Exception as e:  # noqa: BLE001
        raise


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/health":
            return self._send(200, "application/json", b'{"ok":true}')
        if path == "/api/config":
            # 现代前端默认走「同源 /run」；返回相对端点让网页无需硬编码主机。
            # token 由服务端在转发时注入，前端不持有，这里留空。
            return self._send(200, "application/json",
                              b'{"token":"","backend":{"remoteEndpoint":"/run"}}')
        if path in ("", "/"):
            path = "/index.html"
        fpath = os.path.normpath(os.path.join(ROOT, path.lstrip("/")))
        if not fpath.startswith(ROOT) or not os.path.isfile(fpath):
            return self._send(404, "application/json", b'{"error":"not found"}')
        ext = os.path.splitext(fpath)[1].lower()
        ctype = MIME.get(ext, "application/octet-stream")
        try:
            with open(fpath, "rb") as f:
                body = f.read()
        except Exception:  # noqa: BLE001
            return self._send(500, "application/json", b'{"error":"read fail"}')
        return self._send(200, ctype, body)

    def do_POST(self):
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length else b""
        if path == "/run":
            try:
                resp = forward_to_coze(body)
            except Exception as e:  # noqa: BLE001
                return self._send(502, "application/json",
                                  json.dumps({"error": str(e)}).encode("utf-8"))
            status = getattr(resp, "status", None) or getattr(resp, "code", 200)
            hdrs = dict(getattr(resp, "headers", {}) or {})
            ctype = hdrs.get("Content-Type", "application/json")
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")  # §性能 ④/传输：分块直传，避免服务端缓冲整包
            self.end_headers()
            try:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except Exception:  # noqa: BLE001
                        break
            except Exception:  # noqa: BLE001
                pass
            finally:
                try:
                    resp.close()
                except Exception:  # noqa: BLE001
                    pass
            return
        # 其余 /api/* 暂以 200 占位，避免前端非核心功能报错。
        return self._send(200, "application/json",
                          b'{"ok":false,"note":"not implemented in local proxy"}')

    def log_message(self, *a):  # 静默访问日志
        pass


if __name__ == "__main__":
    url = f"http://{HOST}:{PORT}/"
    print(f"ct-advisor 本地服务已启动： {url}")
    print("请在系统浏览器(Edge / Chrome)打开上述地址发送问题；Ctrl+C 停止。")
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    if HOST == "127.0.0.1":
        # §性能 ①：端口轮询就绪后再自动开浏览器（避免开白页），镜像 meta-analysis launch_workbench 思路
        import socket, webbrowser, threading, time
        def _open_when_ready():
            for _ in range(200):  # 约 30s 上限
                try:
                    with socket.create_connection(("127.0.0.1", PORT), timeout=0.3):
                        webbrowser.open(url); return
                except OSError:
                    time.sleep(0.15)
        threading.Thread(target=_open_when_ready, daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
