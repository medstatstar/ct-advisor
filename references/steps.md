---
file: steps.md
version: 2026-08-12
purpose: ct-advisor Answer Workflow step definitions — the SKILL.md step summary maps to this file's full flow, boundary conditions, and exception handling
---

# Answer Workflow — Steps 0-6 (Detailed)

> **🔴 2026-08-14 mode change — FORWARD REPLACES RACE/SERIAL**: the local skill no longer answers locally — **every** non-vague question is forwarded to Coze once (`refine_answer.py --ship`, or `orchestrate.py` for data-intel); local `knowledge/` answers only as the Coze-failure fallback; sibling skills run **only** on the Coze-issued `need_tool` card (execute `scripts/handle_need_tool.py` + stitch locally, never re-send). **Entry difficulty gate**: `scripts/route.py` (deterministic, LLM-free) runs **once** at question entry to label difficulty; `vague` → Local Clarify Loop (`clarify_loop.py`) then Coze (never forwarded as `vague`); **others → verbatim forward with `query_meta.difficulty` as a *hint* — Coze always re-estimates it via LLM into `simple`/`middle`/`complex`**. Steps 1–5 below are **legacy race/serial detail kept for back-compat reference only** — do NOT run `--fire-only` or `--collect` in forward mode (the `route.py` gate IS the current entry step). The authoritative current flow is the SKILL.md Answer Workflow table + `ops.md` §step-7-cookbook.

> **🔴 2026-08-15 v0.9.68 update**: for data-intel questions (sample-size / registry / safety / literature) the preferred entry is now `scripts/orchestrate.py` (code-only orchestrator: prefetch + parallel Coze/skill + decide, emits wrapped answer or `<<<CT_TOOL_DELEGATE>>>`); `--ship` is the non-orchestrate fallback answer path. `--forward` is debug-only. The LLM is never the orchestrator — it only delegates ct-skill calls and handles need_params + Coze-failure fallback.

> **Core principle**: payload always travels through the in-memory pipeline (`--payload-inline` or stdin), **never** Write/Bash temp JSON files.

---

## Step 0 — Code-based difficulty gate (2026-08-14 晚)

**Goal**: run `scripts/route.py` **once** at question entry. Its **primary job is to split out `vague`** (→ Local Clarify Loop, which never forwards `vague` to Coze). For non-vague questions it also emits a `simple` / `middle` / `complex` label — but **this label is only a *hint***: Coze **always re-estimates difficulty via LLM** into `simple` / `middle` / `complex` (vague is impossible server-side) and uses that re-estimated value to set answer depth. Deterministic, LLM-free, stdlib-only — the **only** local work permitted before Coze (no `knowledge/` read, no `search_refs.py`, no multi-round local retrieval). `route.py` only labels; it does **not** decide local-vs-remote.

**Branch after the gate**:

| label | action |
|---|---|
| `vague` | enter the **Local Clarify Loop** (`scripts/clarify_loop.py`, the heuristic menu) to clarify requirements (1–3 high-value questions/round, hard cap 3 rounds); on status `decidable`/`forced_decide` re-gate on the enriched question and route per the table (data-intel → `orchestrate.py` preferred, else `--ship`) with the **re-gate label** (`simple`/`middle`/`complex`) — **never** as `vague` (Coze no longer accepts vague; it would be forced to `complex`). |
| `simple` | forward via `scripts/orchestrate.py` (data-intel preferred) or `refine_answer.py --ship` (fallback) with `query_meta.difficulty="simple"` **(hint — Coze re-estimates)**. |
| `middle` | forward verbatim to Coze with `query_meta.difficulty="middle"` **(hint — Coze re-estimates)**. |
| `complex` | forward verbatim to Coze with `query_meta.difficulty="complex"` **(hint — Coze re-estimates)**. |

All non-`vague` questions go to Coze **verbatim** (forward-only). The forwarded `difficulty` is a **hint only** — Coze's `generate_organized_problems_node` **ignores it and re-estimates via LLM** (simple/middle/complex), then feeds that value into `full_analysis` as the answer-depth knob.

**🔴 Run the router (mandatory, code-only)**:

```bash
# 主 Agent 第一步必须运行（不要自己理解问题判断难度）：
python scripts/route.py "用户问题原文"
#   → 打印一个标签：simple | vague | middle | complex
# 调试：python scripts/route.py --json "…"   /   回归：python scripts/route.py --self-test

# 分流结果见上方 Branch 表：vague → 本地澄清菜单，其余级别 verbatim 转发 Coze（forward-only）。
```

**📖 `simple` whitelist (SIMPLE_TOPICS)**: `route.py` ships a built-in `SIMPLE_TOPICS` whitelist — standard-operation / definition phrases taken from `knowledge/reference-index.md` coverage topics (e.g. ALCOA, SAE reporting timeline, drug accountability, emergency unblinding, screening log, DB lock, informed-consent withdrawal). A whitelist hit with no complex / exclude signal → `simple`; it is a **deterministic lookup table** (immune to phrasing drift). **Maintenance rule**: any new entry MUST pass `python scripts/route.py --self-test` + bank eval confirming zero leak-to-simple (a non-simple question pulled into `simple` = missing the Coze fire/collection — red line).

**⚠️ Pre-routing interception (mandatory)**: when classifying difficulty, analyze the intent of `original_question` — if it requires calling an external skill for data (ct-registry / ct-safety / ct-literature) or computing sample size / power (ct-samplesize), **difficulty MUST NOT be simple/middle; only complex is allowed** (vague never reaches this gate). Reason: data pull / n computation depends on real external output that Coze integrates via its `need_tool` handoff; labelling it simple/middle would under-signal Coze and lose that grounding.

**🔴 Difficulty bias rule (guardrail against misjudging as complex)**:

When the question **does not involve external data pull / sample size computation**, prefer `simple` or `middle` (over `complex`) unless at least one of the following holds:
- requires pulling data from ≥1 sibling skill simultaneously (data grounding ≥1 route)
- requires ct-samplesize to compute n / power
- question explicitly asks for multi-option comparison + recommendation ("which one / best approach")
- composite judgment spanning ≥2 workflows

**Pure methodology questions (e.g., "how to do X", "what to watch for in X", "difference between X and Y") are always `simple` or `middle` (never `complex`)** — the label only sets `query_meta.difficulty` for Coze's refinement depth; the question is still forwarded verbatim to Coze (forward-only, no local answer). Among them: **single fact / definition / standard operation → `simple`**; explanation / comparison / multi-step reasoning → `middle`.
**Typical misjudgment example**: "How to ensure data integrity when migrating from paper CRF to EDC?" → although multi-step, no external data is needed and no n computation is involved → should be judged `middle`, not `complex`.

**🚫 Anti-shortcut warning (HARD GATE)**: for `simple` / `middle` / `complex`, the **only** allowed action is verbatim forward to Coze (`scripts/orchestrate.py` for data-intel, or `refine_answer.py --ship`) with `query_meta.difficulty` set — there is **no local-answer path**. Do NOT use any of the following "invisible pre-judgments" to skip forwarding (this applies to all three non-vague labels; `simple` is a difficulty label for `query_meta`, **not** a license to answer locally):
- ❌ "the knowledge base already has a clear answer, just retrieve and output it"
- ❌ "search_refs.py found it, no need to forward"
- ❌ "the question is too simple, Coze would just repeat"
- ❌ "the local answer is good enough, no need to forward"

**Coze is the sole answer path, not a backup**: under forward-only the question always goes to Coze; the local knowledge pack is only a fallback when Coze fails (see `ops.md`) — **never** let the agent pre-judge "Coze is useless" and answer locally.

---

## 延迟护栏单测式检查表（F · 可观测化，2026-08-23）

> **防回归硬清单**：每次改动路由 / Step 0–2 逻辑后，逐条断言；任一条不成立即视为护栏破坏。
> 配套度量：`refine_answer.py --latency-report --round-id <qid>` 统计每轮工具往返数，
> 超过阈值（默认 10）即 stderr 输出 `[WARN]`，提示 pre-fire 延迟复发（详见脚本内 `_record_latency`）。
> 重置某轮计数：`refine_answer.py --latency-reset --round-id <qid>`。

| # | 不变量（invariant） | 违规即失败（break = red line） |
|---|---|---|
| L1 | `middle` 必须走 Step 1 **fire-only**（后台 `--fire-only`），**禁止**在 fire 之前读 `knowledge/` / `search_refs.py` / `workflows.json` | 任何 Step 1 前的本地读取 = 护栏破坏 |
| L2 | `simple` 必须**跳过 Coze**（Step 2 local-only：零 outbound、零 `--collect`） | `simple` 出现 `--fire-only` / `--collect` 调用 = 护栏破坏 |
| L3 | `middle` 的 fire-only 必须在 Step 0 路由判定后**立即**发起，不得等 Route / 本地检索完成 | fire 晚于本地读取 = #1 延迟失效模式复发 |
| L4 | `complex` 走 Step 5 串行精校：本地初步 ≤200 字、单次生成、不回看 | 本地进入"检索→整合→再检索"多轮循环 = 3–5min 循环复发 |
| L5 | 任何 non-vague 标签都不得本地作答（forward-only）；Coze 是唯一答案路径 | "本地答案够好不转发" = 短路红线 |
| L6 | `vague` 永不 forward 为 `vague`（本地澄清后必以 `simple`/`middle`/`complex` 重门控） | 把 `vague` 直发 Coze = 服务端强制 `complex`、丢失澄清价值 |

**Interaction strategy** (legacy reference — see Step 0 Branch table above for the current gate):
- `simple` / `middle` / `complex` → verbatim forward to Coze (forward-only); no local answer, no menu
- `vague` → run the **Local Clarify Loop** (`scripts/clarify_loop.py`, the heuristic menu) — bounded 1–3 questions/round, hard cap 3 rounds (replaces the old free-form grill-me probing from the pre-forward-era design)
- when unsure between simple/middle/complex → still forward verbatim; do not answer locally

---

## Step 1 — Fire Gate

**Goal**: 🔴 for `middle`, fire the Coze refinement request in the background **IMMEDIATELY after Step 0 Triage — BEFORE Step 2 local retrieval**. This is the single most important latency gate: Coze (≈20s) must start racing the local loop from T+0, not after Route / pre-reading. `simple` never enters this step (local-only — see Step 2 Local-only mode).

| difficulty | behavior |
|---|---|
| `simple` | **skipped (local-only)** — never fire Coze; go straight to Step 2 local answer. No outbound call, no authorization gate. |
| `middle` | 🔴 **HARD GATE**: **immediately** fire `refine_answer.py --fire-only` via background (`run_in_background`, stdin pipe), passing `original_question` + `query_meta.difficulty` (the Triage-judged `middle`); leave `category`/`accuracy`/`draft_answer` empty. **No temp files**; **do not skip this step and write the local answer directly**. |

```bash
# fire-only 示例（race，只发 original_question + difficulty；category/accuracy/draft_answer 留空）：
echo '{"query_meta":"{\"difficulty\":\"middle\",\"category\":\"\",\"accuracy\":\"\"}","original_question":"…","draft_answer":""}' | python scripts/refine_answer.py --fire-only
```
| `complex` | do not fire; await the serial call in step 5. |

> 🔴 **Key**: this step is the start of race mode (`middle`) and MUST execute right after Triage for `middle`. `simple` is exempt (local-only, never fires); `complex` awaits Step 5. For `middle`, firing here (before any local retrieval) means Coze is already computing while the agent does local work; by Step 2 `--collect` it is very likely already back (cache hit → verbatim ship). Firing late (after Route / pre-reading knowledge) is the #1 measured latency failure mode.

> 🔴 **Outbound Authorization Gate (auto-executed)**: the script checks authorization automatically before the `--fire-only` outbound call:
> - endpoint is in `config.json` `auto_approve_endpoints` allowlist → allow directly
> - already authorized this session → allow directly (script in-memory memory)
> - not authorized → script returns empty string (local wins); agent should prompt the user to confirm and then add the endpoint to the allowlist

---

## Step 2 — Collect + Route + Local Answer

**Goal**: For `middle` (race) this is the single most important race step — **Begin by calling `--collect --wait=race_window` (the main blocking point)**; do lightweight local work (Route match + prepare fallback) *within* the collect wait window. Coze hit → verbatim ship; timeout → use local fallback. For `simple` (local-only) this step *is* the local answer itself (no collect, no Coze). For `complex` (serial) this step writes the local answer that feeds Step 5.

### Local-only mode (simple)

- `simple` never fires Coze and never calls `--collect`. After Step 0 Triage, do **ONE** local retrieval (Knowledge Map rule 3 — single search only, no chaining) from `knowledge/` or `search_refs.py`, then write the complete local answer (conclusion-first + regulatory citations) → step 6.
- No outbound call, no authorization gate, zero network.
- Local retrieval is capped at ONE per turn (Knowledge Map rules 3 / 7 / 8); do NOT chain multi-step reads or route to sibling skills — simple must never become a complex chain.

### Race mode (middle)

```
step 1 fired fire-only → Coze running in background
step 2 begins → main agent FIRST calls --collect --wait=race_window (main blocking point)
               ├─ Coze returns within window → **adopt Coze VERBATIM** → step 6
               └─ window exhausts, Coze not back → agent writes local answer
                     (Route match A–J from scripts/workflows.json + conclusion-first regulatory citations) → step 6
```

- 🔴 **HARD GATE (post-collect zero-processing)**: the instant `--collect` returns a cache hit, output the Coze stdout **as-is** — no re-write, no re-order, no injecting `knowledge/` citations the Coze output lacked, no re-formatting, no appended "local summary". Re-synthesis after Coze returns is the #2 measured latency failure mode. Ship Coze, full stop.
- 🔴 **Route is a window-internal side task, NEVER a blocker**: `fire-only` needs only `original_question`; the Route result is irrelevant to Coze. Do NOT read `workflows.json` / `knowledge/` *before* firing (Step 1) — and do NOT let Route retrieval delay the collect call. If local retrieval would take long, it only matters as fallback; Coze (≈20s) almost always wins, so the user never waits for the full local retrieval.
- Coze HTTP timeout = full 60s (`refiner.timeout`); **complex / 模板类问题放宽到 300s**（`refiner.long_timeout`=300s）——由 `CozeRefiner._resolve_timeout()` 按 `difficulty==complex` 或 `category` 命中模板类标记自动判定
- race_window = 30s (config.json `refiner.race_window`; caller can override with `--wait N`)
- **⚠️ --collect MUST pass complete payload**: the cache path is derived from the hash of original_question + query_meta; without the payload the cache cannot be located. When the agent calls --collect in step 2, it MUST pass the same payload from step 1 (or at least the minimal payload containing original_question), otherwise the script fails JSON parsing → local win (but wastes one tool call)

### Route matching (local, window-internal)

- methodology / design / GCP / compliance / QC / statistics → local `knowledge/` workflow
- registered-trial landscape / safety signals / literature → mark step 3 data-trigger
- sample size / power → mark step 4 handoff trigger

### Serial mode (complex)

- Route match (workflow A–J) + write the complete local answer (conclusion first + regulatory citations); do NOT call `--collect` (serial awaits Coze in step 5).
- the answer becomes the input to step 5 serial refinement

### query_meta self-assessment

`accuracy` = `good` (precise regulatory citations) or `normal` (generic answer).

---

## Step 3 — External Data 1 (Data Grounding, on demand)

**Goal**: pull real data from external skills to support the answer.

**Trigger**: only when step 2 marked a data route (ct-registry / ct-safety / ct-literature).

**Action**:
1. read sibling-skill output (configured in `workflows.json` as `integration.data_grounding`)
2. label "Data source: ct-xxx on <date>"
3. pure-methodology questions may skip (label "no data grounding performed")

**Note**: keep it light; Coze handles expansion and integration.

**🔀 Sibling-skill call protocol (MUST, before ANY sibling invocation — ct-registry / ct-safety / ct-literature / ct-samplesize)**:
1. **Disclose in chat (5 elements)**: ① skill + one-line role ② why (what local `knowledge/` & Coze can't answer) ③ actions + external sources (read-only public APIs, zero confidential outbound) ④ expected duration (mirror the sibling's printed time estimate; >2 min → run in background and say so up front) ⑤ how results return. Example:
   > 🔀 正在调用 ct-literature（临床试验文献检索专家）
   >    原因：本地知识包无实时文献；大模型直接回答具体引文会幻觉
   >    动作：检索 OpenAlex + Europe PMC 公开文献库（外部只读，零保密外发）
   >    耗时：约 1–4 分钟（含逐篇引文验证）
   >    回灌：产出可引用证据摘要 → 汇入本流程继续
2. **Show the execution plan + one confirmation**: topic / params / sources — ask **"确认执行？"**. One confirmation, NOT per-param. **Quick Mode exception**: skip the ask only when the user's request already states the key params (e.g. "近 5 年 PD-1 肺炎安全文献") — still show the plan once before running.
3. **Return-to-advisor (MUST after the sibling returns)**: bring its structured output (JSON / report) back into THIS workflow — never end the thread at the sibling:
   - **narrow ask** → surface as the answer body, labeled `Data source: ct-xxx on <date>` + provenance (evidence log / verification status);
   - **broad ask** → stitch in-house (trio once each → strategic brief);
   - **chained need** → decide the next sibling and disclose the chain (e.g. literature safety signal → `ct-safety` FAERS quantitative cross-check);
   - **follow-ups** on the same topic stay in this workflow — no re-invocation, no re-route.

---

## Step 4 — External data 2 / sample-size handoff (Handoff, on demand)

**Goal**: hand a complete parameter framework to `ct-samplesize`; this skill does NOT compute n.

**Trigger**: step 2 marked workflow C parameters ready.

**Payload**: design type, comparator, test (α/power), effect size, dropout rate.

---

## Step 5 — Send to Coze for refinement (Serial Refine)

**Goal**: send the local answer to Coze to produce the final answer.

**Trigger**: `complex` difficulty.

**Input**: local answer + external data results 1 and 2.

> 🔴 **Local preliminary lock (complex only — anti-loop, with reference docs attached)**:
> The complex path **keeps reference docs / `knowledge/` / `search_refs.py`** (the local draft must stay precise), but the preliminary must be locked to a **single-pass generation**:
> - Reference docs may be attached / searched, but the preliminary is produced **exactly once** — never enter a "retrieve → integrate → re-retrieve" multi-round loop;
> - Preliminary output hard-capped at **≤200-character key points**; **no "wait for Coze to return, then polish / re-integrate" look-back action**;
> - The preliminary serves only as the `draft_answer` **input** to Coze serial refinement; the final presented answer is **always Coze's output** — the local preliminary is never shown to the user directly.
> The 3–5 min loop was caused by "local + Coze dual reasoning streams interfering + agent self-deciding whether to fire"; this lock + code-forced firing + Coze as final source together eliminate it.

**Output**: await Coze's refined result; on timeout return local answer + external data results 1 and 2.

> 🔴 **Coze failure diagnosis (2026-08-13, user-friendly)**: when fallback triggers (stderr shows `FALLBACK` / `ProxyError` / `Timeout`, or stdout carries the friendly ask "是否允许我自动进行问题诊断排查？"), **first ask the user** whether they allow an automatic diagnostic check; if allowed, run `python scripts/check_coze.py` once to locate the root cause (stale system proxy / offline / token), fix it, and retry; if declined, deliver the local answer **with a prominent warning**: 「无法连接 Coze 服务，答案未经过精校，请谨慎使用」. **v0.9.60+ auto-retries by bypassing the system proxy on `ProxyError`/`ConnectionError`**, so the common Windows "dead proxy" case usually recovers without user action — still surface the diagnostic ask if the retry also fails.

> 🔴 **Outbound Authorization Gate (auto-executed)**: the script checks authorization automatically before the serial refinement outbound call (same rules as Step 1). If unauthorized, it falls back to the local draft directly; agent should prompt the user to confirm.

```
step 2 local answer + step 3/4 external data → foreground serial call to refine_answer.py (with draft_answer)
              ├─ Coze returns within 60s → adopt Coze result
              └─ Coze fails / times out  → fall back to local answer + external data
```

### Serial call style (stdin pipe preferred)

🔴 **payload MUST include `query_meta` with `difficulty`** (the local route.py label is a *hint*; Coze re-estimates it via LLM. Missing/illegal difficulty still falls back to `complex` locally — harmless, since Coze overrides anyway; always pass the route.py label for the Feishu collection to be meaningful):

```bash
# Bash / Git Bash — stdin pipe (zero encoding risk; handles Chinese punctuation in draft_answer)
echo '{"query_meta":"{\"difficulty\":\"complex\",\"category\":\"methodology:B\",\"accuracy\":\"normal\"}","original_question":"…","draft_answer":"…"}' | python scripts/refine_answer.py

# PowerShell here-string (recommended, no escaping needed)
@'
{"query_meta":"{\"difficulty\":\"complex\",\"category\":\"methodology:B\",\"accuracy\":\"normal\"}","original_question":"…","draft_answer":"…"}
'@ | python scripts/refine_answer.py
```

---

## Step 6 — Final answer (Final Output)

**Goal**: return the final answer to the user. **Note: this step does almost no answer processing; it only returns the answer directly.**

| mode | source |
|---|---|
| Local-only (simple) | the local answer from step 2 |
| Race (middle) | the result from step 2 |
| Serial (complex) | the result from step 5 |

**Output**: the formal result returned to the user.

### 🔴 Final pre-output check (HARD GATE)

Before outputting **any** answer content, confirm item by item:

| difficulty | check items |
|---|---|
| `middle` | ☐ **Step 1 fired Coze fire-only** (the most easily skipped gate) → ☐ step 2 already collected → ☐ winner decided → output = winner content |
| `middle` (fallback) | ☐ if `--collect` errored / failed / returned empty → local answer adopted, **no appended Coze wait** |
| `simple` (local-only) | ☐ Step 0 classified `simple` → Step 2 local answer written from `knowledge/` (single retrieval, no Coze, no collect) → output = local answer |
| `complex` | ☐ step 5 already called Coze serially in foreground (with draft_answer) or timed out and fell back → output = winner content |
| in-session follow-up (not a new question) | ☐ step 0 classified as **not a new question** (a follow-up / clarification on an existing answer) → output local answer directly (difficulty no longer constrained) |

**Any unchecked item → forbidden to output content; must roll back and complete the missing step.**

---

## Call-style summary (zero temp files · cross-platform safe)

| priority | style | command template | when to use |
|---|---|---|---|
| **1 (preferred)** | stdin pipe | `echo '{…}' \| python refine_answer.py` | **All** fire-only & serial calls — zero encoding risk, Chinese punctuation passes through directly |
| **2** | `--payload-inline` | `python refine_answer.py --payload-inline '{…}'` | Only when JSON contains no Chinese punctuation (pure English / digits / underscores) |
| **3 (fallback)** | file path | `python refine_answer.py /path/to/file.json` | **Only** `--collect` (backward compat) |

**Forbidden**:
- ❌ `Write`/`Bash cat >` to write temp JSON files (encoding risks: Chinese quotes / BOM / line endings)
- ❌ `/tmp` paths (Git Bash ↔ Python path mismatch under Windows)
- ❌ file paths in fire-only / serial (completely unnecessary)

**Encoding strategy (core principle: Chinese punctuation → stdin pipe)**:

`--payload-inline` wraps JSON in single quotes in Bash/Git Bash, but if the JSON string contains Chinese curly quotes (`"` `"`) or Chinese commas (`，`), it breaks the outer quote structure and causes `JSONDecodeError`. **Measured: if draft_answer or original_question contains Chinese punctuation, `--payload-inline` always fails.**

- **Default to stdin pipe** (priority 1): `echo '{JSON}' | python refine_answer.py` — JSON passes through as-is, zero escaping/encoding risk
- `--payload-inline` is limited to pure English payloads (e.g., only `original_question` + `query_meta`, draft_answer left empty)
- **PowerShell**: use here-string `@'…'@` (no escaping needed)
