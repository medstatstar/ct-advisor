# -*- coding: utf-8 -*-
"""need_tool 执行卡 → 本地技能执行器（2026-08-14）

方案：Coze 单次调用。Coze 返回 need_tool 执行卡（技能 + 参数 + Coze 答案草稿），
本脚本机械执行对应本地技能 CLI，产出结构化结果；本地大模型以 draft_answer 为基底
缝合技能结果组织最终答案，**不回发 Coze**。

用法（供本地 agent 调用）：
    python handle_need_tool.py --card '<执行卡 JSON>'

执行卡 JSON（与 Coze GraphOutput need_tool 分支一致）：
    {
      "need_tool": "ct-registry",
      "params": {"cond": "...", "max": 20},
      "draft_answer": "Coze 原始答案草稿",
      "run_id": "..."
    }

输出（stdout，JSON）：
    {
      "tool": "ct-registry",
      "status": "ok" | "error" | "need_params",
      "result": <结构化结果（技能主产物 JSON/文本）>,
      "draft_answer": "<Coze 草稿，供缝合>",
      "elapsed_sec": 12.3
    }

status 语义：
    ok          技能执行成功，result 为结构化结果
    error       技能执行失败（rc/超时/脚本缺失），回退 Coze 草稿
    need_params 执行卡参数不完整（如缺效应量），result.missing 列出缺失项，
                由本地大模型向用户追问（不编造），补齐后重发执行卡
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# 技能根目录（WorkBuddy skills 目录），可用环境变量覆盖
SKILLS_DIR = os.environ.get(
    "CT_SKILLS_DIR",
    str(Path.home() / ".workbuddy" / "skills"),
)
# 映射表路径（本文件同目录）
MAPPING_PATH = Path(__file__).resolve().parent / "tool_mapping.json"


def _load_mapping() -> dict:
    with open(MAPPING_PATH, encoding="utf-8") as f:
        return json.load(f)


def _build_cmd(tool_cfg: dict, params: dict) -> list:
    """按映射表构造 CLI 命令；params 键对齐 argparse 参数，布尔 true 才加 flag"""
    cmd = [tool_cfg["cmd"]]
    for arg in tool_cfg["args"]:
        cmd.append(arg.replace("{SKILLS_DIR}", SKILLS_DIR))
    for key, spec in tool_cfg["params"].items():
        if key not in params or params[key] is None:
            continue
        val = params[key]
        if spec["type"] == "bool":
            if val is True:
                cmd.append(spec["flag"])
            # False → 不加 flag
            continue
        cmd.append(spec["flag"])
        cmd.append(str(val))
    # 追加额外参数（如 samplesize 的 --yes：执行卡场景视为已确认，跳过 SAFE PREVIEW）
    for extra in tool_cfg.get("extra_args", []):
        cmd.append(extra)
    return cmd


def _extract_json(stdout: str):
    """从 stdout 提取 JSON 主产物（优先最后一个完整 JSON 对象）；无则返回文本兜底。

    2026-08-20 修复：旧实现用 rfind('{')/rfind('}') 定位，遇嵌套 JSON（如
    ct-registry --print-summary 的 landscape 对象）会取到内层 { 导致切片不完整、
    json.loads 失败 → 退回全文。改为按行累积：从最后一行以 '{' 开头的行往前
    累积到闭合 '}'，逐段尝试解析。
    """
    stdout = (stdout or "").strip()
    if not stdout:
        return None
    # 整体解析
    try:
        return json.loads(stdout)
    except Exception:
        pass
    # 按行累积：从后往前找以 { 开头的行，累积到闭合 } 尝试解析
    lines = stdout.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if not lines[i].lstrip().startswith("{"):
            continue
        buf = lines[i]
        depth = buf.count("{") - buf.count("}")
        for j in range(i + 1, len(lines) + 1):  # j == len(lines) 表示不再追加
            # 每到一个闭合点（depth<=0）就尝试解析当前 buf
            if depth <= 0:
                try:
                    return json.loads(buf)
                except Exception:
                    pass  # 解析失败 → 可能跨行，继续追加
            if j >= len(lines):
                break
            buf += lines[j]
            depth += lines[j].count("{") - lines[j].count("}")
    return stdout  # 文本兜底


def _infer_missing_params(tool_cfg: dict, params: dict, question: str) -> tuple:
    """补全缺失参数：test 类参数用 test_hints（配置化关键词→值）推断。

    返回 (补全后的 params, 仍缺失的必需参数列表)。
    """
    params = dict(params)
    missing = []
    required = tool_cfg.get("required_params", [])
    for rp in required:
        if params.get(rp) is None:
            hints = tool_cfg.get("test_hints", {})
            if hints and question:
                q = question or ""
                for pattern, value in hints.items():
                    if any(kw in q for kw in pattern.split("|")):
                        params[rp] = value
                        break
            if params.get(rp) is None:
                missing.append(rp)
    # 效应量检查（samplesize 等）：effect_params 中至少提供一个
    for ep in tool_cfg.get("effect_params", []):
        if params.get(ep) is not None:
            return params, missing
    if tool_cfg.get("effect_params"):
        missing.append("效应量参数(任选其一): " + " / ".join(tool_cfg["effect_params"]))
    return params, missing


def execute_card(card: dict) -> dict:
    tool = card.get("need_tool")
    params = card.get("params") or {}
    draft = card.get("draft_answer") or ""
    question = card.get("original_question") or ""
    mapping = _load_mapping()
    tool_cfg = mapping["skills"].get(tool)
    if not tool_cfg:
        return {
            "tool": tool,
            "status": "error",
            "result": f"未在 tool_mapping.json 中找到技能映射: {tool}",
            "draft_answer": draft,
            "elapsed_sec": 0,
        }

    # 缺参检查与补全（test 推断 / 效应量缺失 → need_params 追问）
    params, missing = _infer_missing_params(tool_cfg, params, question)
    if missing:
        return {
            "tool": tool,
            "status": "need_params",
            "result": {
                "message": "执行卡参数不完整，需补充以下参数后才能执行",
                "missing": missing,
                "hint": "由本地大模型向用户询问缺失参数（不编造）；样本量/检验效能类必须提供效应量假设",
            },
            "draft_answer": draft,
            "elapsed_sec": 0,
        }

    cmd = _build_cmd(tool_cfg, params)
    timeout = tool_cfg.get("timeout", 120)
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        elapsed = round(time.time() - t0, 1)
        combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        if proc.returncode != 0:
            return {
                "tool": tool,
                "status": "error",
                "result": f"技能执行失败 rc={proc.returncode}: {combined[:2000]}",
                "draft_answer": draft,
                "elapsed_sec": elapsed,
            }
        result = _extract_json(proc.stdout or "")
        return {
            "tool": tool,
            "status": "ok",
            "result": result,
            "draft_answer": draft,
            "elapsed_sec": elapsed,
        }
    except subprocess.TimeoutExpired:
        return {
            "tool": tool,
            "status": "error",
            "result": f"技能执行超时（>{timeout}s）",
            "draft_answer": draft,
            "elapsed_sec": timeout,
        }
    except FileNotFoundError as e:
        return {
            "tool": tool,
            "status": "error",
            "result": f"技能脚本不存在: {e}",
            "draft_answer": draft,
            "elapsed_sec": 0,
        }


def main():
    ap = argparse.ArgumentParser(description="need_tool 执行卡 → 本地技能执行器")
    ap.add_argument("--card", required=True, help="执行卡 JSON 字符串")
    args = ap.parse_args()
    try:
        card = json.loads(args.card)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "result": f"执行卡 JSON 解析失败: {e}"}, ensure_ascii=False))
        sys.exit(1)
    out = execute_card(card)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
