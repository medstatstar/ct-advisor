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
# 执行卡产物根目录（2026-08-23）：各技能默认把 out/ 写到**进程 cwd**，
# 此前 cwd = scripts/ → 产物污染脚本目录（实测 scripts/out/report.xlsx 等）。
# 改为按技能隔离到 ct-advisor/out/cards/<tool>/。
CARDS_ROOT = Path(__file__).resolve().parent.parent / "out" / "cards"

# stdout 噪声行（内联图 / 组件标记）：ct-samplesize 单次可输出数万字符 SVG，
# 直接进 result 会挤爆缝合层上下文 → 剥离并以占位符替代。
NOISE_PREFIXES = ("__SVG_WIDGET__", "__FIGURE__", "__HTML_WIDGET__")
MAX_RESULT_CHARS = 4000


def _load_mapping() -> dict:
    with open(MAPPING_PATH, encoding="utf-8") as f:
        return json.load(f)


def _sanitize_result(result):
    """剥离内联图/组件噪声块并限长（仅对文本兜底结果生效）。

    2026-08-23 修正：首版只按行前缀过滤，但 `__SVG_WIDGET__` 是**多行块**
    （标记只在首行，后续 <svg>/<g>/<path> 上万行不带前缀）→ SVG 仍整块进 result。
    改为状态机：命中标记后丢弃其余所有行（内联图恒在数值输出之后）。
    """
    if not isinstance(result, str):
        return result
    kept, figures = [], []
    for line in result.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(NOISE_PREFIXES):
            figures.append(stripped.split()[0].strip("_"))
            if stripped.startswith("__SVG_WIDGET__") or stripped.startswith("__HTML_WIDGET__"):
                break  # 多行组件块：其后全部丢弃
            continue
        kept.append(line)
    text = "\n".join(kept).strip()
    if figures:
        text += f"\n[已剥离 {len(figures)} 个内联图形块（{'/'.join(sorted(set(figures)))}）：图形不参与文字缝合]"
    if len(text) > MAX_RESULT_CHARS:
        text = text[:MAX_RESULT_CHARS] + f"\n…[截断，原长 {len(result)} 字符]"
    return text


def _read_artifacts(tool_cfg: dict, workdir: Path) -> dict:
    """回读技能产物文件（stdout 无结构化数值时的唯一数据来源）。

    2026-08-23 实测：WorkBuddy 沙箱会把技能写出的 .md/.json 重定向到
    `<out>/_unsaved/` 子目录（.xlsx/.html 不受影响）。因此每个候选文件都要
    在 out/、out/_unsaved/ 两处 + 递归兜底里找，否则回读恒为空。
    """
    names = tool_cfg.get("result_files") or []
    if not names:
        return {}
    arts = {}
    for name in names:
        hit = None
        for cand in (workdir / "out" / name,
                     workdir / "out" / "_unsaved" / name,
                     workdir / name):
            if cand.is_file():
                hit = cand
                break
        if hit is None:
            matches = sorted(workdir.rglob(name))
            hit = matches[0] if matches else None
        if hit is None:
            continue
        try:
            raw = hit.read_text(encoding="utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            arts[name] = f"[读取失败: {e}]"
            continue
        if hit.suffix == ".json":
            try:
                arts[name] = json.loads(raw)
                continue
            except Exception:
                pass
        arts[name] = raw[:MAX_RESULT_CHARS]
    return arts


def _build_deferred(mapping: dict, primary: str, need_tools) -> list:
    """多技能命中 → 只执行主判技能，其余生成「请先准备数据」提示项。

    需求（2026-08-23）：一次提问可能同时命中试验格局/信号/文献/样本量，
    全部串行执行会叠加数分钟联网耗时且参数多半不全。改为**只调最关键的一个**
    （主判由 route_tool.predict / Coze tool_router 的优先级规则决定），
    其余以 deferred 形式回给用户，附各自需要准备的参数。
    """
    deferred = []
    for t in (need_tools or []):
        if t == primary or not t:
            continue
        cfg = mapping["skills"].get(t) or {}
        deferred.append({
            "tool": t,
            "required_params": cfg.get("required_params", []),
            "prep_hint": cfg.get("prep_hint", "需补充该技能的必填参数后单独调用"),
        })
    return deferred


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
    # 条件参数（2026-08-23）：仅当某参数缺失/存在时才追加，用于补齐技能的默认行为落差
    # （如 ct-safety 缺 --event 时不做 disproportionality → 自动补 --top-events-signal）
    for rule in tool_cfg.get("conditional_args", []):
        absent = rule.get("when_absent")
        present = rule.get("when_present")
        if absent and params.get(absent) not in (None, ""):
            continue
        if present and params.get(present) in (None, ""):
            continue
        cmd.extend(rule.get("args", []))
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
    # 多命中场景：其余技能延后，附「请先准备数据」提示（需求 2026-08-23）
    deferred = _build_deferred(mapping, tool, card.get("need_tools"))
    deferred_note = ""
    if deferred:
        items = "；".join(f"{d['tool']}（{d['prep_hint']}）" for d in deferred)
        deferred_note = (
            f"本轮只执行最关键的 {tool}。还识别到 {len(deferred)} 个可选数据源需要你先准备信息：{items}。"
            "确认参数后我再逐个调用。"
        )
    if not tool_cfg:
        return {
            "tool": tool,
            "status": "error",
            "result": f"未在 tool_mapping.json 中找到技能映射: {tool}",
            "draft_answer": draft,
            "deferred_tools": deferred,
            "deferred_note": deferred_note,
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
            "deferred_tools": deferred,
            "deferred_note": deferred_note,
            "elapsed_sec": 0,
        }

    cmd = _build_cmd(tool_cfg, params)
    timeout = tool_cfg.get("timeout", 120)
    workdir = CARDS_ROOT / tool
    workdir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            cwd=str(workdir),
        )
        elapsed = round(time.time() - t0, 1)
        combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        if proc.returncode != 0:
            return {
                "tool": tool,
                "status": "error",
                "result": f"技能执行失败 rc={proc.returncode}: {combined[:2000]}",
                "draft_answer": draft,
                "deferred_tools": deferred,
                "deferred_note": deferred_note,
                "elapsed_sec": elapsed,
            }
        result = _sanitize_result(_extract_json(proc.stdout or ""))
        artifacts = _read_artifacts(tool_cfg, workdir)
        # 假成功守卫（2026-08-23）：rc=0 但技能停在 PREVIEW 安全门时，
        # 旧实现判 status=ok、把 "would run …" 当数据交给缝合层（ct-literature 实测）。
        if isinstance(result, str) and "[PREVIEW]" in result and not artifacts:
            return {
                "tool": tool,
                "status": "error",
                "result": f"技能停在 PREVIEW 安全门未联网执行（缺 --run）：{result[:500]}",
                "draft_answer": draft,
                "deferred_tools": deferred,
                "deferred_note": deferred_note,
                "elapsed_sec": elapsed,
            }
        # 假成功守卫（2026-08-25）：rc=0 但技能停在关键字体系确认门（KW-GATE）时，
        # 同 PREVIEW 门一样是确认门假成功——stdout 只有确认菜单无检索数据
        # （ct-registry 实测：--auto-confirm 不覆盖 KW-GATE，TTY 环境下 isatty 判真卡死）。
        if isinstance(result, str) and "[KW-GATE]" in result:
            return {
                "tool": tool,
                "status": "error",
                "result": f"技能停在关键字体系确认门（KW-GATE）未联网执行（需 --kw-adopt / --no-expand / 确认词）：{result[:500]}",
                "draft_answer": draft,
                "deferred_tools": deferred,
                "deferred_note": deferred_note,
                "elapsed_sec": elapsed,
            }
        return {
            "tool": tool,
            "status": "ok",
            "result": result,
            "artifacts": artifacts,
            "workdir": str(workdir),
            "draft_answer": draft,
            "deferred_tools": deferred,
            "deferred_note": deferred_note,
            "elapsed_sec": elapsed,
        }
    except subprocess.TimeoutExpired:
        return {
            "tool": tool,
            "status": "error",
            "result": f"技能执行超时（>{timeout}s）",
            "draft_answer": draft,
            "deferred_tools": deferred,
            "deferred_note": deferred_note,
            "elapsed_sec": timeout,
        }
    except FileNotFoundError as e:
        return {
            "tool": tool,
            "status": "error",
            "result": f"技能脚本不存在: {e}",
            "draft_answer": draft,
            "deferred_tools": deferred,
            "deferred_note": deferred_note,
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
