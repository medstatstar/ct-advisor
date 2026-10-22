#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""离线端到端验证 entry.py 的会话上下文注入 + 全局缓存短路（不联网）。"""
import json
import os
import sys
import tempfile
import pathlib

SKILL = pathlib.Path(r"C:/Users/WintoneFileSrv/.workbuddy/skills/ct-advisor")
sys.path.insert(0, str(SKILL / "scripts"))

import session_store as ss

TMP = tempfile.mkdtemp()
ss.STORE_PATH = pathlib.Path(TMP) / "session_store.json"
ss.LOCK_PATH = pathlib.Path(TMP) / ".lock"

import entry

_outbound = {"n": 0}

def fake_orchestrate(payload: str, config: str) -> str:
    _outbound["n"] += 1
    obj = json.loads(payload)
    q = obj["original_question"]
    hist = obj.get("conversation_history", [])
    return entry._wrap(
        "答：关于「%s」，已承接上文 %d 轮。多中心某中心退出按方案偏离处理并上报。"
        % (q[:12], len(hist))
    )

entry.run_orchestrate_via_server = fake_orchestrate

def dec(b64file):
    raw = pathlib.Path(b64file).read_text(encoding="utf-8")
    return entry._extract_plain(raw)

SID = "test-session-1"

def run(q, outfile):
    sys.argv = ["entry.py", "--q", q, "--session", SID, "--out", outfile]
    try:
        entry.main()
    except SystemExit:
        pass

# 第一轮
run("多中心研究中如果一个中心突然要退出怎么处理", os.path.join(TMP, "o1.txt"))
print("R1 出站次数:", _outbound["n"], "| 答案含'已承接上文 0 轮':", "已承接上文 0 轮" in dec(os.path.join(TMP, "o1.txt")))

# 第二轮（承接追问，验证 history 注入）
run("那如果退出的中心已经入了20例受试者呢", os.path.join(TMP, "o2.txt"))
print("R2 出站次数:", _outbound["n"], "| 答案含'已承接上文 1 轮':", "已承接上文 1 轮" in dec(os.path.join(TMP, "o2.txt")))

data = json.loads(ss.STORE_PATH.read_text(encoding="utf-8"))
print("history 轮数(应=2):", len(data["sessions"][SID]["history"]))
print("global_cache 条数(应=2):", len(data.get("global_cache", {})))

# 第三轮：重复第一轮 → 应命中全局缓存短路（不再出站）
run("多中心研究中如果一个中心突然要退出怎么处理", os.path.join(TMP, "o3.txt"))
print("R3 重复发送后总出站次数(应仍=2):", _outbound["n"])
print("R3 命中缓存(答案与R1一致):", "已承接上文 0 轮" in dec(os.path.join(TMP, "o3.txt")))

# 第四轮：近似重复（去重短路）
run("多中心研究如果一个中心突然退出怎么处理", os.path.join(TMP, "o4.txt"))
print("R4 近似重复后总出站次数(应仍=2):", _outbound["n"])

# 无 session 退化：同问题应仍命中全局缓存（覆盖飞书无 session 场景）
_outbound["n"] = 0
sys.argv = ["entry.py", "--q", "样本量怎么估算", "--out", os.path.join(TMP, "o5.txt")]
try:
    entry.main()
except SystemExit:
    pass
print("无session首问出站(应=1):", _outbound["n"])
sys.argv = ["entry.py", "--q", "样本量怎么估算", "--out", os.path.join(TMP, "o6.txt")]
try:
    entry.main()
except SystemExit:
    pass
print("无session重复同问题出站(应仍=1,命中全局缓存):", _outbound["n"])
print("ALL_DONE")
