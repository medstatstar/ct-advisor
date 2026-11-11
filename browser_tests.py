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

    # ---- 3b. 长文档引导（P2-④）：>2000 字常驻提示 + 一键移到附件框 ----
    # 背景：近 30 天 12 条 >1000 字、2 条 >3000 字的粘贴长文仍从问题框直发，
    # 附件通道仅 10/217（4.6%）。原实现只在发送后弹一次 toast（1.8s），
    # 改为输入过程中常驻 inline 提示 + 一键转入附件通道。
    _short = "短问题"
    test.fill("#qinput", _short)
    test.wait_for_timeout(200)
    test.assert_visible("#longInputHint", False, tags=("long_input",))

    _long = "这是一段用于测试长文档引导的文本内容。" * 120   # 2280 字 > 阈值 2000
    test.fill("#qinput", _long)
    test.wait_for_timeout(250)
    test.assert_visible("#longInputHint", True, tags=("long_input",))
    test.assert_true(
        "长输入提示含字数统计",
        str(len(_long)) in _txt(test, "#longInputHint"),
        detail="hint=%r" % _txt(test, "#longInputHint"),
        tags=("long_input",),
    )
    test.assert_true(
        "长输入提示含「附件」引导动作",
        "附件" in _txt(test, "#longInputHint"),
        detail="hint=%r" % _txt(test, "#longInputHint"),
        tags=("long_input",),
    )
    test.click("#longInputMoveBtn")
    test.wait_for_timeout(250)
    test.assert_value("#qinput", "", tags=("long_input",))
    test.assert_true(
        "长文已转入附件框（内容不丢失）",
        _val(test, "#attachInput").strip() == _long,
        detail="attach len=%d expect=%d" % (len(_val(test, "#attachInput")), len(_long)),
        tags=("long_input",),
    )
    test.assert_visible("#longInputHint", False, tags=("long_input",))
    # 清理，避免影响后续用例
    test.fill("#qinput", "")
    test.fill("#attachInput", "")
    test.wait_for_timeout(150)

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

    # ---- 8. 流式阶段提示（③①②）纯逻辑 ----
    # W2B 层无后端（框架只起静态服务），故这里只验「不依赖网络就能算对」的部分：
    # 阶段名映射、i18n 键完整性、进度文案兜底。端到端草稿渲染在 W2 层 L3 覆盖。
    # 阶段/草稿纯函数经 window._wbStream 暴露（index.html 主体在 IIFE 内，取不到全局）。
    for _node, _expect in (("full_analysis", "生成深入分析"),
                           ("selfcheck", "质量自检与修订"),
                           ("doc_ingest", "解析上传文档"),
                           ("not_a_real_node", "处理中")):
        test.assert_true(
            "阶段名映射 %s → %s" % (_node, _expect),
            _expect in (test.eval("(n) => window._wbStream.stageLabel(n)", _node) or ""),
            detail="实际=%r" % test.eval("(n) => window._wbStream.stageLabel(n)", _node),
            tags=("stream", "stage"),
        )
    test.assert_true(
        "中英文均含全部流式 i18n 键",
        test.eval("""() => {
            const need = ['stageDocIngest','stageCacheCheck','stageProtocolParams',
              'stageValidateParams','stageOrganize','stageFullAnalysis','stageSelfcheck',
              'stageQcChecklist','stageToolRouter','stageUnknown','progStageRun',
              'progStageDone','draftTitle'];
            const all = window._wbStream.allI18n();
            return ['zh','en'].every(loc => need.every(k => (all[loc]||{})[k]));
        }"""),
        detail="见 allI18n 输出",
        tags=("stream", "i18n"),
    )
    test.assert_true(
        "无阶段信息时进度文案退回「已 Ns」",
        "已" in (test.eval("() => window._wbStream.progText()") or ""),
        detail="progText=%r" % test.eval("() => window._wbStream.progText()"),
        tags=("stream", "stage"),
    )
    test.assert_true(
        "草稿事件处理函数存在（供 SSE custom 帧调用）",
        test.eval("() => typeof window._wbStream.onEvent === 'function' "
                  "&& typeof window._wbStream.draftHandle === 'function'"),
        tags=("stream",),
    )

    # ---- 9. 控制台无异常 ----
    test.assert_console_clean(tags=("runtime",))
