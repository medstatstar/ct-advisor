#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨技能执行器加载器（ct-base 单一真源，2026-11-20 上收）。

统一解决 ct- 技能家族里反复出现的「归一到兄弟技能执行器」需求：

  - literature_probe  → ct-literature 的 fetch_europepmc / fetch_pubmed
  - ref_verify        → ct-literature 的 verify_citations
  - registry_probe    → ct-registry 的 search_ctgov

此前三处各写一份「候选根 → 临时 sys.path → from adapters import X → 归属检查 → 清理」，
并且除 literature_probe 外都漏了关键的命名空间修复：调用方自己的 ``adapters`` 包已在
``sys.modules`` 里占名，直接 ``from adapters import X`` 只会命中自己（无该模块）→
ImportError → 静默走兜底，归一功能从未真正生效。本模块把修复收敛到一处。

核心机制（缺一不可）：
  1. 候选根去重 + 逐个尝试（兄弟目录 / coze_client.resolve_skill_dir / bundled）；
  2. 临时把 ``sys.path[0]`` 设为该根；
  3. **临时替换 ``sys.modules['adapters']``**：pop 掉调用方已加载的 adapters，让
     import 命中目标技能的 adapters 包（被加载模块内部 ``from adapters import http_utils``
     强依赖它）；加载完立即恢复原 adapters，绝不顶替调用方包；
  4. 校验加载到的模块确实来自目标根（防同名包误命中）；
  5. finally 清理临时 sys.path（``workbench`` 等命名空间包会被 sys.path 顺序污染）。

best-effort：任何失败只打印一次 WARN 并返回 None/(None,...)，绝不抛异常——
调用方据此回落到自有本地执行器，不中断主流程。

用法::

    from cross_skill_loader import load_modules

    fe, fp = load_modules(
        "ct-literature", ["fetch_europepmc", "fetch_pubmed"],
        caller_file=__file__, label="文献检索")
    # 单模块：返回 1 元组；失败返回 (None,) / (None, None)
    (vc,) = load_modules("ct-literature", ["verify_citations"],
                         caller_file=__file__, label="引文核验",
                         bundled_dirs=[os.path.join(os.path.dirname(__file__), "..", "bundled")])
"""
from __future__ import annotations

import importlib
import os
import sys
from typing import Iterable, List, Optional, Sequence, Tuple


def drop_tmp_syspath(paths: Iterable[str]) -> None:
    """移除临时插入 sys.path 的兄弟技能根（幂等）。

    为什么必须移除：多个技能根下都有无 ``__init__.py`` 的 ``workbench/`` 目录，
    Python 3 将其当命名空间包，``import workbench`` 的 ``__path__`` 按 sys.path
    顺序合并所有同名目录；兄弟根常驻 sys.path[0] 会让 workbench.server 解析到错误技能。
    """
    for p in paths:
        try:
            sys.path.remove(p)
        except ValueError:
            pass


def _candidate_roots(skill: str, caller_file: Optional[str],
                     bundled_dirs: Optional[Sequence[str]] = None,
                     use_resolve_skill_dir: bool = True) -> List[str]:
    """按优先级构造候选技能根（去重、保序）。"""
    out: List[str] = []

    def _add(p):
        if p and os.path.isdir(p) and p not in out:
            out.append(p)

    # ① bundled（发布包内自带）——若调用方显式给出
    for b in (bundled_dirs or []):
        _add(b)
    # ② 与调用方同级的兄弟技能目录（开发布局 ~/.workbuddy/skills/<skill>）
    if caller_file:
        here = os.path.dirname(os.path.abspath(caller_file))
        _add(os.path.join(os.path.dirname(here), skill))
        # 部分调用方在 adapters/ 下两级（如 adapters/coze/tests/），再向上一级兜底
        _add(os.path.join(os.path.dirname(os.path.dirname(here)), skill))
    # ③ ~ 默认安装路径
    _add(os.path.join(os.path.expanduser("~"), ".workbuddy", "skills", skill))
    # ④ coze_client.resolve_skill_dir（兼容 SkillHub 安装命名，如 ct-literature__skillhub）
    if use_resolve_skill_dir:
        try:
            import coze_client as _cc
            _add(_cc.resolve_skill_dir("~/.workbuddy/skills/%s" % skill))
        except Exception:  # noqa: BLE001 - coze_client 缺失不影响
            pass
    return out


def load_modules(skill: str, modules: Sequence[str], caller_file: Optional[str] = None,
                 label: str = "", bundled_dirs: Optional[Sequence[str]] = None,
                 attr_check: Optional[str] = None,
                 use_resolve_skill_dir: bool = True) -> Tuple[Optional[object], ...]:
    """从兄弟技能 ``<root>/adapters/`` 加载一个或多个模块。

    Args:
        skill: 技能目录名（如 "ct-literature"）。
        modules: 要加载的模块名列表（如 ["fetch_europepmc", "fetch_pubmed"]）。
                 多个模块在同一次 sys.modules 替换中加载，共享目标 adapters 包。
        caller_file: 调用方 ``__file__``，用于解析同级兄弟技能根。
        label: 日志标签（如「文献检索」）；空则用 skill。
        bundled_dirs: 额外候选根（发布包内 bundled 目录）。
        attr_check: 可选属性检查（如 search_ctgov 须有 "search"），不满足则跳过该根。
        use_resolve_skill_dir: 是否尝试 coze_client.resolve_skill_dir。

    Returns:
        与 modules 等长的元组；全部成功=各模块对象，任一失败=(None, ...)；
        找不到候选根也返回全 None。best-effort，不抛异常。
    """
    tag = label or skill
    none_tuple: Tuple[Optional[object], ...] = tuple([None] * len(modules))
    if not modules:
        return none_tuple
    roots = _candidate_roots(skill, caller_file, bundled_dirs, use_resolve_skill_dir)
    inserted: List[str] = []
    try:
        for root in roots:
            if not os.path.isdir(os.path.join(root, "adapters")):
                continue
            root_abs = os.path.abspath(root)
            if root_abs not in [os.path.abspath(p) for p in sys.path if p]:
                sys.path.insert(0, root)
                inserted.append(root)

            loaded: List[object] = []
            saved = sys.modules.get("adapters")
            try:
                # 关键：pop 掉调用方 adapters，让 import 命中目标技能的 adapters 包
                sys.modules.pop("adapters", None)
                ct_adapters = importlib.import_module("adapters")
                if not os.path.abspath(getattr(ct_adapters, "__file__", "")).startswith(root_abs):
                    print("[WARN] %s执行器命名空间未命中目标根，跳过（root=%s）" % (tag, root))
                    continue
                for name in modules:
                    mod = importlib.import_module("adapters.%s" % name)
                    if not os.path.abspath(getattr(mod, "__file__", "")).startswith(root_abs):
                        raise ImportError("模块 %s 不在目标根下" % name)
                    if attr_check and not hasattr(mod, attr_check):
                        raise ImportError("模块 %s 缺属性 %s" % (name, attr_check))
                    loaded.append(mod)
            except Exception as e:  # noqa: BLE001 - 换下一个候选根
                print("[WARN] %s执行器加载失败（%s）：%s" % (tag, root, e))
                continue
            finally:
                # 无论成败都恢复调用方 adapters，绝不让兄弟技能包顶替
                if saved is not None:
                    sys.modules["adapters"] = saved
                else:
                    sys.modules.pop("adapters", None)

            print("[INFO] %s执行层已归一到 %s：%s" % (tag, skill, root_abs))
            return tuple(loaded)
    finally:
        drop_tmp_syspath(inserted)
    return none_tuple
