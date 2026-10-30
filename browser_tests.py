#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ct-advisor 浏览器交互测试统一入口（W2B）。

暴露 run(test: BrowserTest)，由 ct-base 的 W2B 层统一调度：
框架负责 Playwright 生命周期、本地服务、失败截图与控制台监听，
本文件只写断言。

选择器来源：workbench/index.html 的真实 DOM（2026-10-28 核对）——
  #qinput 输入框 / #sendBtn / #clearBtn / #appTitle / #charHint /
  #wb-lang 语言 / #wb-side 侧栏 / #toast / .view + [data-view] 多视图 /
  LS.lang = "wb_ctadvisor_lang_"
"""
from ctqa.browser import BrowserTest

LS_LANG = "wb_ctadvisor_lang_"


def _txt(test, selector: str) -> str:
    """安全取文本：选择器不存在时返回空串，而不是让 inner_text 抛超时。

    断言失败要指向"功能不对"，不能让"选择器写错"变成 30 秒超时把整层打断。
    """
    return test.eval(
        "(sel) => { const e = document.querySelector(sel);"
        " return e ? (e.textContent || '').trim() : ''; }", selector) or ""


def _val(test, selector: str) -> str:
    return test.eval(
        "(sel) => { const e = document.querySelector(sel);"
        " return e ? (e.value || '') : ''; }", selector) or ""


def run(test: BrowserTest):
    test.goto("/")

    # ---- 1. 基础元素可见性 ----
    test.assert_visible("#qinput", True, tags=("ui", "smoke"))
    test.assert_visible("#sendBtn", True, tags=("ui", "smoke"))
    test.assert_visible("#wb-lang", True, tags=("i18n", "smoke"))
    test.assert_visible("#view-console", True, tags=("nav", "smoke"))
    test.assert_true(
        "标题含 ct-advisor",
        "ct-advisor" in _txt(test, "#appTitle"),
        detail="appTitle=%r" % _txt(test, "#appTitle"),
        tags=("ui", "smoke"),
    )

    # ---- 2. 多视图导航 ----
    test.click('[data-view="history"]')
    test.wait_for_timeout(250)
    test.assert_visible("#view-history", True, tags=("nav",))
    test.assert_visible("#view-console", False, tags=("nav",))

    test.click('[data-view="console"]')
    test.wait_for_timeout(250)
    test.assert_visible("#view-console", True, tags=("nav",))

    # ---- 3. 输入交互 + 字数提示 ----
    test.fill("#qinput", "样本量估算")
    test.wait_for_timeout(200)
    test.assert_true(
        "输入后字数提示同步更新",
        "5" in _txt(test, "#charHint"),
        detail="charHint=%r" % _txt(test, "#charHint"),
        tags=("input",),
    )
    test.assert_value("#qinput", "样本量估算", tags=("input",))
    test.fill("#qinput", "")

    # ---- 4. 语言切换 + 持久化 ----
    zh_title = _txt(test, "#appTitle")
    test.click("#wb-lang")
    test.wait_for_timeout(400)
    en_title = _txt(test, "#appTitle")
    test.assert_true(
        "语言切换 zh→en 生效",
        zh_title != en_title,
        detail="zh=%r en=%r" % (zh_title, en_title),
        tags=("i18n",),
    )
    stored = test.eval("(k) => localStorage.getItem(k)", LS_LANG)
    test.assert_true(
        "语言选择写入 localStorage",
        stored == "en",
        detail="stored=%r" % stored,
        tags=("i18n", "persistence"),
    )

    test.reload(wait_for_selector="#qinput")
    test.wait_for_timeout(400)
    test.assert_true(
        "刷新后语言保持 en",
        _txt(test, "#appTitle") == en_title,
        detail="刷新后=%r" % _txt(test, "#appTitle"),
        tags=("i18n", "persistence"),
    )

    # 复原中文，避免影响后续用例
    test.click("#wb-lang")
    test.wait_for_timeout(300)
    test.assert_true(
        "语言可切回 zh",
        _txt(test, "#appTitle") == zh_title,
        detail="当前=%r" % _txt(test, "#appTitle"),
        tags=("i18n",),
    )

    # ---- 5. 侧栏折叠 ----
    test.eval("() => toggleSide()")
    test.wait_for_timeout(250)
    test.assert_true(
        "侧栏折叠生效（.app.side-collapsed）",
        "side-collapsed" in (test.attr(".app", "class") or ""),
        tags=("sidebar",),
    )
    test.eval("() => toggleSide()")
    test.wait_for_timeout(250)
    test.assert_true(
        "侧栏可还原",
        "side-collapsed" not in (test.attr(".app", "class") or ""),
        tags=("sidebar",),
    )

    # ---- 6. Toast ----
    test.eval("() => toast('ctqa-test')")
    test.wait_for_timeout(200)
    test.assert_visible("#toast.show", True, tags=("toast",))
    test.assert_true(
        "Toast 文案透传",
        "ctqa-test" in _txt(test, "#toast"),
        detail="toast=%r" % _txt(test, "#toast"),
        tags=("toast",),
    )

    # ---- 7. 历史视图可渲染（空态也必须有容器） ----
    test.click('[data-view="history"]')
    test.wait_for_timeout(300)
    test.assert_true(
        "历史视图渲染出容器",
        test.eval("() => !!document.getElementById('view-history')"),
        tags=("history",),
    )
    test.assert_true(
        "历史视图含「清空历史」入口",
        test.eval("() => !!document.getElementById('clearBtn')"),
        tags=("history",),
    )
    test.click('[data-view="console"]')
    test.wait_for_timeout(200)

    # ---- 8. 控制台无异常 ----
    test.assert_console_clean(tags=("runtime",))
