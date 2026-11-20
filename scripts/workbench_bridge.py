#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""workbench_bridge.py — 对话入口(entry.py) 与 工作台(workbench/proxy) 的共享逻辑真相源。

背景（2026-11-19 用户裁定）
============================
工作台 proxy 是独立薄代理，历史上只与 entry.py 共享 session_store，导致对话侧
的 A–F 改动（文案清理 / 参数补齐 / 翻译 / 明细呈现 / stitch 干净输出）在工作台
全部缺失，两套实现漂移。本模块把这些逻辑收敛为单一真相源，两侧都调用：

  A. scrub_answer(text)         —— 出口清理（删卖点词/转介句、裸链、技能名单一语言）
  C. enrich_params(steps, card) —— plan 参数补齐 + 中译英（registry 双源 / safety drug,event / 检索词翻译）
  D. stitch_clean(spec)         —— 干净 stitch（去标题/原始问题行、disclaimer 一行）
  E. render_detail_list(summary)—— 明细清单（试验登记号 / 文献标题 / 2×2 与 PRR/ROR）

设计约束
========
* 薄封装：不重复实现，re-export 既有函数（confirm_menu / plan_runner / stitch_results）。
* 零 LLM 决策、零触网：所有函数纯本地确定性（翻译器的联网兜底沿用其自身开关）。
* 导入健壮：部署扁平包缺 scripts/ 时，函数由 ROOT 内嵌副本提供；导入失败不阻断调用方。
* E 的 render_detail_list 是纯函数，从云端 full_analysis_node 同步而来（保持逐字一致）。

用法
====
    from workbench_bridge import scrub_answer, enrich_params, stitch_clean, render_detail_list
"""
from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_ROOT = _SCRIPT_DIR.parent
# 保证真源目录在 sys.path（对话侧与工作台侧都能 import 到 adapters / scripts）
for _p in (str(_SCRIPT_DIR), str(_SKILL_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── A. 出口文案清理（re-export confirm_menu.scrub_egress_promo）──────────────
def scrub_answer(text: str) -> str:
    """删除云端正文的卖点词/转介句、裸链显示、技能名单一语言；菜单块原样保留。

    与对话入口 entry.py 出口调用的是同一函数（confirm_menu.scrub_egress_promo），
    保证两侧输出逐字一致。导入失败时降级返回原文（fail-open，绝不阻断）。
    """
    try:
        from adapters.confirm_menu import scrub_egress_promo
        return scrub_egress_promo(text)
    except Exception:  # noqa: BLE001 - 模块缺失 → 原样返回
        return text or ""


# ── C. plan 参数补齐 + 检索词翻译（re-export plan_runner）───────────────────
def enrich_params(steps: List[dict], card: Optional[dict] = None,
                  contract: Optional[dict] = None) -> List[dict]:
    """对 plan steps 做领域参数补齐（registry 双源 / safety drug+event / topic+cond 翻译）。

    直接调用 plan_runner._enrich_domain_params（原地修改 steps），返回 steps 便于链式。
    contract 缺省时加载 plan_contract.json。导入失败时原样返回（fail-open）。
    """
    try:
        from adapters import plan_runner as pr
        cfg = contract or pr.load_contract()
        pr._enrich_domain_params(steps, card or {}, cfg)
        return steps
    except Exception:  # noqa: BLE001
        return steps


def load_contract() -> dict:
    """加载 plan 契约（供调用方复用，避免各自读文件造成漂移）。"""
    try:
        from adapters.plan_runner import load_contract as _lc
        return _lc()
    except Exception:  # noqa: BLE001
        return {}


# ── D. 干净 stitch（re-export stitch_results.stitch）─────────────────────────
def stitch_clean(spec: dict) -> str:
    """本地缝合技能产物为干净答案（去标题/原始问题行、disclaimer 一行）。

    与对话入口 entry.py --stitch 调用同一函数，保证两侧输出一致。
    """
    try:
        import stitch_results
        return stitch_results.stitch(spec)
    except Exception:  # noqa: BLE001
        return ""


# ── E. 明细清单渲染（从云端 full_analysis_node 同步的纯函数）───────────────
# ── 共享的本地技能 CLI extra 参数（对照对话侧 confirm_menu._QUICK_CMD）─────
# 工作台 proxy 的 RUN_SKILL_TOOLS 与 index.html 的 SKILL_META 都应使用这里的 extra，
# 保证与对话侧快速命令口径一致（默认不出 Excel）。单一真相源，避免两处漂移。
LOCAL_SKILL_EXTRA: Dict[str, tuple] = {
    "ct-registry": ("--auto-confirm", "--run", "--print-summary", "--kw-adopt", "--no-excel"),
    "ct-safety": ("--run", "--no-excel"),
    "ct-literature": ("--run", "--no-xlsx", "--no-html"),
}


def _list_truncation_hint(shown: int, total, noun: str, skill: str) -> str:
    """列表被截断时提示「仅列前 N 条 / 完整清单用技能单独取」（2026-11-20 用户要求）。

    仅当命中总数可解析为整数且 > 实际展示条数时才提示——全列出来时不说「仅列部分」，
    避免误导。total 可能是 int / str / "?"，解析失败一律不提示（据实、不猜）。
    与 adapters/plan_assemble_local.py 同名函数逐字一致。
    """
    try:
        t = int(total)
    except (TypeError, ValueError):
        return ""
    if t <= shown:
        return ""
    return ("  ℹ️ 上方仅展示前 %d 条%s（共命中 %d 条）；"
            "完整清单请单独调用 `%s` 技能获取。"
            % (shown, noun, t, skill))


def render_detail_list(summary: dict) -> str:
    """把 brief summary 的 sample_trials / top_works / 2×2 渲染成可读清单。

    纯字符串渲染，零依赖、零触网、零 LLM。与云端
    adapters/coze/src/graphs/nodes/full_analysis_node.py::_render_detail_list 逐字一致，
    以保证工作台明细呈现与对话侧二次综合的结果同构。
    """
    out = []

    def _clip(v, n):
        s = str(v if v is not None else "").strip()
        return (s[:n] + "…") if len(s) > n else s

    trials = (summary or {}).get("sample_trials") or []
    if isinstance(trials, list) and trials:
        out.append("**在研/相关试验明细（前 %d 条）：**" % min(10, len(trials)))
        for j, t in enumerate(trials[:10], 1):
            if not isinstance(t, dict):
                continue
            rid = _clip(t.get("id"), 24) or "登记号未提供"
            title = _clip(t.get("title"), 90)
            phase = _clip(t.get("phase"), 16)
            status = _clip(t.get("status"), 20)
            sponsor = _clip(t.get("sponsor"), 30)
            out.append("  %d. `%s`｜%s｜分期:%s｜状态:%s｜申办方:%s"
                       % (j, rid, title, phase or "—", status or "—", sponsor or "—"))
        _hint = _list_truncation_hint(min(10, len(trials)), (summary or {}).get("total_hits"),
                                      "试验", "ct-registry")
        if _hint:
            out.append(_hint)

    works = (summary or {}).get("top_works") or []
    if isinstance(works, list) and works:
        out.append("**相关文献明细（前 %d 条）：**" % min(10, len(works)))
        for j, w in enumerate(works[:10], 1):
            if not isinstance(w, dict):
                continue
            title = _clip(w.get("title"), 110) or "标题未提供"
            year = _clip(w.get("year"), 6)
            journal = _clip(w.get("journal"), 40)
            doi = _clip(w.get("doi"), 40)
            out.append("  %d. %s（%s；%s%s）"
                       % (j, title, year or "年份未知", journal or "期刊未知",
                          ("；DOI:" + doi) if doi else ""))
        _hint = _list_truncation_hint(min(10, len(works)), (summary or {}).get("total_hits"),
                                      "文献", "ct-literature")
        if _hint:
            out.append(_hint)

    if (summary or {}).get("counts_2x2") or (summary or {}).get("measures"):
        c = summary.get("counts_2x2") or {}
        m = summary.get("measures") or {}
        out.append("**安全信号数值（2×2 与 PRR/ROR 及 95%CI）：**")
        out.append("  2×2: a=%s b=%s c=%s d=%s｜PRR=%s %s｜ROR=%s %s"
                   % (c.get("a", "—"), c.get("b", "—"), c.get("c", "—"), c.get("d", "—"),
                      m.get("prr", "—"), m.get("prr_ci95", "—"),
                      m.get("ror", "—"), m.get("ror_ci95", "—")))
    return "\n".join(out)


# ── G. 工作台产物白名单（2026-11-19 用户裁定：iframe 预览 + 本次运行白名单）───
class ArtifactRegistry:
    """一次性 token → 产物绝对路径 的安全白名单。

    工作台 /api/run-skill 跑完技能后，把产物路径登记进来并返回 token 给前端；
    前端用 /api/artifact?token=xxx 读取。只有登记过的路径可读，防任意文件访问。
    token 短时有效（默认 30 分钟）、单次读取后可保留（iframe 可能重载），过期自动清理。
    纯内存、零持久化——服务重启即失效，符合最小暴露原则。
    """

    def __init__(self, ttl_sec: int = 1800):
        self._ttl = ttl_sec
        self._store: Dict[str, Tuple[str, float]] = {}
        self._lock = None  # 延迟创建（避免 import threading 到扁平包）

    def _get_lock(self):
        if self._lock is None:
            import threading
            self._lock = threading.Lock()
        return self._lock

    def _purge(self):
        now = time.time()
        with self._get_lock():
            dead = [t for t, (_, exp) in self._store.items() if exp < now]
            for t in dead:
                self._store.pop(t, None)

    def register(self, path: str) -> str:
        """登记一个绝对路径，返回一次性 token。"""
        self._purge()
        token = uuid.uuid4().hex
        with self._get_lock():
            self._store[token] = (str(path), time.time() + self._ttl)
        return token

    def resolve(self, token: str) -> Optional[str]:
        """token → 绝对路径；无效/过期返回 None。"""
        if not token:
            return None
        self._purge()
        with self._get_lock():
            entry = self._store.get(token)
            return entry[0] if entry else None

    def size(self) -> int:
        self._purge()
        with self._get_lock():
            return len(self._store)


# 模块级单例（proxy import 后全局共用）
ARTIFACTS = ArtifactRegistry()


# 允许呈现的产物类型（白名单后缀）
ARTIFACT_SUFFIXES = (".html", ".htm", ".md")


def collect_artifacts(out_dir, registry: Optional[ArtifactRegistry] = None) -> List[dict]:
    """扫描产物目录，登记 HTML/MD 文件并返回给前端的清单。

    返回 [{"name": "faers_report.html", "title": "...", "token": "...", "kind": "html|md"}, ...]
    HTML 优先排序（适合 iframe 直接渲染）。目录不存在或为空返回 []。
    """
    d = Path(out_dir) if out_dir else None
    if d is None or not d.is_dir():
        return []
    reg = registry or ARTIFACTS
    files = [f for f in d.rglob("*")
             if f.is_file() and f.suffix.lower() in ARTIFACT_SUFFIXES]
    # HTML 优先，MD 次之；同名取 HTML
    files.sort(key=lambda p: (0 if p.suffix.lower() in (".html", ".htm") else 1, p.name))
    seen, out = set(), []
    for f in files:
        stem = f.stem.lower()
        if stem in seen:
            continue
        seen.add(stem)
        out.append({
            "name": f.name,
            "kind": "html" if f.suffix.lower() in (".html", ".htm") else "md",
            "token": reg.register(str(f.resolve())),
        })
    return out


# ── 离线自测 ────────────────────────────────────────────────────────────────
def self_test() -> int:
    ok = True

    def chk(label, cond):
        nonlocal ok
        print("  [%s] %s" % ("PASS" if cond else "FAIL", label))
        ok = ok and cond

    print("workbench_bridge 离线自测（不触网）")
    print("-" * 62)
    # A: scrub 与原函数一致
    try:
        from adapters.confirm_menu import scrub_egress_promo as _orig
        demo = "该问题需要使用 ct-registry 获取完整信息：@skill:ct-registry。正文保留。"
        chk("scrub_answer 与原函数逐字一致", scrub_answer(demo) == _orig(demo))
    except Exception:
        chk("scrub_answer 可调用", isinstance(scrub_answer("干净正文"), str))
    # C: enrich_params 补双源 + 翻译
    cfg = load_contract()
    if cfg:
        steps = [{"skill": "ct-registry", "params": {"cond": "信迪利单抗"},
                  "depends_on": [], "expect": "registry_landscape", "prefill": True}]
        enrich_params(steps, {"original_question": "信迪利单抗治疗肝癌"}, cfg)
        p = steps[0]["params"]
        chk("enrich_params 补 with_cde", p.get("with_cde") is True)
        chk("enrich_params cde_keyword 中文", p.get("cde_keyword") == "信迪利单抗")
    # D: stitch_clean 可调用
    chk("stitch_clean 可调用", isinstance(stitch_clean({"results": []}), str))
    # E: 明细渲染
    detail = render_detail_list({
        "sample_trials": [{"id": "NCT1", "title": "Trial A", "status": "RECRUITING"}],
        "top_works": [{"title": "Paper B", "year": 2024, "journal": "J Test"}],
        "total_hits": 20,
        "counts_2x2": {"a": 7, "b": 1177, "c": 22281, "d": 21030694},
        "measures": {"prr": 5.98, "prr_ci95": [2.93, 12.2]},
    })
    chk("明细含试验登记号", "NCT1" in detail)
    chk("明细含文献标题", "Paper B" in detail)
    chk("列表截断提示（20>1）", "仅展示前 1 条" in detail and "共命中 20 条" in detail
        and "ct-registry" in detail and "ct-literature" in detail)
    chk("未截断时不误报", "共命中" not in render_detail_list({
        "sample_trials": [{"id": "NCT1", "title": "Trial A"}], "total_hits": 1}))
    chk("明细含 2×2 数值", "a=7" in detail and "5.98" in detail)
    # G: 产物白名单
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "faers_report.html").write_text("<html>ok</html>", encoding="utf-8")
        (Path(td) / "faers_report.xlsx").write_text("x", encoding="utf-8")  # 非白名单后缀
        arts = collect_artifacts(td)
        chk("产物只收 HTML/MD", len(arts) == 1 and arts[0]["kind"] == "html")
        tok = arts[0]["token"]
        chk("token 可解析到真实路径", ARTIFACTS.resolve(tok) == str((Path(td) / "faers_report.html").resolve()))
        chk("无效 token 返回 None", ARTIFACTS.resolve("bogus") is None)
        chk("路径校验：任意路径不可读", ARTIFACTS.resolve("/etc/passwd") is None)
    print("-" * 62)
    print("结论：%s" % ("✅ 全部通过" if ok else "❌ 存在 FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(self_test())
