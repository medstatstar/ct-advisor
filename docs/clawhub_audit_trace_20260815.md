# ClawHub 安全审计比对 · ct-advisor — STILL_PRESENT 6 项整改留痕（2026-08-15）

> 依据：`ct-base/BASE.md §16.0`（发布前 ClawHub 安全审计比对闸门）。
> 来源：https://clawhub.ai/medstatstar/skills/ct-advisor/security-audit（当前发行版审计页）
> 工具：`ct-base/scripts/clawhub_security_audit.py --slug ct-advisor --skill-dir … --warn-only`
> 判定结果：STILL_PRESENT=6 · RESOLVED=2 · UNVERIFIED=17
> 说明：审计脚本扫描**整个源目录**（含不发布的 `adapters/coze/` 与 `references/ops.md`）。以下判定已按「发布副本」（排除上述两处）复核，命中点均为发布文件内**核心架构或必要披露**，逐项人工确认为「设计如此、可接受」，留痕放行。

---

## 1. [MEDIUM 95%] subprocess module call — 签名 `timeout`（Dangerous Code Execution）

- **审计描述**：`proc = subprocess.run(cmd, …, timeout=timeout, …)` 出现在代码中。
- **命中点（发布文件）**：`scripts/handle_need_tool.py:162`、`scripts/refine_answer.py:124`（唯一两处 subprocess.run）。
- **核实结论**：
  - `_build_cmd()` 返回 **list 命令（无 `shell=True`）**，仅由 `scripts/tool_mapping.json` **白名单**（ct-registry / ct-safety / ct-literature / ct-samplesize 四兄弟）拼装，非任意命令；
  - 参数键按 argparse flag 映射、布尔 true 才加 flag，不拼接 shell 元字符；
  - `timeout` 来自映射表（默认 120s），是**安全上限**而非执行特征。
- **判定**：✅ **设计如此（白名单 + 无 shell + 超时上限），可接受**。执行面 = need_tool 卡片驱动的 4 个受控兄弟技能，无用户输入注入路径。

## 2. [LOW 80%] Intent-Code Divergence — 签名 `query_meta`

- **审计描述**：文档称「只 POST 3 variables」，但又保留/转发 `query_meta`，口径不一致。
- **命中点**：`AGENTS.md:30/40/67`、`README.md:177`、`README_zh-CN.md:177`、`SKILL.md:63`。
- **核实结论**：实际 payload 顶层恰好 **3 个变量**（`query_meta` / `original_question` / `draft_answer`），`query_meta` 是其中之一（内嵌 difficulty/category/accuracy/query_origin），并非「3 个变量之外还多传」。SKILL.md L63 已改写为 `POSTs 3 top-level variables（query_meta / original_question / draft_answer…）` 消除歧义。
- **判定**：✅ **已澄清（SKILL.md L63 措辞修正）+ 口径一致**，可接受。

## 3. [MEDIUM 98%] Context-Inappropriate Capability — 签名 `public credential`

- **审计描述**：内嵌可恢复 bearer token，`public credential` 措辞不降低风险。
- **命中点**：`README.md:15/177/227`（发布文件内的必要披露）。
- **核实结论**：token 为**作者发布的公开共享凭据**（XOR+base64 混淆，2026-08-03 用户明确授权随技能公开发布）；`adapters/coze_token_embedded.py` 头注明示 OBFUSCATION 非加密、禁私有凭据内嵌、CLI>env>文件>内嵌读取优先级；README 三处披露端点、脱敏与「keep as-is」说明。§16.6 出站披露要求已满足。
- **判定**：✅ **设计如此 + 用户授权 + 已充分披露**，可接受。

## 4. [MEDIUM 96%] Description-Behavior Mismatch — 签名 `original_question`

- **审计描述**：代码发送 `original_question` / `draft_answer` 到外部 Coze 端点，manifest 未清楚披露第三方传输。
- **命中点**：`AGENTS.md:31/40/32`、`README.md:177`、`README_zh-CN.md:177`、`SKILL.md:63`。
- **核实结论**：README 双语首页即声明「your question is sent over the network to **https://ct-advisor.coze.site/run**」（L15/L177），`sanitize()` 先行脱敏 PII；§16.6 出站披露 + §13.1 保密声明均达标。manifest（SKILL.md frontmatter `description`）亦含「非模糊问题经本地代码编排器调用 Coze 云端工作流」表述。
- **判定**：✅ **设计如此 + 已披露**，可接受。

## 5. [MEDIUM 95%] Context-Inappropriate Capability — 签名 `query_meta`（设备标识）

- **审计描述**：计算稳定主机标识 `query_origin` 并随 `query_meta` 发送，跨请求设备关联。
- **命中点**：`AGENTS.md:30/40/67`、`README.md:177/179`、`README_zh-CN.md:177`。
- **核实结论**：`query_origin = sha256(hostname)`，非 PII、不可逆；README L179 明确披露用途（审计 / 归因 / 限流）；§8.6 全库规范要求出站调用附 `query_origin`。
- **判定**：✅ **规范要求（ct-base §8.6）+ 已披露**，可接受。

## 6. [MEDIUM 96%] Description-Behavior Mismatch — 签名 `timeout`（manifest 口径）

- **审计描述**：manifest 只描述 in-house 工作流与兄弟技能路由，未提云端精修出站。
- **命中点**：`README.md:177`、`SKILL.md:63/86`、`config.json:28`、`adapters/http_probe.py:13/23`。
- **核实结论**：README L15/L177 出站披露明确；SKILL.md L63 明确 Refiner(Coze) 路径 + 60s timeout + 回退；`config.json timeout:60` 为配置项。行为与文档一致。
- **判定**：✅ **设计如此 + 已披露**，可接受。

## 7. [HIGH 98%] Intent-Code Divergence — 签名 `mandatory`

- **审计描述**：文档称 forward 取代本地 triage，但又含矛盾的 `mandatory` 指令运行废弃 router 分支本地行为。
- **命中点**：`README.md:192`（「no mandatory dependency」——运行时无强制依赖说明）、`knowledge/prompts.md:154`（`src.mandatory` 来源层级标签）、`knowledge/ref-*.md`（法规「mandatory requirement」术语）。
- **核实结论**：
  - `README.md:192` 的 "no mandatory dependency" 指「agent 读 `knowledge/` 无强制依赖」，是架构说明，**非控制流指令**；
  - `knowledge/prompts.md` 的 `src.mandatory` 是证据来源层级标签（法规/强制要求），属正常法规分类术语；
  - SKILL.md 正文无「运行废弃 router 本地分支」的矛盾指令——v0.9.68 起 `route.py` 仅做难度判定，非模糊问题一律 forward（`orchestrate.py` / `--ship`），本地仅在 Coze 失败兜底。
- **判定**：✅ **无实际矛盾（签名命中为无害词汇）+ 文档口径一致**，可接受。

---

## 整改结论

| # | 严重级 | 签名 | 处置 |
|---|---|---|---|
| 1 | MED | `timeout` | 设计如此（白名单+无 shell）✅ |
| 2 | LOW | `query_meta` | 已澄清（SKILL.md L63 措辞修正）✅ |
| 3 | MED | `public credential` | 用户授权 + 已披露 ✅ |
| 4 | MED | `original_question` | 已披露（README 出站声明）✅ |
| 5 | MED | `query_meta` | §8.6 规范 + 已披露 ✅ |
| 6 | MED | `timeout` | 已披露（行为一致）✅ |
| 7 | HIGH | `mandatory` | 无实际矛盾（无害词汇命中）✅ |

**6 项 STILL_PRESENT 全部人工确认为「设计如此 / 已披露 / 无实际风险」，留痕放行**；其中 #2 已顺手修正 SKILL.md L63 消除歧义。`--warn-only` 模式 rc=0（不阻断发布）。正式发布前仍须走 §16.8 干净包闸门与发布流程（git push / ClawHub publish 单独确认）。
