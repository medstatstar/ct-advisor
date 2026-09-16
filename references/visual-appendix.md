# 可视化附录模板（Graphical Appendix）

> **⚠️ 状态：技术储备（2026-09-16 起禁用）。** 本模板原为对解释型/合规性问答、在扣子端返回纯文本时追加独立图示卡片所用。现因本地渲染耗时过长、且"收到结果后再做格式化"实测显著拉长响应（单题测试达 ~6.5 分钟），技能已**一律禁止**收到结果后的任何本地格式化行为，故本附录**不再被触发**——既不自动绘制、也不给文字提示、亦不询问。仅作为可复用 SVG 骨架留存于仓库，供将来需要时参考。
> 历史约束（备查）：① 不改动逐字投递的答案正文；② 图示绝不嵌入正式交付物；③ 浅色主题下每个形状显式填色。

## 触发规则（双重门禁 · 默认不绘制）

> 是否**提示 / 允许**绘制 B 附录须**同时满足**两个条件：① 问题类型为**解释型 / 合规性**（不含方法型、设计型等其他类）；② 扣子端投递的答案仍为**纯文本**（不含 Markdown 对比表 `|---|`，也不含 `> **核心要求：**`/`> **合规红线：**`/`> **说明：**` 这类加粗标签引用块——即 C5 尚未生效）。若云端答案已带 C5 排版，则视为「格式已足够」，**连提示都不给**。两条件满足也**不自动绘制**——仅在输出末尾附一句文字提示（如「如需可视化对照，可回复让我绘制对比矩阵 / 决策流」），实际渲染只在用户明确要求时进行（本地渲染耗时较长）。

| 条件组合 | 是否绘制 / 提示 | 说明 |
|---|---|---|
| 类型=解释型/合规性 **且** 扣子端返回为纯文本 | ⚠️ 仅给一句文字提示，**不自动绘制** | 本地渲染耗时较长，默认不启动；用户明确要求时才调用模板绘制 |
| 类型=解释型/合规性 **但** 扣子端已带信息框/对比表（C5 生效） | ❌ 连提示都不给 | 云端已排版，避免重复、保持单一来源 |
| 正式文档结构（protocol / CSR / review 报告） | ❌ 默认不加 | 如用户要，作独立附录另出，且**不改**正文 |
| 方法型 / 设计型 / 其他非 解释-合规 类 | ❌ 不提示、不绘制 | 不在 B 适用范围 |
| simple 档（≤200 字单段，纯文本） | ⚠️ 可提示但不绘制 | 答案已够短，绘制价值低，等用户要求再画 |

调用方式：`read_me(["diagram"])` → `show_widget(title=..., widget_code=<SVG>, loading_messages=[...])`。

---

## 模板 1 · 对比矩阵（comparison matrix）

适用：两种立场 / 方案 / 做法的对照（如「全额 vs 按比例」「该做 vs 不该做」）。

```svg
<svg viewBox="0 0 680 320" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,Segoe UI,Roboto,sans-serif">
  <!-- 表头 -->
  <rect x="0" y="0" width="150" height="44" fill="#eef2ff"/>
  <rect x="150" y="0" width="265" height="44" fill="#fef2f2"/>
  <rect x="415" y="0" width="265" height="44" fill="#ecfdf5"/>
  <text x="12" y="28" font-size="14" font-weight="700" fill="#1f2937">维度</text>
  <text x="162" y="28" font-size="14" font-weight="700" fill="#b91c1c">方案 A（不推荐）</text>
  <text x="427" y="28" font-size="14" font-weight="700" fill="#047857">方案 B（合规）</text>
  <!-- 数据行：每行 h=55，从 y=44 起 -->
  <!-- 行模板：复制并改 y / 文本 -->
  <rect x="0" y="44" width="150" height="55" fill="#f8fafc" stroke="#cbd5e1"/>
  <rect x="150" y="44" width="265" height="55" fill="#ffffff" stroke="#cbd5e1"/>
  <rect x="415" y="44" width="265" height="55" fill="#ffffff" stroke="#cbd5e1"/>
  <text x="12" y="76" font-size="13" font-weight="700" fill="#1f2937">{{维度}}</text>
  <text x="162" y="76" font-size="13" fill="#374151">{{方案A内容}}</text>
  <text x="427" y="76" font-size="13" fill="#374151">{{方案B内容}}</text>
  <!-- ... 更多行 ... -->
</svg>
```

---

## 模板 2 · 决策流（decision flow）

适用：条件判断型问题（如「是否支付全额 → 是否完成全部访视 → 是否受试者过错 → 结论」）。

```svg
<svg viewBox="0 0 680 300" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,Segoe UI,Roboto,sans-serif">
  <!-- 起点 -->
  <rect x="240" y="10" width="200" height="40" rx="8" fill="#2563eb"/>
  <text x="340" y="35" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">{{问题}}</text>
  <!-- 菱形判断 -->
  <polygon points="340,70 440,110 340,150 240,110" fill="#fef3c7" stroke="#d97706"/>
  <text x="340" y="114" font-size="13" font-weight="700" fill="#92400e" text-anchor="middle">{{判断}}</text>
  <!-- 分支：是 -->
  <line x1="340" y1="150" x2="340" y2="190" stroke="#475569" stroke-width="2"/>
  <rect x="240" y="190" width="200" height="40" rx="8" fill="#ecfdf5" stroke="#047857"/>
  <text x="340" y="215" font-size="13" fill="#065f46" text-anchor="middle">{{是→结论}}</text>
  <!-- 分支：否 -->
  <line x1="240" y1="110" x2="120" y2="110" stroke="#475569" stroke-width="2"/>
  <rect x="20" y="90" width="180" height="40" rx="8" fill="#fef2f2" stroke="#b91c1c"/>
  <text x="110" y="115" font-size="13" fill="#991b1b" text-anchor="middle">{{否→结论}}</text>
  <!-- 依据 -->
  <text x="340" y="265" font-size="12" fill="#6b7280" text-anchor="middle">依据：{{法规/条款}}</text>
</svg>
```

---

## 模板 3 · 要点 / 依据信息框（callout stack）

适用：把答案里的「核心要求 / 合规红线 / 说明」关键框单独渲染成并排卡片，便于一眼抓住结论。

```svg
<svg viewBox="0 0 680 140" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,Segoe UI,Roboto,sans-serif">
  <rect x="10" y="10" width="210" height="120" rx="10" fill="#eff6ff" stroke="#2563eb"/>
  <text x="24" y="34" font-size="13" font-weight="700" fill="#1d4ed8">核心要求</text>
  <text x="24" y="60" font-size="13" fill="#1e3a8a">{{关键结论}}</text>
  <rect x="235" y="10" width="210" height="120" rx="10" fill="#fef2f2" stroke="#dc2626"/>
  <text x="249" y="34" font-size="13" font-weight="700" fill="#b91c1c">合规红线</text>
  <text x="249" y="60" font-size="13" fill="#7f1d1d">{{合规红线}}</text>
  <rect x="460" y="10" width="210" height="120" rx="10" fill="#f0fdf4" stroke="#16a34a"/>
  <text x="474" y="34" font-size="13" font-weight="700" fill="#15803d">说明</text>
  <text x="474" y="60" font-size="13" fill="#14532d">{{口径澄清}}</text>
</svg>
```

---

## 演示（已用于 SAE 交通补贴一题）

见本技能运行时对「方案规定完成全部访视可获 5000 元补贴，受试者因 SAE 提前退出是否应支付全额」生成的对比矩阵附录——左红（不推荐全额派发）/ 右绿（按已完成访视比例折算，GCP 合规）。
