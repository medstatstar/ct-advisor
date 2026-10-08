# -*- coding: utf-8 -*-
"""
ct-advisor — 常驻编排服务的本地 HTTP 客户端（§16.9 适配层）

原 scripts/entry.py 中通过 urllib.request 与本地常驻编排服务（L1,
http://127.0.0.1:<CT_ADVISOR_PORT>）通信的**所有出站代码**，已按 §16.9 迁移到
此统一适配器目录，使 scripts/entry.py 不再含任何 urllib 出站调用。

§16.9 要求：对外 API / 检索 / 远程 LLM 调用"一律移入本技能统一的专用目录（推荐
adapters/）"。常驻编排服务虽为本机 loopback，但仍是进程外出站 HTTP 调用，故同样
下沉到此适配层，与 coze_upload 等出站适配器保持一致。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# 确保 scripts/（orchestrate 等兄弟模块）与技能根可 import
_SKILL_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _SKILL_ROOT / "scripts"
for _p in (str(_SCRIPTS_DIR), str(_SKILL_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from orchestrate import run_orchestrate  # 内联回退路径

SERVER_PORT = int(os.environ.get("CT_ADVISOR_PORT", "18771"))
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"


def server_available() -> bool:
    try:
        with urllib.request.urlopen(SERVER_URL + "/health", timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


def server_version() -> dict:
    try:
        with urllib.request.urlopen(SERVER_URL + "/version", timeout=2) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return {}


def server_stale() -> bool:
    """本地 orchestrate.py 比常驻服务启动时记录的更新 -> 需重启服务以加载新代码。"""
    try:
        local = os.path.getmtime(os.path.join(str(_SCRIPTS_DIR), "orchestrate.py"))
        remote = server_version().get("orchestrate_mtime", 0)
        return local > remote
    except Exception:
        return False


def shutdown_server():
    try:
        urllib.request.urlopen(SERVER_URL + "/shutdown", timeout=3)
    except Exception:
        pass


def start_server():
    """best-effort 后台拉起常驻服务；失败不影响主流程（回退内联）。"""
    try:
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen(
            [sys.executable, str(_SCRIPTS_DIR / "serve.py")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
        sys.stderr.write("[entry] 已后台拉起常驻服务\n")
    except Exception as e:
        sys.stderr.write(f"[entry] 常驻服务拉起失败（回退内联）: {e}\n")


def wait_server(timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if server_available():
            return True
        time.sleep(0.5)
    return False


def server_ask(payload: str, config: str, timeout: int = 300) -> str:
    data = json.dumps({"payload": payload, "config": config}).encode("utf-8")
    req = urllib.request.Request(
        SERVER_URL + "/ask",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def run_orchestrate_via_server(payload: str, config: str) -> str:
    """优先常驻服务（L1），版本漂移时自动重启；不可用时回退内联 run_orchestrate。

    替代原 entry.py 的 _run_orchestrate；出站（urllib）逻辑已下沉到本适配器。
    """
    if server_available():
        if server_stale():
            sys.stderr.write("[entry] 检测到技能代码更新，重启常驻服务\n")
            shutdown_server()
            time.sleep(1.5)  # 等端口释放
            start_server()
            if not wait_server():
                return run_orchestrate(payload, config)
        else:
            try:
                return server_ask(payload, config)
            except Exception as e:
                sys.stderr.write(f"[entry] 常驻服务调用失败（回退内联）: {e}\n")
                return run_orchestrate(payload, config)
    else:
        start_server()
        if not wait_server():
            return run_orchestrate(payload, config)
    try:
        return server_ask(payload, config)
    except Exception as e:
        sys.stderr.write(f"[entry] 常驻服务调用失败（回退内联）: {e}\n")
        return run_orchestrate(payload, config)
