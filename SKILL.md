---
slug: ct-advisor
name: ct-advisor
displayName: Clinical Trial Chief Advisor / 临床试验总顾问
cn_name: 临床试验总顾问
version: 1.0.3
invocable: true
required_commands: [python]
summary: "面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问。方法学/设计/合规/QC/现场执行类问题直接提交云端 Coze 引擎分析；其余更深入的专业问题调用 ct系列兄弟技能处理，并整合回复结果。"
description: "The single entry point for the ct-series across the full clinical-development lifecycle — a cloud-assisted clinical trial advisor. Methodology / design / compliance / QC / site-execution questions are submitted directly to the cloud Coze engine for analysis; other, deeper specialist questions are handled by sibling skills such as ct-samplesize / ct-registry / ct-safety / ct-literature, with the results integrated. / 面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问。方法学/设计/合规/QC/现场执行类问题直接提交云端 Coze 引擎分析；其余更深入的专业问题调用 ct系列兄弟技能处理，并整合回复结果。"
license: MIT
triggers:
  - "ct-advisor"
  - "clinical trial advisor"
  - "ct advisor"
  - "trial methodology"
  - "clinical trial methodology"
  - "clinical research advisor"
  - "trial design"
  - "GCP question"
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
  network_note: "All **non-vague** questions are forwarded to Coze (single call, `--ship` / `orchestrate.py`); `vague` questions are clarified locally via `scripts/clarify_loop.py` first, then forwarded with `difficulty=\"vague\"`; local knowledge base is fallback only (Coze failure); skill needs are judged by Coze (`need_tool` card → local execution + stitch) **only for strong, uniquely-directed triggers** — generic words and definition / methodology / document questions are never delegated, and instead get a **trailing install / invoke suggestion** after the own-capability answer; `scripts/route.py` labels difficulty deterministically at entry."
  filesystem: "Read-only to own files (writes only config.json + optional data/qa_log.jsonl, off by default); no confidential data leaves locally — Coze payloads sanitized, query_origin is a stable per-machine sha256 hash (sha256 of hostname + salt, non-PII, not host-readable)."
adapted_from: "https://github.com/A-xin946/clinical-trial-advisor"
dependencies:
  - {slug: ct-registry,   tier: A}
  - {slug: ct-safety,     tier: A}
  - {slug: ct-literature, tier: A}
  - {slug: ct-samplesize, tier: A}
# meta-analysis 为 referral-only：不经 need_tool 自动调用（需数据抽取 + 重型 R 管线），
# 由本技能引导用户显式 @skill:meta-analysis 调用；故不列入自动依赖 / 自动路由。
tier: A
---

# Clinical Trial Chief Advisor

## Language

- **English guide** → [README.md](https://github.com/medstatstar/ct-advisor/blob/main/README.md) · **Chinese guide** → [README_zh-CN.md](https://github.com/medstatstar/ct-advisor/blob/main/README_zh-CN.md)
- **This SKILL.md body is English-only, agent-facing.** Bilingual walkthroughs live in the two READMEs.
- Bilingual auto-switch: the answer language follows the user's question language (English question → English answer, Chinese question → Chinese answer).

## 🔴 Pipe-Only Hard Contract (highest priority — overrides everything below)

> When `refine_answer.py --ship` (or `orchestrate.py`) prints `<<<CT_ANSWER_START>>>` … `<<<CT_ANSWER_END>>>`, your **ONE AND ONLY** action is to extract the text between those delimiters and output it **verbatim, character-for-character**. You are a **pipe**, not the author.

**Forbidden — this list is exhaustive and non-negotiable:**
- Do **NOT** rewrite, rephrase, reorder, or "polish" the text.
- Do **NOT** add / remove / modify any Markdown (headings, bold, lists, tables, blockquotes).
- Do **NOT** append a summary, lead-in, closing remark, or "key takeaways".
- Do **NOT** translate or align language (the code already handles that).
- Do **NOT** inject process narration ("Step 2", "Coze returned", "assembling payload").
- Do **NOT** strip or alter the `checksum:` line that follows `<<<CT_ANSWER_END>>>`.

**The only permitted post-delimiter action:** if a `<<<CT_TOOL_DELEGATE>>>` block appears, follow its instructions (ask user for `missing_params`, then call `refine_answer.py --card-inline`). If a `<<<CT_NEED_PARAMS>>>` block appears, ask the user for those params. Otherwise: **output and stop**.

This rule exists because the local LLM's "helpful formatting" instinct destroys Coze-delivered content (breaks C5 formatting, alters numeric precision, injects unsolicited content). If you are tempted to "clean up" the answer, that temptation **is** the bug — suppress it.

## Overview

Single entry point for the ct-series: methodology / design / compliance / QC / site-execution answered in-house (workflows A–J from `knowledge/`); sample-size hands off to `ct-samplesize`; raw-data / competitive-intel route to `ct-registry` / `ct-safety` / `ct-literature` (broad asks stitched in-house from the trio).

## Requirements

| Item | Requirement |
|---|---|
| Runtime | `python3` stdlib; read `knowledge/` directly |
| Sibling skills | **Tier A · listed on SkillHub** (non-confidential input, publicly released): `ct-registry` / `ct-safety` / `ct-literature` / `ct-samplesize` — auto-routed via `need_tool`, installable on user consent (see "A/B Tier Gate"); `meta-analysis` — referral-only (guided to `@skill:meta-analysis`, never auto-invoked). **Tier A · NOT yet listed**: `ct-pipeline` (public-intel orchestration) / `ct-synthdata` (library fixture) → `unpublished_a`, announce as not publicly released and answer from own capability; `ct-synthdata` is a library fixture, not a user-facing entry. **Tier B** (confidential input, **not publicly released**): `ct-protocol` / `ct-csr` / `ct-analysis` / `ct-sdtm` / `ct-eligibility` etc. — never installable; state that the skill is needed but unreleased, then answer from own capability |
| Refiner (Coze) | `scripts/refine_answer.py --ship` (data-intel preferred via `scripts/orchestrate.py`) POSTs 3 top-level variables (`query_meta` / `original_question` / `draft_answer`, with `query_meta` nesting difficulty/category/accuracy/query_origin) to `ct-advisor.coze.site/run`. Entry gate: `scripts/route.py` (deterministic, LLM-free) labels difficulty once; **vague** → Local Clarify Loop then Coze; **simple/middle/complex** → verbatim forward with `query_meta.difficulty` set. Credential embedded in `adapters/coze_token_embedded.py` (obfuscated public token — keep as-is). 90s timeout → fallback to local `knowledge/` (fault fallback). Coze may return a `need_tool` card → local executes the skill and stitches. |

## Attachment handling (docx / pdf / ppt)

> **Governance pointer (2026-08-19 rollback):** the layered conversion strategy, user prompts, and confidentiality boundary are consolidated into **ct-base §6.7** (`ct-base/docs/03-interaction-constraints.md`); this skill no longer re-declares them — on conflict, ct-base §6.7 wins. The shared converter lives in `ct-base/scripts/office_to_md.py` (injected into each skill at publish). This section keeps only ct-advisor-specific **implementation details**:

1. Append the converted text to the **`original_question`** field and run the normal pipeline (`route.py` → `refine_answer --ship`), wrapped as:
   `...Requirement: write the full spec. Template content below:\n---\n{md}\n---`
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
7. **🔴 Coze cache behaviour (2026-09-09) — fully automatic, no agent action needed:** a cached-hit answer carries a built-in "from cloud cache (previous run)" declaration at its top, and user challenges/requests to re-verify force fresh regeneration on the Coze side (accuracy=good write gate, 6-month TTL, punt-content read gate). Do **not** re-generate, re-run registry, or strip the declaration manually; just pass the answer through verbatim (translate only per rule 6). The cache policy and its gate wordlists are maintained on the Coze side and are fully automatic; no local action is required.

8. **🔴 Dual-knowledge-base architecture (2026-09-16, prevents P0 "live but ineffective")**: ct-advisor has **two** knowledge bases with completely different roles; modifying only one of them will get the new content zero hits in production —
   - **Local `knowledge/` (frozen, no longer updated)**: only serves as the offline Coze-failure fallback (3c fallback). **Adding/editing content here does not go live** — production retrieval uses the Coze-side copy only.
   - **Coze-side `adapters/coze/knowledge/` (must be updated at all times)**: the single source of truth for production retrieval. Any knowledge change **must land here**; the local copy is not synced.
   - **Standard post-change actions (all required)**: ① Add/edit `.md` in Coze-side `knowledge/`; ② if a new file, update the `_CATEGORY_KNOWLEDGE` routing table in `adapters/coze/src/kb/__init__.py`; ③ rerun `adapters/coze/scripts/build_knowledge_index.py` to rebuild `knowledge_index.json` (chapter-level routing index; a new index not deployed = new chapters never match); ④ re-upload the Coze package and **rebuild the image / restart the long-running process** — `_knowledge_cache` and `_index_cache` are in-process memory caches; overwriting files without restart = the old cache keeps serving and new files are invisible to production.
   - **Fatal error pattern (2026-09-15, observed)**: editing only the local `knowledge/` → neither Coze-side index nor routing table has the new file → zero production hit on the new content (P0 "live but ineffective"). Iron rule: **knowledge change = edit Coze-side copy + rebuild index + rebuild image**; local `knowledge/` is for fallback only and carries no new content.

## Answer Workflow (steps 0–6)

> **Core principle:** payload stays in-memory pipeline throughout (`--payload-inline` or stdin); **prohibit** Write/Bash temporary JSON files.
> **Detailed flow:** full description, I/O, boundary conditions per step → `references/steps.md`

| Step | Responsibility | Forward (all questions) |
|---|---|---|
| **1 Difficulty gate** | 🔴 run `python scripts/route.py "<q>"` **once** (code-based, instant, no KB read) → label. **vague** → Local Clarify Loop (`clarify_loop.py`) then re-gate on the enriched question and route per the table below (data-intel → `orchestrate.py` preferred, else `--ship`); **simple/middle/complex** → forward via `scripts/orchestrate.py` (data-intel preferred) or `refine_answer.py --ship` (fallback), with `query_meta.difficulty` set | → 2 |
| **2 Receive & route** | inspect the structured result — 3 branches below | → 3a / 3b / 3c |
| **3a Answer** | `need_tool` empty → ship Coze `final_answer` as-is. 🔴 If the question merely *touches* a sibling skill (weak hit / definition / methodology) **code has already appended a one-line install / invoke suggestion at the very end** (`route_tool.suggest_footer`) — pipe it verbatim; never call the skill yourself | → 6 |
| **3b Skill card** 🔴 | `need_tool` non-empty ⇒ **MUST** run `scripts/handle_need_tool.py` (no shortcut). The runner is **tier-aware** (see "A/B Tier Gate" below): `ok` → stitch skill result into Coze `draft_answer` (the skeleton) → deliver (never re-send Coze); `need_params` → ask user for missing params (never fabricate) → re-run; `install_required` → say what the skill does, give the install command and **suggest** installing (`install_mode="suggest"` by default: 🔴 never install automatically — installing writes into the local skills directory and may trigger a security prompt, so the user may run the command themselves) → explicit authorisation: re-run with `install_consent="approved"` (→ `install_mode="authorized"`, then install and re-run) / decline: re-run with `install_consent="declined"`; `unpublished_a` → Tier-A skill not yet publicly released → no install address, deliver the Coze draft + local note; `unreleased_b` → Tier-B skill, not publicly released → deliver the Coze draft + local note; `local_fallback` → deliver the Coze draft labelled "data not retrieved" | → 6 |
| **3c Fallback** | Coze timeout / network / HTTP error (`FALLBACK` marker) → answer from local `knowledge/` (A1/A2 routing) + warning | → 6 |
| **6 Final Answer** | Return result directly | — |
### 🔴 Outbound Authorization Gate

Runs automatically inside `refine_answer.py` before each outbound HTTP call (agent never triggers it manually). Rules: ① endpoint in `config.json` → `auto_approve_endpoints` → allow; ② authorized earlier this session → allow; ③ otherwise → show the confirmation prompt below (first call only; never expose step / workflow / internal terminology). **🔴 agent NEVER edits `config.json`** (incl. `auto_approve_endpoints`) — whitelist is author-preset (`ct-advisor.coze.site/run` already in it, so it never prompts); if the user wants another endpoint whitelisted across sessions, the USER adds it explicitly (agent may guide, not write). Unauthorized endpoint → `[AUTH-BLOCK]` → user-confirm → on decline, local-fallback answer with "cloud analysis was not used this time" note (never block):

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
- **🔴 Answer contract (cloud-side, 2026-09-10):** the *shape* of the shipped answer is governed by the Coze nodes `full_analysis` / `review`, which now carry a highest-priority **Answer contract** — **C1 answer-first** (first paragraph must answer the literal question; decision questions must state one explicit recommendation) · **C2 scope lock** (no sections on topics `original_question` never asked; adjacent topics collapse into a single trailing one-line offer) · **C3 difficulty = expected magnitude + hard backstop** (simple ~100 / middle 300–500 / complex 500–800 Chinese characters; backstop 200 / 700 / 1000, `###` banned), with **element completeness outranking length** so the budget bounds redundancy only · **C4 commit to one recommendation**. Because you are a **pipe**, **never compensate** for a long answer by trimming, reordering or re-writing it yourself — if the shipped answer still sprawls — or, conversely, reads too thin — the fix belongs in `adapters/coze/config/*.json` **plus a Coze redeploy** (see `coze_modification_guide.md`), never in the agent prompt.
- **💡 Skill-advice tail (2026-09-10, user request):** whenever the stitch layer appends a sibling skill's result (`## Supplementary data (Source: ct-xxx)`), **code also appends one line** telling the user that what they see is a readable summary and that to **verify it or get the full original output they should run that skill directly**. Emitted by `_merge_answer()` in `refine_answer.py` (zh/en follows the question language); 🔴 do **NOT** add it by hand — it is part of the stitched answer, so pipe it verbatim like the rest.
- **🔴 Sibling-skill invocation bar (HARD GATE, 2026-09-10 — user request):** keyword false positives used to hijack the answer (a pure methodology question could be routed to `ct-registry` and get a "please supply the drug name" demand). Two rules now gate every sibling-skill call, enforced **identically** in the local router (`scripts/route_tool.py`) and the cloud router (`adapters/coze/src/graphs/nodes/tool_router_node.py`):
  - **① Answer-first, suggest-last.** Whenever a sibling skill is *not* auto-invoked, this skill answers from its **own capability first** and only then appends — **at the very end** — a one-line suggestion that the sibling skill can be installed / invoked (`💡 *Supplementary: this question also relates to the following sibling skills…*`, emitted by `route_tool.suggest_footer`, language follows the question). It **never blocks** the answer to demand params or installation. This also now applies to the `install_required` path (answer + install suggestion at the tail, not a blocking delegate card). 🔴 **2026-09-10 patch — the suggestion list is itself gated:** when the consultation guard fires (definition / methodology / document question, no explicit retrieval action) **only strong hits are suggested**; bare generic words no longer overflow into the tail (a pure "ITT vs mITT" definition question must carry **no** suggestion). A named data source / statistic still earns its suggestion — that is a genuine hit. Mirrored as `_suggest_tools(..., strong_only=…)` in the cloud router.
  - **② Only uniquely-directed triggers auto-invoke.** Auto-invocation requires a **strong** trigger: ① a named data source (`NCT…` / `ClinicalTrials.gov` / `FAERS` / `PubMed`…), ② a named statistic or high-specificity method (`PRR` / `ROR` / `EBGM` / dechallenge-rechallenge / `case report` / `meta-analysis`…), or ③ an explicit "**retrieval verb + clear object**" phrasing (`Retrieve the registered trials for…`). Generic words — `signal` / `literature` / `trial` / `safety` / `design` / bare `registry` — are **weak**: they never auto-invoke, they only earn the trailing suggestion. A **consultation guard** (definition `DEF` / methodology `METHOD` / document `DOC`, **Chinese and English**) additionally suppresses triggering unless the question also carries an explicit retrieval action (`RETRIEVAL`); this is what previously let "…how do I keep the overall type I error rate at 0.05?" be misread as a registry query. On a guard hit the **suggestion list is reduced to strong hits only** (2026-09-10 patch) — bare generic words are dropped there too, so a definition question no longer trails a registry hint.
- **🔴 Code orchestrator for data-intel (2026-08-15):** for sample-size / registry / safety / literature questions you SHOULD call `scripts/orchestrate.py` (NOT `--ship`) — it is the **code-only orchestrator**: at entry it predicts the needed ct skill (high-confidence prefetch via `scripts/route_tool.py`), fires Coze **and** the predicted skill **in parallel** (threads), merges both results, and **decides in code** whether the answer is complete. It emits the same `<<<CT_ANSWER_START>>>`…`<<<CT_ANSWER_END>>>` wrapped answer when sufficient (pipe it verbatim), or a `<<<CT_TOOL_DELEGATE>>>` block when a ct skill still must run. In the delegate case **you (local LLM) are NOT the orchestrator** — you only: ① confirm / ask the user for the missing params listed in the block (never fabricate), ② hand the card to `python scripts/refine_answer.py --card-inline '<JSON>'` so **code** executes the skill + stitches + wraps. You do **NOT** judge sufficiency and do **NOT** rewrite Coze text.
- **Local-retrieval discipline (HARD GATE):** local DB retrieval capped at **ONE per turn** for the 3c fallback — never chain multi-step local reads.
- **need_tool is Coze-judged:** the agent NEVER decides by itself that a sibling skill is needed — it only executes the card Coze returns (mechanical lookup in `scripts/tool_mapping.json`).

### Step 0.5 · Local Clarify Loop (pure-local, no outbound)

Entered **only** when `route.py` returns `vague` (the gate above). Run `python scripts/clarify_loop.py` (same in-memory pipeline as `refine_answer.py`, the **heuristic menu**) **before** forwarding: 1–3 high-value questions per round, hard-capped at **3 rounds** (hitting the cap still proceeds, never loops). On `decidable`/`forced_decide`, **re-run `route.py` on the enriched question** and route per the table below (data-intel → `orchestrate.py` preferred; methodology → `--ship`), passing `query_meta.difficulty="vague"` for the original classification.

**Call style (zero temp files):** stdin pipe `echo '{…}' | python refine_answer.py --ship` (Chinese punctuation safe) — **Forbidden**: Write/Bash temp JSON files, `/tmp` paths. PowerShell: here-string `@'…'@`. Full rules + encoding caveat → `references/steps.md` "Call-style summary".
**🔴 Payload keeps `query_meta`** (difficulty/category/accuracy may be empty — server-side routing + Feishu collection tolerate blanks; script defaults `difficulty` to `complex`). Example: `echo '{"query_meta":"{\"difficulty\":\"complex\",\"category\":\"\",\"accuracy\":\"\"}","original_question":"…"}' | python refine_answer.py --ship`
**🩺 Coze failure diagnosis (user-friendly):** on fallback (stderr `FALLBACK` / `ProxyError` / `Timeout`, or the stdout ask "…may I run automatic diagnostics?"), **ask the user first** — "The Coze cloud service is temporarily unavailable. May I run automatic diagnostics?" If allowed → run `python scripts/check_coze.py` once, fix the root cause (stale system proxy / offline / token), retry; if declined → deliver the local answer **with a prominent warning**: "Could not connect to Coze; this answer is unrefined — use with caution." v0.9.60+ auto-retries bypassing the system proxy on `ProxyError`/`ConnectionError`.

---

### Session continuity
Once `@skill:ct-advisor` is invoked, its instructions + `knowledge/` stay in thread — **do NOT re-invoke the skill on follow-ups**; re-run gate 0 each turn. Off-topic / meta requests (e.g. "modify this skill") drop the framing and are handled as normal assistant work (no methodology workflow, no Coze refine).

**Type-B follow-ups (implicit carry-over, no anaphora)** — since v0.9.70 (rewritten to **mode B** on 2026-08-25, aligned with ct-base `references/continuity.md` §2), `refine_answer.py --ship` auto-attaches bounded conversation history before forwarding: `scripts/context_stitch.py` **always** exports the structured `conversation_history` (via `pack_history_for_coze`) and forwards it to Coze — the remote LLM judges relevance/inheritance. Local code does **NOT** detect follow-ups or rewrite the question (the old `is_followup()` regex + self-contained stitch was hard-deprecated: fragile, missed long-form design-evolution follow-ups). `config/context_cache.json` is a **write-through mirror only** (TTL 2h / ≤10 rounds + 24h hard cap), never the sole continuity source. Pure local code — no LLM (judgment delegated to Coze), no new outbound contract.
### Personalization (tone writing + local user memory) — ⚠️ DEFERRED (not enabled)

Tone writing (`tone_profile`) and local user memory (`memory_context`) are **temporarily disabled**: the deployed Coze workflow (v1.5 contract) does not implement these fields, so local injection is silently ignored. The scripts (`tone_matcher.py` / `memory_manager.py`) and the `--tone` / `--memory` CLI flags remain in place for future use but **MUST NOT be invoked**. Re-enable only after the Coze workflow ships the v1.6 contract fields (2026-08-12 decision).

### Performance discipline (latency guards — keep these, they are why this skill is fast)
- **🔴 HARD GATE: minimal local work before `--forward`** — between receiving the question and firing Coze, the **only** permitted local work is **one** deterministic, LLM-free difficulty call: `python scripts/route.py "<q>"` (stdlib-only, instant, ~tens of ms). It performs **NO `knowledge/` read, NO `search_refs.py`, NO multi-round local retrieval** — those historically cost 10–20 tool round-trips (≈3–4 min) and are the #1 latency failure mode. For `vague`, the clarify loop (`clarify_loop.py`) is a bounded pure-local menu (≤3 rounds) that still precedes Coze. The 3c fallback (local answer) happens **only after** Coze fails.
- **Search backoff:** on `search_refs.py` 0 hits → do NOT chain more local reads; hand the original question straight to Coze remote. **Long sessions:** prune stale context before step 2 (keep recent turns + final conclusion; never drop info still needed).
- **🔧 Latency observability (F, 2026-08-23):** `refine_answer.py --latency-report --round-id <qid>` tallies tool round-trips per question (counter in `.runtime/`, gitignored, pure-local, no network call); `--latency-threshold` (default 10) emits a `[WARN]` when a round exceeds it — the pre-fire delay regression signal. The invariant checklist lives in `references/steps.md` "Latency guard checklist (F)". → `references/ADVANCED.md` for the full latency discipline.

## Code Orchestrator (`orchestrate.py`, 2026-08-15)

**Code-only orchestrator + LLM-delegated ct-skill execution.** `scripts/orchestrate.py` is the recommended entry for data-intel questions (sample-size / registry / safety / literature). It is the **fully-automatic orchestrator** — the local LLM is **NOT** the orchestrator:

1. **Entry prefetch (code, no LLM)** — calls `scripts/route_tool.py` to predict the needed ct skill at **high confidence only**. Since 2026-09-10 that means **strong, uniquely-directed triggers** only (named data source / named statistic / "retrieval verb + clear object"); definition / methodology / document questions and generic words (`signal` / `literature` / `trial` / `safety` / `design`) are **not** predicted — they instead yield `suggest_tools`, which the stitch layer renders as a **trailing install / invoke suggestion after the answer** (and since the 2026-09-10 patch a guard-hit question yields **strong hits only** there, so bare generic words produce no trailing suggestion at all). Low-confidence / hidden needs are left to Coze's `need_tool` (fallback).
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

### 🔴 A/B Tier Gate (sibling-skill invocation)

> Full tier-gate table, skill-card execution protocol, and sibling-skill boundaries → `references/tier_gate.md`. Summary: sibling calls pass a tier gate (A = non-confidential / B = confidential); Tier A published skills are **suggested** (not auto-installed); Tier A unpublished and Tier B are non-installable. `need_tool` cards are always executed in code — you only pipe the result.

## China Regulatory Depth (C-layer)

CTA/IND 60-day tacit approval, Type A/B/C communication meetings, registration ≠ tacit approval — see `knowledge/ref-regulatory-versions.md` + `knowledge/reference-index.md`; verify any version / status / deadline in real time against the official original.

## Quality Gate & Stop Rules

Pre-delivery checks and stop conditions live in `knowledge/system_prompt.md` "Quality gate & stop rules". Core red line: **never expose in user-visible content personal info, subject info, unpublished project data, private path or access credential.**

**Presentation rules (user-mandated, hard)** — deliver only the answer (refined stdout) + essential cited basis. **Never emit any workflow / process narration to the user** — this explicitly covers: step 0–6 labels ("Step 2", "Gate 0", "Step 6"), difficulty tags (`simple` / `middle` / `complex` / `vague`), forward / need_tool / fallback mechanics, routing / triage narration, progress / status broadcasts, self-process recaps, memory / CHANGELOG housekeeping notes, follow-up CTAs, redundant closing summaries, internal-pipeline wording ("refined by Coze", "assembling payload"), and disclosure of internal knowledge sources. Internal reasoning may still use these labels freely — they just must **never** appear in user-visible text. See ct-base §6.2 / §6.3.

**Graphical explanation policy (SUPERSEDED 2026-09-16):** disabled. The Pipe-Only Hard Contract (line 53) forbids any post-delimiter formatting. `references/visual-appendix.md` kept as technical reserve only.

**🔔 Forward-mode user notice (the ONLY allowed process message)** — emit **exactly one** brief user-facing notice **immediately before firing the Coze call** (`refine_answer.py --ship` / `orchestrate.py`), i.e. **AFTER** `route.py` has returned (the difficulty gate is local, sub-second — no notice needed for it) and any clarify loop has finished. The notice covers the wait for the cloud response, not the local gate. Example:
> Calling the cloud analysis engine, please wait…

Do **NOT** repeat it, do **NOT** add any other process chatter.

### Bug Report (§20.3 · ct-base)

On defect detection or explicit user request, `adapters/bug_report.py` offers a sanitized 11-key report to `https://ct-bugreport.coze.site/run`. Two-stage confirmation mandatory. → `references/ADVANCED.md` for the full protocol.

## Changelog — full history (0.8.0 → 0.9.30+) → **[CHANGELOG.md](CHANGELOG.md)**
