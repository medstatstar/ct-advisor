#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tone_matcher.py — ct-advisor 语气写作（clarify_loop 增强版）的提取器。

纯本地、零网络出域，仅依赖 Python 标准库（json / re / argparse / sys）。
从用户提供的写作样本（文章 / 邮件 / 报告片段）提取**表达风格**特征，
生成 ``tone_profile.json``，供 ``refine_answer.py --tone`` 注入 Coze 精校 prompt，
让最终答案以与用户一致的语气书写。

🔴 硬闸（HARD GATE，不可绕过）：
  本提取器**只迁移表达风格**，绝不迁移样本中的事实内容——
  日期 / 时间、项目名 / 产品名、人名 / 机构名、具体观点 / 结论、数字指标
  一律不进入 profile。Coze 端注入时也附带同样的风格硬闸指令。
  理由：样本可能含过时信息，照搬会污染当前答案。

调用方式：
  python scripts/tone_matcher.py --samples-inline '["段落1","段落2"]' --out tone_profile.json
  python scripts/tone_matcher.py --samples-file samples.txt --out tone_profile.json
  python scripts/tone_matcher.py --self-test      # 最小内联自测，不落临时文件

输入：
  --samples-inline : JSON 数组字符串，含 1+ 个写作样本文本
  --samples-file   : 文本文件路径，按空行分段（每段算一个样本）
  --out            : 输出 tone_profile.json 路径（缺省 stdout）

输出 tone_profile.json 结构：
  {
    "schema": "ct-advisor.tone_profile/v1",
    "generated_at": "ISO-8601",
    "style_only": true,            # 硬闸声明：仅风格、无事实
    "samples": N,                  # 参与提取的样本数
    "features": {
      "sentence_length": "short|medium|long",
      "formality": "formal|semi-formal|casual",
      "second_person": bool,       # 是否常用"你/您"
      "first_person": bool,        # 是否常用"我/我们"
      "paragraph_avg_chars": int,
      "uses_lists": bool,
      "rhetoric": ["设问","排比", ...],
      "transitions": ["但是","因此", ...],   # 常用连接词（风格层）
      "term_style": "首注缩写|全称|混用",
      "emoji": bool,
      "punctuation": "全角|半角"
    },
    "hard_gate": "仅使用上述表达风格；禁止搬用样本中的日期/项目/人物/观点/数字"
  }
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

# 与 refine_answer.py / clarify_loop.py 一致：强制三流 UTF-8，避免中文/emoji 在
# Windows 控制台（cp936）下被错误解码/编码。
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 硬闸正则：命中即视为「事实内容」，禁止进入风格 profile
# ---------------------------------------------------------------------------
_FACT_PATTERNS = [
    (r"\d{4}[-/年.]\d{1,2}([-/月.]\d{1,2})?", "日期"),
    (r"\d{1,2}[:：]\d{2}", "时刻"),
    (r"(20|19)\d{2}年", "年份"),
    (r"(项目|课题|试验|研究)\s*[:：]?\s*[\u4e00-\u9fffA-Za-z0-9_\-]{2,20}", "项目/研究名"),
    (r"(公司|机构|医院|大学|药企|申办方)\s*[:：]?\s*[\u4e00-\u9fffA-Za-z&]{2,20}", "机构名"),
    (r"(Dr\.|Mr\.|Ms\.|教授|博士|主任医师|PI)\s*[\u4e00-\u9fffA-Za-z]{1,12}", "人名"),
    (r"[\u4e00-\u9fff]{1,4}(率|比|值|分|元|万|亿|%|％)\s*[:：=]?\s*[\d.]+", "指标数字"),
]
_FACT_RE = [re.compile(p) for p, _ in _FACT_PATTERNS]

# 句子切分（中英文句号 / 问号 / 感叹号 / 换行）
_SENT_SPLIT = re.compile(r"[。！？!?\n]+")
_CJK = re.compile(r"[\u4e00-\u9fff]")


def _detect_factual_leak(text: str) -> List[str]:
    """检测文本中是否含事实内容（仅用于告警，不纳入 profile）。"""
    leaks: List[str] = []
    for rx, label in zip(_FACT_RE, [l for _, l in _FACT_PATTERNS]):
        if rx.search(text):
            leaks.append(label)
    return leaks


def _split_sentences(text: str) -> List[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]


def _split_paragraphs(text: str) -> List[str]:
    # 按空行或单换行分段
    paras = re.split(r"\n\s*\n|\n", text)
    return [p.strip() for p in paras if p.strip()]


def _build_profile(samples: List[str]) -> Dict[str, Any]:
    """从样本列表提取纯风格特征。"""
    all_text = "\n".join(samples)
    sentences = _split_sentences(all_text)
    paragraphs = _split_paragraphs(all_text)

    # 句子长度（按字符，混合中英）
    sent_lens = [len(s) for s in sentences] or [0]
    avg_sent = sum(sent_lens) / len(sent_lens)
    if avg_sent < 25:
        sentence_length = "short"
    elif avg_sent < 60:
        sentence_length = "medium"
    else:
        sentence_length = "long"

    # 正式度：书面连词 / 术语密度
    formal_markers = ["因此", "然而", "此外", "基于", "依据", "综上所述", "由此可见",
                      "具体而言", "换言之", "鉴于", "据此", "从而", "进而"]
    casual_markers = ["咱们", "其实吧", "说白了", "简单说", "说真的", "说实话",
                      "哈哈", "哎", "嗯", "那个", "就是个", "搞个"]
    f_count = sum(all_text.count(m) for m in formal_markers)
    c_count = sum(all_text.count(m) for m in casual_markers)
    if f_count >= c_count and f_count > 0:
        formality = "formal"
    elif c_count > f_count:
        formality = "casual"
    else:
        formality = "semi-formal"

    # 第二/第一人称：CJK 字符间无 \b 词边界，用子串匹配（风格层判断，宽松即可）
    second_person = bool(re.search(r"你|您|你们|咱", all_text))
    first_person = bool(re.search(r"我|我们|咱们|我方", all_text))

    para_lens = [len(p) for p in paragraphs] or [0]
    paragraph_avg_chars = int(sum(para_lens) / len(para_lens))

    uses_lists = bool(re.search(r"^\s*[-*\u2022]|\n\s*\d+[.、)]", all_text, re.M))

    # 修辞
    rhetoric: List[str] = []
    if re.search(r"[？?]\s*$", all_text) or re.search(r"[？?]\s*\n", all_text):
        # 设问：问句后紧跟作答
        qs = [s for s in sentences if s.endswith("？") or s.endswith("?")]
        if qs and len(qs) >= 1:
            rhetoric.append("设问")
    if re.search(r"(，|\、)([^\，\、]{2,8})?\1", all_text):
        rhetoric.append("排比")
    if re.search(r"例如|比如|如：|诸如", all_text):
        rhetoric.append("举例")
    if re.search(r"第一|首先|其一|一是|一则", all_text):
        rhetoric.append("分点列举")

    # 常用连接词（风格层，非事实）
    transition_pool = ["但是", "所以", "因此", "不过", "而且", "同时", "另外",
                       "也就是说", "换句话说", "换句话说", "换句话说", "总之",
                       "一方面", "另一方面", "相比之下", "换言之"]
    transitions = [t for t in transition_pool if t in all_text]

    # 术语风格：是否首注缩写
    term_style = "混用"
    if re.search(r"[A-Za-z]{2,}\s*[（(][\u4e00-\u9fff]+[）)]", all_text) or re.search(r"[\u4e00-\u9fff]+（[A-Za-z]+）", all_text):
        term_style = "首注缩写"
    elif re.search(r"\b(OS|PFS|ORR|AE|HR|CI|ITT|FAS)\b", all_text):
        term_style = "缩写为主"

    emoji = bool(re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", all_text))

    punctuation = "全角" if re.search(r"[，。！？；：]", all_text) else "半角"

    # 硬闸校验：若有任何事实泄漏，仍只产出风格（事实不进 features），但记录告警
    leaks = _detect_factual_leak(all_text)

    features = {
        "sentence_length": sentence_length,
        "formality": formality,
        "second_person": second_person,
        "first_person": first_person,
        "paragraph_avg_chars": paragraph_avg_chars,
        "uses_lists": uses_lists,
        "rhetoric": rhetoric,
        "transitions": transitions[:8],
        "term_style": term_style,
        "emoji": emoji,
        "punctuation": punctuation,
    }

    return {
        "schema": "ct-advisor.tone_profile/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "style_only": True,
        "samples": len(samples),
        "features": features,
        "hard_gate": "仅使用上述表达风格；禁止搬用样本中的日期/项目/人物/观点/数字",
        # 仅供人类审计，不进入 Coze prompt 的风格内容
        "_factual_leak_warning": leaks if leaks else [],
    }


def _render_prompt(profile: Dict[str, Any]) -> str:
    """把 profile 渲染成可注入 Coze prompt 的风格指令（不含事实）。"""
    f = profile.get("features", {})
    parts: List[str] = []
    parts.append(
        "[STYLE-ONLY TONE] 请以与用户样本一致的**表达风格**书写最终答案，"
        "但严禁搬用样本中的任何事实内容（日期/项目/人物/观点/数字）。"
    )
    sl = f.get("sentence_length")
    if sl == "short":
        parts.append("- 句式偏短，单句说完不拖沓。")
    elif sl == "long":
        parts.append("- 句式偏长，允许复合句与展开。")
    else:
        parts.append("- 句式中等长度。")
    fm = f.get("formality")
    if fm == "formal":
        parts.append("- 书面正式，多用‘因此/基于/综上所述’等连接。")
    elif fm == "casual":
        parts.append("- 口语轻松，可直接用‘你/咱们’，避免生硬书面词。")
    else:
        parts.append("- 半正式，书面与口语平衡。")
    if f.get("second_person"):
        parts.append("- 善用第二人称‘你/您’拉近距离。")
    if f.get("first_person"):
        parts.append("- 可用第一人称‘我/我们’陈述。")
    if f.get("uses_lists"):
        parts.append("- 适当用列表/分点组织信息。")
    if f.get("rhetoric"):
        parts.append("- 修辞：" + "、".join(f["rhetoric"]) + "。")
    if f.get("transitions"):
        parts.append("- 常用连接词：" + "、".join(f["transitions"][:5]) + "。")
    if f.get("term_style") == "首注缩写":
        parts.append("- 术语首现写全称+（缩写），后续统一缩写。")
    if f.get("emoji"):
        parts.append("- 可适度使用 emoji 增强表达。")
    parts.append(f"[HARD GATE] {profile.get('hard_gate','')}")
    return "\n".join(parts)


def run_match(samples: List[str]) -> Dict[str, Any]:
    """核心：从样本提取风格 profile（dict）。"""
    if not samples or not any(s.strip() for s in samples):
        # 容错：空样本回退为空风格（下游照常继续，不可中断）
        return {
            "schema": "ct-advisor.tone_profile/v1",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "style_only": True,
            "samples": 0,
            "features": {},
            "hard_gate": "仅使用风格；禁止搬用样本事实",
            "_factual_leak_warning": [],
        }
    return _build_profile([s for s in samples if s and s.strip()])


def _read_payload(args) -> List[str]:
    if args.samples_inline:
        try:
            obj = json.loads(args.samples_inline)
            if isinstance(obj, list):
                return [str(x) for x in obj]
            if isinstance(obj, str):
                return [obj]
        except Exception:
            pass
        return [args.samples_inline]
    if args.samples_file:
        from pathlib import Path
        try:
            text = Path(args.samples_file).read_text(encoding="utf-8")
        except Exception:
            return []
        # 按空行分段，每段一个样本
        return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return []


def _self_test() -> int:
    """最小内联自测：验证提取可调用、风格硬闸生效、不死循环。不落临时文件。"""
    ok = True

    # 场景 1：含日期/人名的样本 → 仍只产出风格，事实不进 features
    r1 = run_match([
        "2024年3月，我们和张医生讨论了OS的优化方案。因此，我认为应该先做样本量估算。",
        "你看看这个设计，其实吧，关键在于把握度。比如 power 设 0.9 就好。",
    ])
    cond1 = (
        r1["style_only"] is True
        and isinstance(r1["features"], dict)
        and "2024" not in json.dumps(r1["features"], ensure_ascii=False)
        and "张医生" not in json.dumps(r1["features"], ensure_ascii=False)
        and r1["features"].get("second_person") is True
        and r1["features"].get("formality") in ("casual", "semi-formal", "formal")
    )
    print(f"[self-test] scenario1 style-only -> {cond1} : {'PASS' if cond1 else 'FAIL'}")
    ok = ok and cond1

    # 场景 2：渲染 prompt 不含事实
    prompt = _render_prompt(r1)
    cond2 = "2024" not in prompt and "张医生" not in prompt and "HARD GATE" in prompt
    print(f"[self-test] scenario2 prompt-clean -> {cond2} : {'PASS' if cond2 else 'FAIL'}")
    ok = ok and cond2

    # 场景 3：空样本容错
    r3 = run_match([])
    cond3 = r3["samples"] == 0 and isinstance(r3["features"], dict)
    print(f"[self-test] scenario3 empty -> {cond3} : {'PASS' if cond3 else 'FAIL'}")
    ok = ok and cond3

    print(f"[self-test] overall: {'ALL PASS' if ok else 'FAILED'}")
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="ct-advisor tone matcher (pure-local, style-only)")
    ap.add_argument("--samples-inline", help="JSON array of sample texts (highest priority)")
    ap.add_argument("--samples-file", help="text file, paragraphs split by blank lines")
    ap.add_argument("--out", help="output tone_profile.json path (default: stdout)")
    ap.add_argument("--as-prompt", action="store_true",
                    help="output the Coze-injectable style prompt instead of the raw JSON")
    ap.add_argument("--self-test", action="store_true", help="run minimal inline self-test")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(_self_test())

    samples = _read_payload(args)
    try:
        profile = run_match(samples)
    except Exception as e:  # noqa: BLE001
        profile = {
            "schema": "ct-advisor.tone_profile/v1",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "style_only": True,
            "samples": 0,
            "features": {},
            "hard_gate": "仅使用风格；禁止搬用样本事实",
            "_factual_leak_warning": [],
            "error": f"{type(e).__name__}: {e}",
        }

    if args.as_prompt:
        out = _render_prompt(profile)
    else:
        out = json.dumps(profile, ensure_ascii=False, indent=2)

    if args.out:
        from pathlib import Path
        try:
            Path(args.out).write_text(out + "\n", encoding="utf-8")
            sys.stderr.write(f"[tone_matcher] profile written: {args.out}\n")
        except Exception as e:
            sys.stderr.write(f"[tone_matcher] write failed: {e}\n")
            sys.exit(1)
    else:
        sys.stdout.write(out)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
