#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc_comments.py — Word 批注操作（§29，2026-11-05 新增）

功能：向已有 Word 批注追加回复（保留原批注作者与内容）。

适用场景：
  - 评阅意见（如 Siru Li 的 21 条批注）需要逐条回复；
  - 统计评估结论需要注入原批注，生成可对照原文的文档；
  - 任何需要「在原批注内追加结构化回复」的场景。

用法：
  # 列出现有批注（含正文锚点定位）
  python doc_comments.py list <input.docx>
  python doc_comments.py list <input.docx> --no-anchors
  # 追加回复
  python doc_comments.py append-reply <input.docx> --replies replies.json -o out.docx

replies.json 格式：
  {
    "<comment_id>": {
      "reply": "回复正文（支持 **粗体**）",
      "sugg": "建议文本（可选）",
      "concl": "结论（可选）",
      "heading": "自定义标题（可选，默认【统计评估回复 <author>】）"
    }
  }

实现要点：
  - 直接操作 word/comments.xml，在 <w:comment> 末尾追加段落；
  - 保留原批注作者、日期、内容，仅追加回复；
  - 回复结构：【统计评估回复 <author>】+ 回复正文 + 【建议修改】+ 建议 + 【结论】；
  - markdown **粗体** 转 Word <w:b/>；
  - 不修改 document.xml（无需锚点，批注已锚定）。

🔴 §28.12 红线：回复内容由调用方（AI）生成，不得包含未经脱敏的原文片段；
   如需引用原文，须先确认文档已脱敏。
"""

import argparse
import json
import os
import re
import sys
import zipfile

DEFAULT_AUTHOR = "ct-protocol 统计评估"
DEFAULT_INITIALS = "CT"


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def md_runs(line):
    """把一行 markdown 文本转成 w:r 序列（支持 **粗体**）。

    星号约定（v1.4.43）：仅 `**粗体**` 被解析；非粗体段的 `*` **原样保留**
    （Word 里就是普通字符）。旧版无条件 `p.replace("*", "")` 会把 `α*`、`p*`、
    `α^*` 这类记号里的星号吞掉，已废弃。若需字面 `**`，写成 `\\*\\*`。
    """
    parts = re.split(r"(\*\*.+?\*\*)", line)
    runs = []
    for p in parts:
        if not p:
            continue
        if p.startswith("**") and p.endswith("**") and len(p) > 4:
            inner = p[2:-2].replace("\\*", "*")
            runs.append(
                '<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">%s</w:t></w:r>'
                % esc(inner)
            )
        else:
            txt = p.replace("\\*", "*")
            runs.append(
                '<w:r><w:t xml:space="preserve">%s</w:t></w:r>' % esc(txt)
            )
    return "".join(runs) if runs else '<w:r><w:t xml:space="preserve"></w:t></w:r>'


def para(text, bold=False):
    if bold:
        return (
            '<w:p><w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">%s</w:t></w:r></w:p>'
            % esc(text)
        )
    return "<w:p>%s</w:p>" % md_runs(text)


def build_reply_xml(item, author, initials):
    """构建追加到批注末尾的 XML 段落。

    item["heading"] 可覆盖默认标题（如「【评估结论补充 · 同源合并】」），
    用于非「逐条回复评阅意见」性质的追加：ct-protocol U7 去重合并场景会
    把评估定级并入已有批注，此时不应再自称一条新的「统计评估回复」。
    """
    blocks = ["<w:p/>"]  # 空行分隔
    head = item.get("heading") or ("【统计评估回复 %s】" % author)
    blocks.append(para(head, bold=True))
    for ln in (item.get("reply") or "").split("\n"):
        ln = ln.strip()
        if not ln:
            blocks.append("<w:p/>")
        else:
            blocks.append(para(ln))
    if item.get("sugg"):
        blocks.append("<w:p/>")
        blocks.append(para("【建议修改】", bold=True))
        for ln in item["sugg"].split("\n"):
            ln = ln.strip()
            if ln:
                blocks.append(para(ln))
    if item.get("concl"):
        blocks.append("<w:p/>")
        blocks.append(para("【结论】", bold=True))
        blocks.append(para(item["concl"]))
    return "".join(blocks)


def append_replies(docx_path, out_path, replies,
                   author=DEFAULT_AUTHOR, initials=DEFAULT_INITIALS):
    """向已有批注追加回复。

    返回：(成功注入数, 跳过数)
    """
    zin = zipfile.ZipFile(docx_path, "r")
    comments_xml = zin.read("word/comments.xml").decode("utf-8")

    count = 0
    skipped = 0

    def repl(m):
        nonlocal count, skipped
        head, cid, body, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        item = replies.get(cid)
        if not item:
            skipped += 1
            return head + body + tail
        inj = build_reply_xml(item, author, initials)
        count += 1
        return head + body + inj + tail

    pattern = re.compile(
        r'(<w:comment\s[^>]*w:id="(\d+)"[^>]*>)(.*?)(</w:comment>)', re.S
    )
    new_xml = pattern.sub(repl, comments_xml)

    if os.path.exists(out_path):
        try:
            os.remove(out_path)
        except OSError:
            # 目标被占用（如 Word 预览锁定）→ 降级 _v2，不静默覆盖、不静默失败
            base, ext = os.path.splitext(out_path)
            new_path = "%s_v2%s" % (base, ext)
            sys.stderr.write(
                "输出文件被占用，改用：%s\n" % new_path
            )
            out_path = new_path
    zout = zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED)
    for zi in zin.infolist():
        data = zin.read(zi.filename)
        if zi.filename == "word/comments.xml":
            data = new_xml.encode("utf-8")
        zout.writestr(zi, data)
    zout.close()
    zin.close()
    return count, skipped


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def _para_text(p):
    """段落纯文本（含 OMML 的 m:t），用于锚点预览。"""
    return "".join(
        (t.text or "") for t in p.iter()
        if t.tag in ("{%s}t" % W_NS, "{%s}t" % M_NS)
    )


def comment_anchors(docx_path):
    """解析 document.xml，返回 {cid: (start_idx, end_idx, preview)}。

    - 段落下标 = `root.iter(w:p)` 的文档顺序序号（含表格内段落，与正文阅读顺序一致）；
    - start/end 取该批注 `w:commentRangeStart` / `w:commentRangeEnd` 所在段落；
    - preview 取起始段落前 80 字。
    用于回答「批注 id=X 锚定在正文哪一段」。document.xml 缺失或解析失败时返回 {}。
    """
    import xml.etree.ElementTree as ET

    try:
        with zipfile.ZipFile(docx_path, "r") as zin:
            doc_xml = zin.read("word/document.xml")
    except (KeyError, OSError):
        return {}
    try:
        root = ET.fromstring(doc_xml)
    except ET.ParseError:
        return {}

    anchors = {}
    for i, p in enumerate(root.iter("{%s}p" % W_NS)):
        text = _para_text(p)
        for el in p.iter("{%s}commentRangeStart" % W_NS):
            cid = el.get("{%s}id" % W_NS)
            if cid is not None:
                anchors.setdefault(cid, [i, i, text])
        for el in p.iter("{%s}commentRangeEnd" % W_NS):
            cid = el.get("{%s}id" % W_NS)
            if cid is None:
                continue
            if cid in anchors:
                anchors[cid][1] = i
            else:
                anchors[cid] = [i, i, text]
    return {k: (v[0], v[1], v[2]) for k, v in anchors.items()}


def list_comments(docx_path):
    """列出现有批注（id + 作者 + 内容前 80 字）。"""
    zin = zipfile.ZipFile(docx_path, "r")
    comments_xml = zin.read("word/comments.xml").decode("utf-8")
    zin.close()
    pattern = re.compile(
        r'<w:comment\s[^>]*w:id="(\d+)"[^>]*w:author="([^"]*)"[^>]*>(.*?)</w:comment>',
        re.S,
    )
    results = []
    for m in pattern.finditer(comments_xml):
        cid, author, body = m.group(1), m.group(2), m.group(3)
        text = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", body))
        results.append((cid, author, text))
    return results


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser(
        description="ct- Word 批注操作（§29）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    # list
    p_list = sub.add_parser("list", help="列出现有批注")
    p_list.add_argument("input", help="输入 docx")
    p_list.add_argument("--no-anchors", action="store_true",
                        help="不输出正文锚点定位（默认输出）")

    # append-reply
    p_ar = sub.add_parser("append-reply", help="向已有批注追加回复")
    p_ar.add_argument("input", help="输入 docx")
    p_ar.add_argument("--replies", required=True, help="回复 JSON 路径")
    p_ar.add_argument("-o", "--output", help="输出路径（默认 <原名>_含回复.docx）")
    p_ar.add_argument("--author", default=DEFAULT_AUTHOR, help="回复标识署名")
    p_ar.add_argument("--initials", default=DEFAULT_INITIALS, help="署名缩写（预留）")

    args = ap.parse_args(argv)

    if not os.path.isfile(args.input):
        sys.stderr.write("输入文件不存在：%s\n" % args.input)
        return 1

    if args.cmd == "list":
        items = list_comments(args.input)
        if not items:
            print("未发现批注。")
            return 0
        anchors = {} if args.no_anchors else comment_anchors(args.input)
        print("现有批注（共 %d 条）：" % len(items))
        for cid, author, text in items:
            preview = text.replace("\n", " ")[:80]
            print("  [%s] %s: %s" % (cid, author, preview))
            if anchors:
                a = anchors.get(cid)
                if a:
                    s, e, ptext = a
                    loc = ("段#%d" % s) if s == e else ("段#%d–#%d" % (s, e))
                    ptext = ptext.replace("\n", " ")[:80]
                    print("      ↳ 锚点 %s ｜ 正文: %s" % (loc, ptext))
                else:
                    print("      ↳ 锚点: 未在 document.xml 找到 commentRangeStart/End")
        return 0

    if args.cmd == "append-reply":
        replies = json.load(open(args.replies, encoding="utf-8"))
        output = args.output or os.path.join(
            os.path.dirname(os.path.abspath(args.input)) or ".",
            os.path.splitext(os.path.basename(args.input))[0] + "_含回复.docx",
        )
        count, skipped = append_replies(
            args.input, output, replies,
            author=args.author, initials=args.initials)
        print("已追加回复：%d 条（跳过 %d 条）" % (count, skipped))
        print("已生成：%s（%d 字节）" % (output, os.path.getsize(output)))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
