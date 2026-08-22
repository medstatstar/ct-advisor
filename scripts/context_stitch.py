#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ct-advisor — 类型 B 追问自包含化（本地上下文摘要 + 拼接，代码级，无 LLM）

背景（2026-08-15 实测）：
  - 类型 A 追问（"刚才说的那个药"）已由 route.py ANAPHORA → vague → clarify_loop 覆盖。
  - 类型 B 追问（"若检验效能改用90%呢" / "如果HR是0.7呢"）无回指词，被判
    simple/middle/complex 直接转发 Coze，而 Coze payload 只有 original_question、
    无上一题上下文 → Coze 会重复追问已给参数（实测 need_params 追问 p1/p2），体验断裂。
  - 方案①：本地维护"上一轮问题 + 关键实体摘要"，转发前把追问拼接为自包含问题
    （"承接上一问（…实体摘要…），追问：<用户原话>"），Coze 契约零改动、隐私最小化。

设计（对齐"代码全自动、LLM 只兜底"红线）：
  - stdlib-only，无网络、无 LLM。
  - 缓存文件：{ROOT}/config/context_cache.json（本地运行态，gitignore 已排除 config 内运行时产物
    由 .gitignore data/ 段覆盖——本文件走 config/ 但仅本地生成，若担心入库可后续加 ignore）。
  - TTL：3 轮内有效（超过则视为新会话，不强拼）。

用法：
  echo "<用户追问>" | python scripts/context_stitch.py --prev "<上一轮摘要>"
        → 输出 enriched question（已自包含化）；无上下文时原样输出
  python scripts/context_stitch.py --store --q "<本轮问题>" --summary "<本轮结论摘要>"
        → 写入本轮上下文（供下一轮 --prev 使用）
  python scripts/context_stitch.py --clear
        → 清空会话上下文（新会话）
"""

import argparse
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "config", "context_cache.json")
TTL_ROUNDS = 3          # 上下文有效轮数
MAX_PREV_LEN = 200      # 拼接前缀上限（防止上下文膨胀）

# 承接语气信号：无回指词、但明显承接上文的短问。
# 分两档——强承接词（可覆盖完整问题锚点）与弱承接词（仅对无锚点短句生效）。
STRONG_FOLLOWUP = re.compile(
    r"(若|如果|假如|那|那么|改用|改成|调整为|调整|重新|再算|再|换成|"
    r"也适用|适用吗|按.*分配|分配合适)"
)
WEAK_FOLLOWUP = re.compile(r"(呢$|吗$)")
COMPLETE_ANCHOR = re.compile(
    r"(什么是|如何|怎么|为什么|请|帮我|解释|区别|比较|需要|是否|哪些|多少|"
    r"SDTM|ADaM|样本量|检验|试验|药物|方案|报告|时限|要求)"
)


def is_followup(q: str) -> bool:
    """判定是否为类型 B 追问（隐式承接、无回指词）。"""
    q = (q or "").strip()
    if not q:
        return False
    # 完整独立问题（有明确主题/动作词）：仅强承接词可覆盖（如"那III期也适用吗"）
    if COMPLETE_ANCHOR.search(q):
        return bool(STRONG_FOLLOWUP.search(q)) and len(q) <= 24
    # 无完整锚点：承接语气 + 短句（"如果HR是0.7呢"）
    return bool(STRONG_FOLLOWUP.search(q) or WEAK_FOLLOWUP.search(q)) and len(q) <= 24


def extract_summary(prev_q: str, prev_answer: str = "") -> str:
    """从上一轮问题中提取"关键实体摘要"（代码规则：保留药名/参数/终点，裁剪语气词）。"""
    prev_q = (prev_q or "").strip()
    if not prev_q:
        return ""
    # 剥离已拼接前缀（防止多轮追问嵌套）。两种格式：
    #   "承接上一问（…），追问：X"（stitch 产出）
    #   "承接上一问（…），追问：X"（含全角括号变体）——统一取最后一个 "追问：" 之后
    idx = prev_q.rfind("追问：")
    if idx >= 0:
        prev_q = prev_q[idx + len("追问："):]
    # 裁剪首尾语气/承接词，保留主体
    s = re.sub(r"^(若|如果|那|那么|请帮我|帮我|请问|我想知道)[，,、]?\s*", "", prev_q)
    s = re.sub(r"[？?。！!]$", "", s)
    s = s.strip()
    if len(s) > MAX_PREV_LEN:
        s = s[:MAX_PREV_LEN] + "…"
    return s


def load_cache():
    try:
        with open(CACHE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_cache(cache):
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, ensure_ascii=False, indent=2)
    except OSError:
        pass


def stitch(q: str, prev_summary: str) -> str:
    """拼接自包含问题。有上下文且为追问 → 拼接；否则原样。"""
    q = (q or "").strip()
    if not q:
        return q
    prev_summary = (prev_summary or "").strip()
    if prev_summary and is_followup(q):
        return f"承接上一问（{prev_summary}），追问：{q}"
    return q


def main() -> int:
    ap = argparse.ArgumentParser(description="ct-advisor 类型 B 追问自包含化")
    ap.add_argument("--prev", default=None, help="上一轮摘要（直接传入，优先于缓存）")
    ap.add_argument("--store", action="store_true",
                    help="存储本轮上下文（--q + --summary）")
    ap.add_argument("--q", default="", help="本轮问题（--store 用）")
    ap.add_argument("--summary", default="", help="本轮结论摘要（--store 用）")
    ap.add_argument("--clear", action="store_true", help="清空会话上下文")
    ap.add_argument("--check", action="store_true",
                    help="仅输出 JSON：是否追问 + 是否命中信号（供 route 集成）")
    args = ap.parse_args()

    if args.clear:
        save_cache({"rounds": 0})
        print("cleared")
        return 0

    if args.store:
        cache = load_cache()
        cache["rounds"] = 0
        cache["q"] = args.q
        cache["summary"] = args.summary
        save_cache(cache)
        print("stored")
        return 0

    if args.check:
        q = sys.stdin.read().strip() if not args.q else args.q
        print(json.dumps({"followup": is_followup(q)}, ensure_ascii=False))
        return 0

    # 拼接模式：读 stdin 问题
    q = sys.stdin.read().strip()
    if not q:
        q = args.q
    if args.prev:
        prev = args.prev
    else:
        cache = load_cache()
        rounds = int(cache.get("rounds", TTL_ROUNDS + 1))
        if rounds <= TTL_ROUNDS and cache.get("summary"):
            prev = cache["summary"]
        else:
            prev = ""
        # 本轮结束后 rounds+1（由调用方 --store 或此处自增）
        cache["rounds"] = rounds + 1
        save_cache(cache)
    print(stitch(q, prev))
    return 0


if __name__ == "__main__":
    sys.exit(main())
