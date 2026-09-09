# ct-advisor Coze 缓存与响应信封策略 / Cache & Response-envelope Policy

> **范围**：ct-advisor 的 Coze 端（`adapters/coze/` 镜像）与本地渲染层在 **2026-09-09** 定稿的缓存治理、信封字段与飞书表写入约定。改任何一处前先读本文档；实现文件与部署动作见文末清单。
> **作者/日期**：彤（张温通）拍板，2026-09-09。**部署状态（2026-09-09 同步 v2 实测更新）**：缓存四闸/TTL/信封契约已上线 Coze 并经验证——本地镜像已同步为 Coze 端最新 v2 代码包（`ct-advisor_coze_project_latest_v2.tar_ea00666b.gz`）。模型配置现状：`config/` 下 **4 个** `*_cfg.json`（full_analysis / generate_organized_problems / judge_difficulty / review），模型名均为 `doubao-seed-*-260215`（线上实测可跑、非下线）；**`cache_check` 节点已无独立 cfg**（v2 移除了 `cache_check_cfg.json`）。缓存目录改走可写 `/tmp`（跨请求命中已验证，3 连发同题 第2/3 发亚秒级命中）；`message` 字段已声明但当前无节点赋值 → 出参不含该键（属正常，见 §7）。

---

## 1. 缓存生命周期总览（写 → 存 → 读，四道闸 + 有效期）

```
生成答案 ──①写闸──> SQLite(answer_cache) ──②命中读取──> 交付用户
   │       (accuracy=good 才入库)              │
   │                                          ├─ ③内容闸（敷衍非答案→视为 miss）
   │                                          ├─ ④质疑闸（用户质疑→强制 miss）
   │                                          └─ ⑤TTL（>6 个月→删条 + miss）
   └── miss / 过期 / 质疑 ──────────────────> 走正常重生成（review/full_analysis → tool_router）
```

实现文件：`adapters/coze/src/graphs/nodes/{cache_manager,cache_check_node,full_analysis_node,review_node}.py`。

## 2. 写路径质量闸：仅 `accuracy=good` 入库

- `cache_manager.py::set_cache_answer(question, answer, history_fp="", accuracy="normal")`：
  **`accuracy != "good"` 一律不写缓存，直接返回 False**（normal/poor/未标注都拒）。
- 两个写点必须显式传 accuracy：
  - `full_analysis_node.py` → 传 LLM 自评 accuracy（答案尾行 `accuracy: good|normal|poor` 提取）；
  - `review_node.py` → 传 `query_meta.accuracy`（默认 normal → 默认不入缓存）。
- 单一强制点在 `set_cache_answer` 内部——未来新增写点自动继承，不存在"忘加闸"旁路。
- 目的：从源头杜绝低质/敷衍答案（如"未收录，请去官网自行检索"类 punt）污染缓存。

## 3. 缓存有效期：TTL = 6 个月（命中即查，过期强制重生成）

- 常量 `CACHE_TTL_SECONDS = 6 * 30 * 24 * 3600`（≈180 天；置 0 = 关闭过期）。
- schema 增列 `created_at REAL`；存量库启动时**在线 `ALTER TABLE ADD COLUMN`** 补列（与 `history_fp` 同款，忽略"列已存在"）。
- `created_at` = **首次生成时间**；`INSERT ... ON CONFLICT DO UPDATE` **不更新 created_at** → 命中刷新不续期，到期必然失效。
- **每次命中都检查有效期**（读路径全覆盖）：
  - `get_cached_answer()`（Tier1 精确）；
  - `find_cache_match()` Tier1 精确命中 + Tier2 n-gram 相似候选（扫描时跳过并顺手删除过期候选）。
- 过期处理：删除该条 + 返回未命中 → **强制重新生成**（自愈，不留死条目）。
- **存量无 `created_at`（NULL）的条目视同过期**：无法证明新鲜，首次命中即失效重生成一次。

## 4. 读路径内容闸：敷衍非答案 → 视为 miss（自愈）

`cache_check_node.py::_looks_like_punt_answer` 命中缓存文本后，若含下列**极窄拒绝式措辞**之一 → 返回 cache_hit=False，走正常重生成（触发 tool_router）：

- 中文：`未收录` / `知识库未收录` / `暂未收录` / `建议通过以下官方路径` / `请自行检索` / `请自行查询` / `建议您自行` / `我建议您自行` / `我建议你自行` / `这个我也不知道`
- 英文：`not in the knowledge base` / `not currently in the knowledge base` / `please search` / `please check the official` / `search it yourself`

> 只拦截"让用户自己去查"的敷衍形态；正常正文即使含"建议"等词也不误伤。特征词修改只改这一处清单。

## 5. 质疑强制重生成：缓存不服务质疑轮

`cache_check_node.py::_looks_like_challenge` 检测 `original_question` + **最近 3 条对话历史**（质疑通常针对上一轮答案），命中即 cache_hit=False 强制重生成。词表：

- 中文：`对吗` `正确吗` `对不对` `准确吗` `确定吗` `真的吗` `可靠吗` `是不是错了` `有误` `错了吧` `不对吧` `质疑` `请复核` `再核对` `核对一下` `重新生成` `重新算` `重算` `再查一遍` `重新检索` `重新核查`
- 英文：`are you sure` / `is this correct` / `is it correct` / `is that correct` / `verify` / `double-check` / `re-check` / `recheck` / `recalculate` / `wrong` / `incorrect` / `not right`

> 宁可多算一次，也不把可疑旧答案再递给质疑用户。普通问题误中至多多一次生成，无正确性损害。

## 6. 缓存命中来源声明（本地渲染层，不污染缓存文本）

命中缓存交付时，答案最前必须明示**"来自云计算缓存、非本次实时计算"**：

- `scripts/refine_answer.py` 主链路：`result.cache_hit=True` → Prepend `> 📦 本答案来自云计算缓存（历史运行结果，非本次实时计算）。如需最新结果，请追问要求重新生成。`（英文随提问语言切换）；
- `workbench/index.html` `bubble()`：`meta.cached` → 答案上方金色声明条；
- `--forward` JSON 本就带 `cache_hit` 机器字段，供消费端自渲染。

> 声明只发生在视图层，缓存/飞书存储文本不变。

## 7. 响应信封兼容约定（本地解析顺序）

- 主答案字段：**`final_answer` = 正式（新版/当前镜像 `GraphOutput`）；`answer` = 备用（老版信封）**。本地一律 `data.get("final_answer") or data.get("answer") or draft`（`adapters/refiner.py`）。
- `message`（§20.15 表面提示）：响应信封**顶层可选 / 尽力而为**字段。
  - 契约：结构 `{level, text, dismissible}`；Coze 给裸字符串时本地按 `{level:"notice", text, dismissible:True}` 归一化；多条合并为一段。
  - **当前状态（2026-09-09 实测 + 用户确认）**：`GraphOutput`/`GlobalState` 已声明 `message: Optional[Any]=None` 作为**保留字段**，但**全图没有任何节点对其赋值** → LangGraph 将该未赋值通道从最终 JSON 出参中丢弃，**实际响应里不含 `message` 键**。这是**预期且正常**的（用户明确：未赋值即不应出参），并非 bug，无需强制让它出现。
  - **兼容性保证（本地已就位，无需改动）**：
    1. `adapters/refiner.py` 用 `data.get("message")` 取字段 → 缺失即 `None`；`_normalize_coze_message` 对 `None/str/list/dict/数字/布尔` 全部安全降级（无效值→`None`），**绝不抛错**；
    2. `scripts/refine_answer.py` 渲染前用 `getattr(result, "message", None)` + 真值判断守卫，**`None`/空 → 跳过 banner、不中断主流程**；
    3. 未来任一节点开始赋值 `message`，将自动经出参透传并被本地归一化渲染，**前后向兼容、零改动**。
  - 用户可用提示词"关闭提示/隐藏提示/no notice…"关闭已出现的 banner；当前无 banner 即视为"无表面提示"。
- 详见 `references` 的 ct-base `coze_io_contract.md §5/§5.4` 与 ct-base §20.15。

## 8. advisorlog 表：固定字段写入（不再动态查表架构）

- 飞书表 schema 已移除 `draft_answer` 列（2026-09-09）。
- `async_feishu_writer.py` **删除 `_get_table_fields()`**（原每次写前查一次表字段），改按固定清单常量 `ADVISORLOG_FIELDS` 构造记录：
  `difficulty / category / original_question / organized_problems / accuracy / final_answer / query_origin / inittime`（8 列，**无 draft_answer**）。
- `draft_answer` 函数参数保留（`full_analysis / review / cache_check` 三个调用点兼容），但**不再写入记录**。
- **表 schema 再变更 → 只改 `ADVISORLOG_FIELDS` 常量一处**。

## 9. 配置/维护速查

| 项 | 位置 | 说明 |
|---|---|---|
| TTL | `cache_manager.py::CACHE_TTL_SECONDS` | 0=关闭；改后重启生效 |
| 写闸阈值 | `set_cache_answer` accuracy 参数 | 仅 `good` 放行 |
| punt 特征词 | `cache_check_node.py::_PUNT_HINTS` | 只加"让用户自查"类措辞 |
| 质疑词表 | `cache_check_node.py::_CHALLENGE_HINTS` | 质疑/复核/重算意图 |
| 表字段清单 | `async_feishu_writer.py::ADVISORLOG_FIELDS` | 对齐飞书 advisorlog schema |
| 模型配置（v2） | `adapters/coze/config/*.json`：**4 个** `full_analysis_cfg` / `generate_organized_problems_cfg` / `judge_difficulty_cfg` / `review_cfg` | 模型名均为 `doubao-seed-*-260215`（线上实测可跑）；**`cache_check` 节点无独立 cfg**（v2 已移除 `cache_check_cfg.json`）——改模型只动这 4 个文件 |
| 部署包 | `adapters/coze/` 镜像（已同步 v2）｜历史打包见仓库 CHANGELOG | 上传后**必须重启/重建镜像**才生效（ct-base §20.2.6） |

## 10. 双向兼容（新/老终端）

- **新本地 + 老 Coze**（老信封 `answer`、无 message、无 TTL）：`answer` 兜底 ✓；无 message 不渲染 ✓；老缓存无 `created_at` 视同过期、命中重生成一次 ✓。
- **老本地 + 新 Coze**：仍回 `final_answer`/`cache_hit`，老本地解析不变；message 键老本地忽略。
- 全部新增字段带缺省值、旧入参不受影响（pydantic `extra='ignore'`）。
