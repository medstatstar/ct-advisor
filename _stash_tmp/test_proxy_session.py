#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""离线验证 proxy 的会话注入 + 缓存/去重短路（不联网）。"""
import sys
import json
import tempfile
import pathlib

SKILL = pathlib.Path(r"C:/Users/WintoneFileSrv/.workbuddy/skills/ct-advisor")
sys.path.insert(0, str(SKILL / "workbench"))
sys.path.insert(0, str(SKILL / "scripts"))

import session_store as ss

TMP = tempfile.mkdtemp()
ss.STORE_PATH = pathlib.Path(TMP) / "session_store.json"
ss.LOCK_PATH = pathlib.Path(TMP) / ".lock"

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "ct_advisor_proxy",
    str(SKILL / "workbench" / "ct-advisor-proxy.py"))
proxy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(proxy)

SID = "proxy-session-1"

def mk(q):
    return json.dumps({
        "entry_point": "workbench",
        "original_question": q,
        "query_meta": {"difficulty": "forwarded"},
        "conversation_history": [],
    }).encode()

# R1：首问，无历史无缓存 → 不短路；注入空 history
nb1, sc1 = proxy._inject_session(mk("多中心某中心退出怎么处理"), "/async_run", {"X-Session-Id": SID})
print("R1 shortcut(应None):", sc1)
print("R1 注入字段含 conversation_history:", b"conversation_history" in nb1)

# 模拟收到答案 → 上报
ss.record(SID, "多中心某中心退出怎么处理",
          answer="答：按方案偏离处理并上报伦理。", difficulty="forwarded")

# R2：承接追问，前端未带 history → 注入服务端历史 1 轮
nb2, sc2 = proxy._inject_session(mk("那如果已入组20例呢"), "/async_run", {"X-Session-Id": SID})
d2 = json.loads(nb2)
print("R2 shortcut(应None):", sc2)
print("R2 注入 history 轮数(应=1):", len(d2.get("conversation_history", [])))

# R3：重复 R1 → 命中全局缓存 → 短路返回本地 task_id
nb3, sc3 = proxy._inject_session(mk("多中心某中心退出怎么处理"), "/async_run", {"X-Session-Id": SID})
tid = (sc3 or {}).get("task_id")
print("R3 shortcut 含 task_id:", bool(tid))
print("R3 本地伪 task 存在:", tid in proxy._LOCAL_TASKS)
print("R3 task 答案正确:",
      proxy._LOCAL_TASKS.get(tid, {}).get("result", {}).get("final_answer") == "答：按方案偏离处理并上报伦理。")

# R4：近似重复（去重短路）
nb4, sc4 = proxy._inject_session(mk("多中心某中心要退出怎么处理"), "/async_run", {"X-Session-Id": SID})
print("R4 近似重复短路含 task_id:", bool((sc4 or {}).get("task_id")))

# /run 同步路径短路返回 {result:{...}}
nb5, sc5 = proxy._inject_session(mk("多中心某中心退出怎么处理"), "/run", {"X-Session-Id": SID})
print("R5 /run 短路含 result.final_answer:",
      bool((sc5 or {}).get("result", {}).get("final_answer")))

# /stream_run 不短路（仅注入上下文）
nb6, sc6 = proxy._inject_session(mk("多中心某中心退出怎么处理"), "/stream_run", {"X-Session-Id": SID})
print("R6 /stream_run 不短路(应None):", sc6)

print("ALL_DONE")
