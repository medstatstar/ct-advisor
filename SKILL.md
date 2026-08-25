---
slug: ct-advisor
name: ct-advisor
displayName: 临床试验总顾问 / Clinical Trial Chief Advisor
cn_name: 临床试验总顾问
version: 0.9.103
invocable: true
required_commands: [python]
summary: "面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问。方法学/设计/合规/QC/语气类问题在内部走 A–J 工作流并转发远程 Coze 引擎精校；统计计算转交 ct-samplesize；原始数据/竞品情报类需求路由到 ct-registry / ct-safety / ct-literature 并在代码内缝合三源产出。本技能会在本机运行兄弟技能、保留语言偏好/上下文缓存/长期记忆等本地状态，并支持可选的脱敏错误报告。"
description: "面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问。方法学/设计/合规/QC/语气类问题在内部走 A–J 工作流并转发远程 Coze 引擎精校；统计计算转交 ct-samplesize；原始数据/竞品情报类需求路由到 ct-registry / ct-safety / ct-literature 并在代码内缝合三源产出。本技能会在本机运行兄弟技能、保留语言偏好/上下文缓存/长期记忆等本地状态，并支持可选的脱敏错误报告。 / The ct-series TOTAL ENTRY POINT across the full clinical-development lifecycle — a cloud-assisted clinical-trial advisor. Methodology / design / compliance / QC / tone questions run in-house through workflows A–J and are forwarded to the remote Coze engine for refinement; sample-size computation is handed to ct-samplesize; raw-data and competitive-intel needs route to the three sibling data skills (ct-registry / ct-safety / ct-literature) and are stitched in code. The skill runs sibling skills locally, keeps local state (language preference / context cache / long-term memory), and supports an optional de-identified bug report."
license: MIT
triggers:
  - "ct console"
  - "ct-advisor"
  - "clinical trial advisor"
  - "ct advisor"
  - "trial methodology"
  - "clinical trial methodology"
  - "clinical research advisor"
  - "trial design"
  - "GCP question"
  - "临床试验情报"
  - "临床试验顾问"
  - "临床试验总顾问"
trigger_scope: "触发词仅限临床试验方法学/法规/设计/合规/QC/情报类问题；不主动匹配非临床类通用问答；不含文件系统写入与系统级 API 调用。"
metadata:
  openclaw: { emoji: "🛠️", icon: "assets/icon.svg" }
  authors: ["medstatstar", "phoe-zip"]
  family: ct-series
  homepage: "https://github.com/medstatstar/ct-advisor"
permissions:
  scope: "user-space-only"
  network: "controlled-coze-opt-in"
  network_note: "All **non-vague** questions are forwarded to Coze (single call, `--ship` / `orchestrate.py`); `vague` questions are clarified locally via `scripts/clarify_loop.py` first, then forwarded with `difficulty=\"vague\"`; local knowledge base is fallback only (Coze failure); skill needs are judged by Coze (`need_tool` card → local execution + stitch); `scripts/route.py` labels difficulty deterministically at entry."
  filesystem: "Read-only to own files (writes only config.json + optional data/qa_log.jsonl, off by default); no confidential data leaves locally — Coze payloads sanitized, query_origin is a stable per-machine sha256 hash (sha256 of hostname + salt, non-PII, not host-readable)."
adapted_from: "https://github.com/A-xin946/clinical-trial-advisor"
dependencies:
  - {slug: ct-registry,   tier: A}
  - {slug: ct-safety,     tier: A}
  - {slug: ct-literature, tier: A}
  - {slug: ct-samplesize, tier: A}
  - {slug: meta-analysis, tier: A}
tier: A
---

# Clinical Trial Chief Advisor

## Language

- **English guide** → [README.md](https://github.com/medstatstar/ct-advisor/blob/main/README.md) · **中文指南** → [README_zh-CN.md](https://github.com/medstatstar/ct-advisor/blob/main/README_zh-CN.md)
- **This SKILL.md body is English-only, agent-facing.** Bilingual walkthroughs live in the two READMEs.
- Bilingual auto-switch: the answer language follows the user's question language (English question → English answer, Chinese question → Chinese answer).

## Overview

Single entry point for the ct-series: methodology / design / compliance / QC / tone answered in-house (workflows A–J from `knowledge/`); sample-size hands off to `ct-samplesize`; raw-data / competitive-intel route to `ct-registry` / `ct-safety` / `ct-literature` (broad asks stitched in-house from the trio).

## Requirements

| Item | Requirement |
|---|---|
| Runtime | `python3` stdlib; read `knowledge/` directly |
| Sibling skills | `ct-registry` / `ct-safety` / `ct-literature` / `ct-samplesize` / `meta-analysis` (degrade gracefully if missing, never fabricate) |
| Refiner (Coze) | `scripts/refine_answer.py --ship` (data-intel preferred via `scripts/orchestrate.py`) POSTs 3 top-level variables (`query_meta` / `original_question` / `draft_answer`, with `query_meta` nesting difficulty/category/accuracy/query_origin) to `ct-advisor.coze.site/run`. Entry gate: `scripts/route.py` (deterministic, LLM-free) labels difficulty once; **vague** → Local Clarify Loop then Coze; **simple/middle/complex** → verbatim forward with `query_meta.difficulty` set. Credential embedded in `adapters/coze_token_embedded.py` (obfuscated public token — keep as-is). 60s timeout → fallback to local `knowledge/` (fault fallback). Coze may return a `need_tool` card → local executes the skill and stitches. |

## Attachment handling (docx / pdf / ppt)

> **Governance pointer (2026-08-19 rollback):** the layered conversion strategy, user prompts, and confidentiality boundary are consolidated into **ct-base §6.7** (`ct-base/docs/02-governance-redlines.md`); this skill no longer re-declares them — on conflict, ct-base §6.7 wins. The shared converter lives in `ct-base/scripts/office_to_md.py` (injected into each skill at publish). This section keeps only ct-advisor-specific **implementation details**:

1. Append the converted text to the **`original_question`** field and run the normal pipeline (`route.py` → `refine_answer --ship`), wrapped as:
   `...要求：撰写完整规范。以下是模板内容：\n---\n{md}\n---`
2. Coze `full_analysis`'s "template induction" mode recognizes this format → generates the full spec body; gaps are marked explicitly, never padded.
3. The local converter is this skill's `scripts/office_to_md.py` (same source as the base shared artifact, shipped with the package).

## Knowledge Map & Read Discipline (2026-08-05)

`knowledge/` = 15 topic files (`ref-ops-*` / `ref-reg-*`). Route via `knowledge/reference-index.md`; search via `search_refs.py "<kw>" --context 3`; single Read ≤ 60 lines. Hard rules:

1. **🔴 ONE local lookup per turn (HARD GATE)** — a single locate/retrieve (`search_refs.py` or one Read), then stop regardless of hit/miss. Never chain a second lookup or multi-step local reads.
2. **🔴 On miss, go straight to Coze (HARD GATE)** — never re-Read `reference-index.md` / any `ref-*`; hand the original question directly to Coze remote (the single information authority).
3. **🔴 No external network retrieval after any local lookup (HARD GATE)** — never stack "local lookup + sibling-skill outbound". Sibling-skill data is fetched **only** via the Coze-issued `need_tool` card (step 3b), never by local initiative.
4. `knowledge/system_prompt.md` = Coze-side deployment copy, do not read locally; `prompts.md` only when menu strings are needed. After editing any `ref-*`, rebuild the index via `update_reference_index.py`.
5. External search fallback: on local miss + Coze under-grounded, list authoritative sites from `references/search-sites.md` for the user to consult — never visit sites on their behalf / fabricate content.
6. **🔴 Language alignment (2026-08-21, C-combo: Coze-side consistency fix + local translation fallback):** if the Coze answer's language disagrees with the question (English question often returns Chinese), before passing through **only translate the language** — translate the narrative to the question language, **do not add/remove content, change numbers, or reorder**; proper nouns / drug names / regulation names and structured data (table cells, JSON, xlsx paths) stay verbatim. This is language alignment, not "rewriting Coze text". The stitching layer (source labels / table headers) already auto-switches by `original_question` language via code (`orchestrate.py` / `refine_answer.py` `_detect_lang`) — no manual handling needed.

## Answer Workflow (steps 0–6)

> **Core principle:** payload stays in-memory pipeline throughout (`--payload-inline` or stdin); **prohibit** Write/Bash temporary JSON files.
> **Detailed flow:** full description, I/O, boundary conditions per step → `references/steps.md`

| Step | Responsibility | Forward (all questions) |
|---|---|---|
| **1 Difficulty gate** | 🔴 run `python scripts/route.py "<q>"` **once** (code-based, instant, no KB read) → label. **vague** → Local Clarify Loop (`clarify_loop.py`) then re-gate on the enriched question and route per the table below (data-intel → `orchestrate.py` preferred, else `--ship`); **simple/middle/complex** → forward via `scripts/orchestrate.py` (data-intel preferred) or `refine_answer.py --ship` (fallback), with `query_meta.difficulty` set | → 2 |
| **2 Receive & route** | inspect the structured result — 3 branches below | → 3a / 3b / 3c |
| **3a Answer** | `need_tool` empty → ship Coze `final_answer` as-is | → 6 |
| **3b Skill card** 🔴 | `need_tool` non-empty ⇒ **MUST** run `scripts/handle_need_tool.py` (no shortcut); `need_params` → ask user for missing params (never fabricate) → re-run; `ok` → stitch skill result into Coze `draft_answer` (the skeleton) → deliver (never re-send Coze) | → 6 |
| **3c Fallback** | Coze timeout / network / HTTP error (`FALLBACK` marker) → answer from local `knowledge/` (A1/A2 routing) + warning | → 6 |
| **6 Final Answer** | Return result directly | — |

### 🔴 Outbound Authorization Gate

Runs automatically inside `refine_answer.py` before each outbound HTTP call (agent never triggers it manually). Rules: ① endpoint in `config.json` → `auto_approve_endpoints` → allow; ② authorized earlier this session → allow; ③ otherwise → show the confirmation prompt below (first call only; never expose step / workflow / internal terminology). **🔴 agent NEVER edits `config.json`** (incl. `auto_approve_endpoints`) — whitelist is author-preset (`ct-advisor.coze.site/run` already in it, so it never prompts); if the user wants another endpoint whitelisted across sessions, the USER adds it explicitly (agent may guide, not write). Unauthorized endpoint → `[AUTH-BLOCK]` → user-confirm → on decline, local-fallback answer with "本次未使用云端分析" note (never block):

```
⚠️ ct-advisor needs to send your question to an external server for intelligent analysis:
   Target server: https://ct-advisor.coze.site/run
   Content sent: your original question (no personal identifying information)
⚠️ Note: the local reference library is limited; most domain expertise relies on cloud-based
   search and analysis. If you decline, answer quality & coverage will be significantly reduced.
Allow this send? You will not be asked again this session.
```

### 🔴 Forward & stitch HARD GATES (summary)
- **🔴 Forward-first (HARD GATE):** EVERY question is forwarded to Coze — there is **no local-answer shortcut** ("KB already has the answer" never skips Coze; local `knowledge/` answers only when Coze fails). Local is the **fallback**, Coze is the referee.
- **🔴 Pipe-only delivery (HARD GATE, 2026-08-15):** you MUST call `scripts/refine_answer.py --ship` (NOT `--forward`). `--ship` calls Coze, runs any `need_tool` sibling skill **in code**, and emits the **final user-facing answer** wrapped in `<<<CT_ANSWER_START>>>` … `<<<CT_ANSWER_END>>>`. Your **ONLY** action is to output the text between those delimiters **verbatim** (character-for-character) — do **NOT** add a lead-in, summary, rephrasing, markdown reformat, or "here is your answer" wrapper; do **NOT** re-merge / re-write / re-stitch. **You are a pipe, not the author — Coze + code are the authors.** (`--forward` still exists but only returns raw JSON for debugging; never ship from it.)
- **🔴 Code orchestrator for data-intel (2026-08-15):** for sample-size / registry / safety / literature questions you SHOULD call `scripts/orchestrate.py` (NOT `--ship`) — it is the **code-only orchestrator**: at entry it predicts the needed ct skill (high-confidence prefetch via `scripts/route_tool.py`), fires Coze **and** the predicted skill **in parallel** (threads), merges both results, and **decides in code** whether the answer is complete. It emits the same `<<<CT_ANSWER_START>>>`…`<<<CT_ANSWER_END>>>` wrapped answer when sufficient (pipe it verbatim), or a `<<<CT_TOOL_DELEGATE>>>` block when a ct skill still must run. In the delegate case **you (local LLM) are NOT the orchestrator** — you only: ① confirm / ask the user for the missing params listed in the block (never fabricate), ② hand the card to `python scripts/refine_answer.py --card-inline '<JSON>'` so **code** executes the skill + stitches + wraps. You do **NOT** judge sufficiency and do **NOT** rewrite Coze text.
- **Local-retrieval discipline (HARD GATE):** local DB retrieval capped at **ONE per turn** for the 3c fallback — never chain multi-step local reads.
- **need_tool is Coze-judged:** the agent NEVER decides by itself that a sibling skill is needed — it only executes the card Coze returns (mechanical lookup in `scripts/tool_mapping.json`).

→ Step definitions, exception handling, invocation → `references/steps.md`

### Step 0.5 · Local Clarify Loop (pure-local, no outbound)

Entered **only** when `route.py` returns `vague` (the gate above). Run `python scripts/clarify_loop.py` (same in-memory pipeline as `refine_answer.py`, the **heuristic menu**) **before** forwarding: 1–3 high-value questions per round, hard-capped at **3 rounds** (hitting the cap still proceeds, never loops). On `decidable`/`forced_decide`, **re-run `route.py` on the enriched question** and route per the table below (data-intel → `orchestrate.py` preferred; methodology → `--ship`), passing `query_meta.difficulty="vague"` for the original classification.

**Call style (zero temp files):** stdin pipe `echo '{…}' | python refine_answer.py --ship` (Chinese punctuation safe) — **Forbidden**: Write/Bash temp JSON files, `/tmp` paths. PowerShell: here-string `@'…'@`. Full rules + encoding caveat → `references/steps.md` "Call-style summary".
**🔴 Payload keeps `query_meta`** (difficulty/category/accuracy may be empty — server-side routing + Feishu collection tolerate blanks; script defaults `difficulty` to `complex`). Example: `echo '{"query_meta":"{\"difficulty\":\"complex\",\"category\":\"\",\"accuracy\":\"\"}","original_question":"…"}' | python refine_answer.py --ship`
**🩺 Coze failure diagnosis (user-friendly):** on fallback (stderr `FALLBACK` / `ProxyError` / `Timeout`, or the stdout ask "…是否允许我自动进行问题诊断排查？"), **ask the user first** — "Coze 云端服务暂时不可用，是否允许我自动诊断排查？" If allowed → run `python scripts/check_coze.py` once, fix the root cause (stale system proxy / offline / token), retry; if declined → deliver the local answer **with a prominent warning**: 「无法连接 Coze 服务，答案未经过精校，请谨慎使用」. v0.9.60+ auto-retries bypassing the system proxy on `ProxyError`/`ConnectionError`.

---

### Session continuity
Once `@skill:ct-advisor` is invoked, its instructions + `knowledge/` stay in thread — **do NOT re-invoke the skill on follow-ups**; re-run gate 0 each turn. Off-topic / meta requests (e.g. "modify this skill") drop the framing and are handled as normal assistant work (no methodology workflow, no Coze refine).

**Type-B follow-ups (implicit carry-over, no anaphora)** — since v0.9.70 (rewritten to **mode B** on 2026-08-25, aligned with ct-base `references/continuity.md` §2), `refine_answer.py --ship` auto-attaches bounded conversation history before forwarding: `scripts/context_stitch.py` **always** exports the structured `conversation_history` (via `pack_history_for_coze`) and forwards it to Coze — the remote LLM judges relevance/inheritance. Local code does **NOT** detect follow-ups or rewrite the question (the old `is_followup()` regex + self-contained stitch was hard-deprecated: fragile, missed long-form design-evolution follow-ups). `config/context_cache.json` is a **write-through mirror only** (TTL 2h / ≤10 rounds + 24h hard cap), never the sole continuity source. Pure local code — no LLM (judgment delegated to Coze), no new outbound contract.

### Personalization (tone writing + local user memory) — ⚠️ DEFERRED (not enabled)

Tone writing (`tone_profile`) and local user memory (`memory_context`) are **temporarily disabled**: the deployed Coze workflow (v1.5 contract) does not implement these fields, so local injection is silently ignored. The scripts (`tone_matcher.py` / `memory_manager.py`) and the `--tone` / `--memory` CLI flags remain in place for future use but **MUST NOT be invoked**. Re-enable only after the Coze workflow ships the v1.6 contract fields (2026-08-12 decision).

### Performance discipline (latency guards — keep these, they are why this skill is fast)

- **🔴 HARD GATE: minimal local work before `--forward`** — between receiving the question and firing Coze, the **only** permitted local work is **one** deterministic, LLM-free difficulty call: `python scripts/route.py "<q>"` (stdlib-only, instant, ~tens of ms). It performs **NO `knowledge/` read, NO `search_refs.py`, NO multi-round local retrieval** — those historically cost 10–20 tool round-trips (≈3–4 min) and are the #1 latency failure mode. For `vague`, the clarify loop (`clarify_loop.py`) is a bounded pure-local menu (≤3 rounds) that still precedes Coze. The 3c fallback (local answer) happens **only after** Coze fails.
- **Search backoff:** on `search_refs.py` 0 hits → do NOT chain more local reads; hand the original question straight to Coze remote. **Long sessions:** prune stale context before step 2 (keep recent turns + final conclusion; never drop info still needed).
- **🔧 Latency observability (F, 2026-08-23):** `refine_answer.py --latency-report --round-id <qid>` tallies tool round-trips per question (counter in `.runtime/`, gitignored, pure-local, no network call); `--latency-threshold` (default 10) emits a `[WARN]` when a round exceeds it — the pre-fire delay regression signal. The invariant checklist lives in `references/steps.md` "延迟护栏单测式检查表（F）". → `references/ADVANCED.md` for the full latency discipline.

## Code Orchestrator (`orchestrate.py`, 2026-08-15)

**Code-only orchestrator + LLM-delegated ct-skill execution.** `scripts/orchestrate.py` is the recommended entry for data-intel questions (sample-size / registry / safety / literature). It is the **fully-automatic orchestrator** — the local LLM is **NOT** the orchestrator:

1. **Entry prefetch (code, no LLM)** — calls `scripts/route_tool.py` to predict the needed ct skill at **high confidence only** (clear tool triggers, not definition / pure-methodology / vague). Low-confidence / hidden needs are left to Coze's `need_tool` (fallback).
2. **Parallel fire (code, threads)** — fires Coze (`refine_forward`) **and** the predicted ct skill (via `handle_need_tool.py` subprocess) in parallel; the prefetch does not wait for Coze.
3. **Merge + decide (code, no LLM)** — merges Coze's `final_answer` + `need_tool` with the prefetch result, and **decides in code** whether the answer is complete:
   - **Sufficient** → emits the final answer wrapped in `<<<CT_ANSWER_START>>>` … `<<<CT_ANSWER_END>>>` (same protocol as `--ship`) — you pipe it verbatim.
   - **Still needs a ct skill** → emits a `<<<CT_TOOL_DELEGATE>>>` block (structured card: `need_tool` / `params` / `draft_answer` / `original_question` / `missing_params`).
4. **LLM delegates the ct-skill call** — when you see `<<<CT_TOOL_DELEGATE>>>`, you are **not** orchestrating: you only ① confirm / ask the user for `missing_params` (never fabricate), ② hand the card to `python scripts/refine_answer.py --card-inline '<JSON>'`, where **code** executes the skill + stitches + wraps the final answer. You do **NOT** judge sufficiency and do **NOT** rewrite Coze text.

This satisfies the red line: **code decides**, **LLM only executes the skill + asks for missing params**; the final answer assembly is always code (deterministic stitch + delimiter wrap).

## Routing & Total Entry

| Need | Route |
|---|---|
| Any question | **1)** code gate `route.py` → label; **vague** → clarify loop then Coze; **simple/middle/complex** → **preferred:** `scripts/orchestrate.py` (code orchestrator: prefetch + parallel Coze/skill + decide → emits wrapped answer to pipe, or `<<<CT_TOOL_DELEGATE>>>` to hand the ct-skill call to you); **fallback:** `refine_answer.py --ship` (no prefetch) — both emit delimiters, pipe-only |
| Sibling-skill data (registry / safety / literature / sample-size) | Code predicts (high-confidence) + Coze judges; when a ct skill must run, `orchestrate.py` emits `<<<CT_TOOL_DELEGATE>>>` → you (LLM) hand the card to `refine_answer.py --card-inline` (code executes + stitches). With `--ship` only, the stitch is done in code on Coze's `need_tool`. |
| Coze failure | Local `knowledge/` fallback (A1/A2 routing) + warning |
| Unsure what you need | Local clarify loop (`scripts/clarify_loop.py`) — still pure-local, no outbound |

Missing sibling skill → state what's required + give its GitHub address (`https://github.com/medstatstar/<slug>`), do the prep you can, label the reply **"data not retrieved"** (never fabricate).

**🔴 Skill-card execution protocol (need_tool, MUST — 强制硬门):** when Coze returns a non-empty `need_tool` you **MUST** run the sibling skill — **no shortcut**: never answer from Coze `final_answer` alone, never answer from local `knowledge/`, never skip the call. **With `--ship` (the normal path) the stitch is done IN CODE** — `refine_answer.py --ship` calls `handle_need_tool.py` itself and emits the merged answer wrapped in delimiters; you do **NOT** stitch, you only pipe. **With `orchestrate.py` (preferred for data-intel)** the code decides sufficiency; when a ct skill still must run it emits a `<<<CT_TOOL_DELEGATE>>>` block — you are **NOT** the orchestrator: read the card (`need_tool` / `params` / `draft_answer` / `original_question` / `missing_params`), ask the user for any `missing_params` (never fabricate), then run `python scripts/refine_answer.py --card-inline '<JSON>'` (code executes the skill + stitches + wraps). You do **NOT** judge sufficiency and do **NOT** rewrite Coze text. Only two cases need you (both are within the `--ship` / `--card-inline` wrapped-answer path):
- **`need_params`** (a `<<<CT_NEED_PARAMS>>>` block appears inside the delimiters) → ask the user for the listed missing params (never fabricate), rebuild the card JSON (keep the same `draft_answer` / `need_tool`, fill `params`, keep `original_question`), then re-run `python scripts/refine_answer.py --card-inline '<card>'` (skips Coze, re-runs the skill in code, emits the stitched answer).
- **Execution failure** (`补充信息获取失败` inside the delimiters) → deliver the Coze `draft_answer` portion as-is + one-line note (never block).
(Legacy/debug only: with `--forward` you would build the card manually — `draft_answer` := the `final_answer` string verbatim; `need_tool`/`params` := same; `original_question` := user's verbatim question — then run `handle_need_tool.py --card` and stitch locally. Not needed when using `--ship`.) Confidential C/D-tier skills never have their results sent to Coze (local-only by design).

## Boundaries with Sibling Skills

`ct-registry` / `ct-safety` / `ct-literature` → read real outputs for grounding, never re-search; `ct-samplesize` computes n (this skill provides the parameter framework only); `meta-analysis` handles R meta plots; `ct-base` = internal base (i18n / excel_style / series safety model).

**方案评审 / 修订风险（2026-08-19）：** this skill (Coze side) provides **basic protocol review** (point-by-point judgment + severity grading + revision suggestions). **In-depth protocol review needs `ct-protocol`** for more complete results — multi-role review (PI / site physician / regulator), amendment-risk scoring, structured review.json, and **protocol stays local (offline)**. After a user gets a basic review on the Coze side, if they need in-depth review / amendment-risk assessment, **explicitly guide them to the local `ct-protocol` skill** (`@skill:ct-protocol`); do not impersonate its capability.

## China Regulatory Depth (C-layer)

CTA/IND 60-day tacit approval, Type A/B/C communication meetings, registration ≠ tacit approval — see `knowledge/ref-regulatory-versions.md` + `knowledge/reference-index.md`; verify any version / status / deadline in real time against the official original.

## Quality Gate & Stop Rules

Pre-delivery checks and stop conditions live in `knowledge/system_prompt.md` "Quality gate & stop rules". Core red line: **never expose in user-visible content personal info, subject info, unpublished project data, private path or access credential.**

**Presentation rules (user-mandated, hard)** — deliver only the answer (refined stdout) + essential cited basis. **Never emit any workflow / process narration to the user** — this explicitly covers: step 0–6 labels ("Step 2", "Gate 0", "Step 6"), difficulty tags (`simple` / `middle` / `complex` / `vague`), forward / need_tool / fallback mechanics, routing / triage narration, progress / status broadcasts, self-process recaps, memory / CHANGELOG housekeeping notes, follow-up CTAs, redundant closing summaries, internal-pipeline wording ("refined by Coze", "assembling payload"), and disclosure of internal knowledge sources. Internal reasoning may still use these labels freely — they just must **never** appear in user-visible text. See ct-base §6.2 / §6.3.

**🔔 Forward-mode user notice (the ONLY allowed process message)** — emit **exactly one** brief user-facing notice **immediately before firing the Coze call** (`refine_answer.py --ship` / `orchestrate.py`), i.e. **AFTER** `route.py` has returned (the difficulty gate is local, sub-second — no notice needed for it) and any clarify loop has finished. The notice covers the wait for the cloud response, not the local gate. Example:
> 正在调用云端分析引擎，请稍候…

(English: `Please wait while the cloud analysis runs…`) Do **NOT** repeat it, do **NOT** add any other process chatter.

### Bug Report (§20.3 · ct-base, optional sanitized outbound)
On a detected skill defect (CLI≠0 / R engine error / user questions result) or **explicit user request** ("report a bug" / "反馈问题"), `adapters/bug_report.py` offers a sanitized 11-key report (no raw input; user-approved `description` only) to `https://ct-bugreport.coze.site/run`. **Two-stage confirmation** (propose-with-preview → send) is mandatory — the full sanitized report (`render_report_text`) is shown together with the propose message, and one explicit user consent sends it (2026-08-21 simplified from three-stage, keeping pre-send content review + explicit release); capped at 1 unsolicited offer/session, but user-initiated requests are unlimited. Public credential embedded (obfuscated) in `adapters/bug_report.py`. Invoke: `python adapters/bug_report.py --error-type <t> --test <name> --description "<free text>" [--send]` (add `--send` only after the user confirms). After a successful send, the endpoint returns `history` (last submission for the same `query_origin`, or `""`); compose the reply from `confirm_thanks(locale)` + `build_followup(history, locale)` — bilingual, auto-switched by `locale` (2026-08-22 history receipt): empty `history` → end; `history.resultstr == "done"` → also show the fix note from `history.memo`; otherwise show "not yet fixed". All user-facing strings are bilingual via `_MSGS` and `_current_locale()` auto-detection. → `references/ADVANCED.md` for the full bug-report protocol.

## Changelog — full history (0.8.0 → 0.9.30+) → **[CHANGELOG.md](CHANGELOG.md)**
