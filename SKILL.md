---
slug: ct-advisor
name: ct-advisor
displayName: Clinical Trial Chief Advisor / 临床试验总顾问
cn_name: 临床试验总顾问
version: 1.3.55
invocable: true
required_commands: [python]
summary: "面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问，覆盖合规应答 / 项目运营 / 交付物撰写 / 方案设计 / 统计分析 / 注册申报 / 安全性 / 数据管理 / 真实世界研究等各方面。"
description: "The single entry point for the ct-series across the full clinical-development lifecycle — a cloud-assisted clinical trial advisor. Coverage: regulatory-response / trial-operations / deliverable-drafting / study-design / statistics / submission / safety / data-management / real-world-evidence and more. / 面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问，覆盖合规应答 / 项目运营 / 交付物撰写 / 方案设计 / 统计分析 / 注册申报 / 安全性 / 数据管理 / 真实世界研究等各方面。"
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
trigger_scope: "触发词覆盖临床试验方法学/法规/设计/合规应答/项目运营/交付物撰写/QC/安全性/数据/注册/情报类问题；尽量扩大适用范围，仅对明确非医药/生命科学语境的问题（如消费电子、金融、快消、地产等）给出建设性转介建议，绝不空拒；不含文件系统写入与系统级 API 调用。"
metadata:
  openclaw: { emoji: "🛠️", icon: "assets/icon.svg" }
  authors: ["medstatstar", "phoe-zip"]
  family: ct-series
  homepage: "https://github.com/medstatstar/ct-advisor"
permissions:
  scope: "user-space-only"
  network: "controlled-coze-opt-in"
  network_note: "All questions forwarded to Coze (single call, internal scripts/orchestrate.py); local side does no KB lookup / web search. Attachments (<5 MB original bytes; >5 MB converted to Markdown locally) uploaded as doc_context; Coze KB is the single source of truth."
  filesystem: "Read-only to own files; no confidential data leaves — Coze payloads sanitized, query_origin is a stable per-machine sha256 hash (non-PII)."
adapted_from: "https://github.com/A-xin946/clinical-trial-advisor"
dependencies:
  - {slug: ct-registry,   tier: A}
  - {slug: ct-safety,     tier: A}
  - {slug: ct-literature, tier: A}
  - {slug: ct-samplesize, tier: A}
tier: A
---
## Data Egress Guardrail (CT family standard · F33)

This skill may call external endpoints (Coze services, shared third-party search endpoints, public APIs or LLMs). **Internal confidential data must not leave the local domain.** Mandatory rules:

- **Never outbound**: patient-level records, unpublished protocols / CSRs / internal documents, personal identifiers or sponsor-confidential content — as query terms, attachments or prompt payload.
- **Allowed minimum**: public search terms and non-content metadata only (machine hash, skill version, entry point, language, request id). Results from public registries (ct.gov / CDE / FAERS / OpenAlex / PubMed, etc.) are processed locally.
- **Local first**: computation, de-identification, aggregation and reporting stay on this machine; confirm the payload carries no confidential field before any cloud call.
- **Visible disclosure**: workbench search forms must state the outbound endpoint and this boundary in visible text, not only in a hover tooltip.
- **Fail loud**: stop and tell the user if any rule cannot be guaranteed; never degrade silently.

Machine-checked by `ct-base/scripts/spec_lint.py` rule **F33**.

# Clinical Trial Chief Advisor

## Language

- **English guide** → [README.md](https://github.com/medstatstar/ct-advisor/blob/main/README.md) · **中文指南** → [README_zh-CN.md](https://github.com/medstatstar/ct-advisor/blob/main/README_zh-CN.md)
- **This SKILL.md body is English-only, agent-facing.** Bilingual walkthroughs live in the two READMEs; the answer language follows the user's question language.

## 🔴 HIGHEST PRIORITY: scripts/entry.py is the ONLY permitted action

> **The local LLM is FORBIDDEN from making any decisions in this skill. Its ONE AND ONLY allowed action is:** Run the single entry point with the user's question (and optional attachment). Pipe the stdout to the user verbatim. CLI details live in `references/ADVANCED.md` — do not type commands from here.
>
> Since **v1.3.21** the stdout is **plain text followed by a trailing integrity line** and one ASCII pointer to the answer file — no decoding, no transcription, no second command:
>
> ``` {the answer text, as many lines as it needs} <<<CT_ANSWER_END>>> checksum: {sha256[:16]} answer_file: C:/Users/<user>/.workbuddy/skills/ct-advisor/_answers/{checksum}.md ```
>
> **One entry point, one output shape, one protocol, one place where the protocol is produced.** No base64 anywhere in the pipeline; `entry.py` writes UTF-8 bytes straight to `stdout.buffer` and the marker/checksum pair is produced in exactly one function. Historical rationale → `references/ADVANCED.md` §10.1.

**HARD GATE — the following are absolutely PROHIBITED for the local LLM:**
- ❌ **NEVER** read, search, or reference any local knowledge base (the `knowledge/` directory has been removed)
- ❌ **NEVER** perform any local network retrieval or web search (`references/search-sites.md` has been removed)
- ❌ **NEVER** answer the question from the LLM's own knowledge — all domain expertise lives on the Coze side
- ❌ **NEVER** bypass `entry.py` by calling `route.py`, `refine_answer.py`, `orchestrate.py`, or any other script directly
- ❌ **NEVER** rewrite, rephrase, reorder, summarize, or "polish" the answer text that precedes `<<<CT_ANSWER_END>>>`
- ❌ **NEVER** append a summary, lead-in, closing remark, or "key takeaways" before or after the answer
- ❌ **NEVER** strip, alter, or re-generate the `<<<CT_ANSWER_END>>>` marker or the `checksum:` line that follows it
- ❌ **NEVER** translate or align language (the code already handles that)
- ❌ **NEVER** inject process narration ("Step 2", "Coze returned", "assembling payload")
- ❌ **NEVER** decide whether to forward to Coze — ALL questions are forwarded (entry.py handles routing internally)
- ✅ **EXCEPTION**: when stdout carries `<<<CT_TOOL_MENU>>>`, presenting that code-generated menu to the user and re-running `entry.py --resume <token> --selected <user's literal picks>` is permitted — the agent still makes no judgement; it relays the user's choice verbatim. See "Skill-call confirmation menu" above.
- ❌ **NEVER** wrap, encode, base64-ify, or otherwise re-transport the answer on your own — the pipeline already emits the final form
- ❌ **NEVER** present the `answer_file:` line as part of the answer (it is a pointer, not content)
- ❌ **NEVER** discard stderr with `2>$null` / `2>/dev/null` — stderr carries the answer-cache-hit / resident-service / `[ct-advisor][ERR]` signals that tell you whether a Coze call actually happened

**Why this rule exists:** The local LLM's "helpful" instincts (answering from its own knowledge, pre-reading files, post-formatting answers) have repeatedly violated the pipeline contract, destroyed Coze-delivered content formatting, altered numeric precision, injected unsolicited content, and bypassed the cloud analysis entirely. This rule eliminates ALL local LLM decision space.

### 🔴 When the local LLM may act at all

Normal path: `scripts/entry.py` runs, the answer is delivered verbatim, and the local LLM analyzes nothing. It may intervene **only** when code-level parsing actually fails — a missing `<<<CT_ANSWER_END>>>` marker, a checksum mismatch, a garbled stdout body, or an `[ct-advisor][ERR]` signal on stderr. Parse-shape failures follow the Integrity check table above; `[ERR]` alone triggers self-healing below. Even then the action is mechanical only: re-capture the **same** command, read the printed `answer_file:` path, or relay the machine signal. **Never** decode, repair, reconstruct, summarise or author answer content, and never fall back to the host model's own knowledge. Parse-failure byte-level rules: `ADVANCED.md` §9.

> **`entry.py` has exactly two non-forwarding modes, both still zero-LLM and still the one permitted action:** `--stitch` (consume existing skill outputs; no Coze call) and `--resume` (second phase of the user-confirmation skill menu — see "Skill-call confirmation menu" below). Everything else forwards through the normal path.

## How to use this skill

Run the single entry point with the user's question. Optionally attach a file (e.g. a CSR or protocol snippet). The stdout is the final answer — deliver it verbatim.

CLI invocation details, examples, and flag notes → `references/ADVANCED.md`.

### Skill-call confirmation menu (`<<<CT_TOOL_MENU>>>` → `--resume`)

For questions that need sibling A-tier skills, the skill **never auto-executes** the skill call. After the first `entry.py --q`, if stdout contains a `<<<CT_TOOL_MENU>>>…<<<CT_TOOL_MENU_END>>>` block, do this — and nothing else:

1. **Show the text BEFORE the block verbatim** (for a single skill this is already the preliminary answer; for multi-skill it is a short "please choose" lead-in). Both modes append a "quick reference / use the full skill or web portal for formal output" note — show that verbatim as part of the menu text too. Do not show the block itself to the user.
2. **Parse the JSON inside the block**. It has `token`, `mode` (`single`/`multi`), `question`, and `options` (each option has `skill`, `label`, `desc`).
3. **Ask the user once with a multi-select menu** (AskUserQuestion, `multiSelect=true`):
   - use each option's `label` as a choice; include an explicit **"都不调用 / 不需要"** choice (the user may pick it to decline);
   - for `mode=single` phrase it as "是否调用这一个技能补充数据"; for `mode=multi` as "勾选需要执行的技能".
4. **Map the user's picked labels back to skill ids**: a label starts with `ct-<slug>｜`; take that prefix as the skill id. If the user picked "都不调用", use an empty list.
5. **Run the second command** (still `entry.py`, still the only permitted action): `python scripts/entry.py --resume <token> --selected '["ct-registry","ct-safety"]'` (use `[]` if the user declined). Pipe this command's stdout verbatim as the final answer.

🔴 **This is NOT local-LLM decision-making.** The menu options are code-generated from the cloud's whitelisted judgement; the agent merely presents them and relays the user's literal choice as `--selected`. **Two judgement sources exist — local `route_tool` prediction and remote Coze `plan`/`need_tools`; on conflict the Coze decision always wins (2026-11-20 ruling). Local prediction is only a convenience/fallback (param prefill + backup when Coze returns prose only); it must never override or mix into Coze's tool-call decision.** How a skill runs is a separate concern decided by local install state (`_runs_local`), not by which source proposed it. No tool runs until the user confirms. `--resume` reads a one-time, TTL-bounded local state file (token is a 16-hex id, single use), re-validates that every selected skill was in the offered set (fail-closed), then runs the plan + second-Coze assembly. Second-Coze failure is a hard failure — no local fallback. Emergency rollback: set `CT_ADVISOR_CONFIRM=0` to restore pre-confirmation behavior (v1.75 auto-execute).

### What entry.py does internally (all code, zero LLM)

Five code-only steps: attachment gate → vague gate → Coze forward (async-first) → delegate stitch → plain-text output with the ≥180 s slow-flow guard. Full canonical pipeline → `references/ADVANCED.md` §10.2.

> **LLM-forbidden zone**: every step above is executed by code. The local LLM never picks the channel, never judges difficulty, never decides forwarding.

## Session, Context, Cache & Routing

Multi-turn history, 30-min answer cache, 10-min near-duplicate dedup and domain routing are all code-side; contracts → `references/ADVANCED.md` §8 and §10.3.

## Requirements

Python stdlib-only runtime; sibling `ct-*` skills are client-callable via code-generated handoff cards (never auto-run). Full requirements, async-first Coze transport and endpoint details → `references/ADVANCED.md` §1 and §10.4.

## Attachment handling (docx / xlsx / pptx · doc / xls / ppt · pdf)

**Single gate = 5 MB, decided FIRST inside `entry.py`.** `< 5 MB` uploads the original file to Coze through `doc_context` (no local conversion); `> 5 MB` converts locally to Markdown and uploads the `.md` through the same channel with a user-visible notice. Full table and governance pointers → `references/ADVANCED.md` §10.5.

**Deliverable boundary:** **text only** — never generate / export / hand back a modified document file. When asked for the revised file, state on the **first line** that this feature is unavailable and only written suggestions are provided, then give the suggestions as text.

### 🔴 Integrity check (HARD GATE · simplified in v1.3.19, final in v1.3.21)

Because the answer arrives as **plain text**, the whole check collapsed into one structural question: **is the trailing `<<<CT_ANSWER_END>>>` marker there?**

| # | Observation | Meaning | Action |
|---|---|---|---|
| 1 | Marker + `checksum:` present, body non-empty | Capture complete | Deliver the body verbatim (`answer_file:` line included, it is not part of the answer). `checksum:` re-verification is optional here — the marker's presence already proves the capture was not cut. |
| 2 | Marker absent, or `checksum:` line missing | The tool channel truncated the capture | Re-capture the **same** command with Bash / Git Bash. **Do NOT re-run Coze.** |
| 3 | Marker present but checksum mismatch (verification code in `ADVANCED.md` §9) | Real corruption, not truncation | Do NOT deliver. Report expected vs actual and stop — never loop re-runs. |
| 4 | Body looks garbled but marker + checksum are intact | Display-layer code page, data intact | **Read the `answer_file:` path exactly as printed** (absolute ASCII — verified to survive the capture that destroyed the body) and deliver everything before `<<<CT_ANSWER_END>>>`. No re-run. **If that line is missing** (both candidate dirs unwritable), stop and report — never decode or guess the text. |

Re-running without capture evidence is a protocol violation: in the 2026-10-15/16 incidents it made one question fire 2–3 times, dragging a single Q&A to minutes.

## Quality Gate & Stop Rules

**Presentation rules (user-mandated, hard)** — deliver only the plain-text answer printed by `scripts/entry.py` (everything above the trailing `<<<CT_ANSWER_END>>>` marker). **Never emit any workflow / process narration to the user.**

**🔔 Forward-mode user notice (the ONLY allowed process message)** — entry.py emits a brief notice to stderr before firing the Coze call. The local LLM should not add any additional process chatter.

### Slow-response notice (v1.3.48 · code-only, part of the answer)

`entry.py` starts a monotonic clock at process load and, at its single exit, compares the full-flow wall-clock against **180 s (3 min)** (override for testing only: env `CT_ADVISOR_SLOW_SEC`). When the threshold is reached it prepends, in code, a bilingual notice — Chinese when the question (or, absent a question, the answer body) contains CJK, English otherwise:

> `[Slow-response notice]` — code-generated bilingual (CJK-aware, ≥180 s, idempotent). Deliver verbatim as the answer's first lines. Verbatim template + semantics → `references/ADVANCED.md` "Slow-response notice" section.

This notice is **answer content**, produced inside `_emit_plain` before the checksum/answer-file are computed. The local LLM must **deliver it verbatim as the first lines of the answer**, exactly like any other answer text: never strip it, never explain it away, never replace it with its own timing estimate, and never add a second copy. It is idempotent (already-prefixed answers are not prefixed again), so cached/delegated outputs cannot duplicate it. Measured scope is the skill's own process (attachment gate → Coze poll → delegate stitch → callback → exit); reasoning time spent by the host model **before** invoking or **after** receiving `entry.py` is outside this process and cannot be measured by the skill.

## Outbound Authorization Gate

Runs automatically inside `entry.py` → `scripts/orchestrate.py` before each outbound HTTP call (agent never triggers it manually). Endpoint `https://ct-advisor.coze.site/run` is in `auto_approve_endpoints` by default, so it never prompts. If the user wants another endpoint whitelisted across sessions, the USER adds it explicitly to `config.json` — **the agent MUST NOT edit `config.json`**.

## Bug Report (§20.3 · ct-base)

On defect detection or explicit user request, `adapters/bug_report.py` offers a sanitized 11-key report to `https://ct-bugreport.coze.site/run`. Two-stage confirmation mandatory.

## External Tool References

Authoritative external assets (teal, Docling, Pinnacle 21 CDISC rules, ICH M12 DDI thresholds) and their Coze KB mirrors → `references/ADVANCED.md` §10.6.

## Error Self-Heal Protocol (stderr machine signals · 2026-10-15)

**Scope — failure paths ONLY.** On a successful run (`scripts/entry.py` exits 0 and prints the answer, and **no `[ct-advisor][ERR]` line on stderr**), the agent delivers the answer and stops. **The agent MUST NOT enter self-healing when no error was reported** — no proactive health checks, no proactive dependency installs, no proactive config/env edits, no speculative retries. The `[ct-advisor][ERR]` signal is the **only** trigger.

> **Where signals live (2026-10-16)**: the resident service (`scripts/serve.py`) is spawned with `stderr=DEVNULL`, so anything written inside the service process — including an `[ct-advisor][ERR]` emitted on the service path — is redirected by the service itself to **`config/serve.log`** (auto-truncated at 1 MB). If `entry.py` prints no `<<<CT_ANSWER_END>>>` marker (empty or destroyed stdout) while stderr carries no `[ERR]` line, read the tail of `config/serve.log` before concluding anything.

**Signal format (single line, stderr):**

```
[ct-advisor][ERR] code=<CODE> auto_fixable=<true|false> retry_safe=<true|false> requires_network=<true|false> [detail="…"] [fix_cmd="…"]
```

**Code → agent action:**

| code | auto_fixable | retry_safe | requires_network | Agent action |
|---|---|---|---|---|
| `CONN_FAIL_PROXY` | false | true | true | Deliver the answer-block text verbatim (it carries numbered recovery steps). Offer **one** retry only after the user confirms the proxy/network is fixed. Never edit env or config yourself. |
| `CONN_FAIL_DIRECT` | false | true | true | Same as above. |
| `TIMEOUT` | false | **false** | true | Deliver verbatim. **Never auto-retry** — Coze likely already received the request; a blind retry duplicates it. |
| `AUTH_401` | false | false | false | Deliver verbatim; explain the token must be renewed by the skill maintainer. Do not edit any skill file. |
| `COZE_HTTP_ERROR` | false | false | true | Deliver verbatim; a user-initiated retry after 1–2 minutes is acceptable. |
| `ORCH_FAIL` | false | false | false | Deliver verbatim; ask the user to report the `detail` field to the skill maintainer. |

**Hard rules (violating any of these is a defect):**

1. **No signal → no action.** Absence of `[ct-advisor][ERR]` means success; the agent must not probe, install, edit, or retry anything.
2. `fix_cmd` may be executed **only** when `auto_fixable=true` (after the 2026-10-15 stdlib-urllib transport change, **no code currently qualifies** — the dependency-missing class was eliminated) **and** the user has explicitly confirmed. Execute it **verbatim**; never improvise commands; never edit skill files or `config.json` (same red line as the Outbound Authorization Gate).
3. At most **one** retry per user turn, only after a successful fix, and only when `retry_safe=true`.
4. `requires_network=true` means the fix itself needs working outbound access — resolve network-class errors first.
5. Self-healing covers **transport repair only**. It never licenses local answer generation — the coze-only red line stands.
6. If stderr carries an `[ERR]` line but stdout has no answer block, treat the turn as failed: relay the signal's meaning plus any human-readable guidance. **Never fabricate an answer.**
7. Signals are emitted from failure paths only (`adapters/errsignal.py::emit_err_signal`). If an `[ERR]` line appears on a run that returned a valid answer, treat it as a skill defect and report it.

---

## Extended reference

Full technical material (moved out 2026-11-20, wording unchanged) lives in [`references/ADVANCED.md`](references/ADVANCED.md): return path / output contract, integrity verification code, session-routing contracts, requirements, attachment handling, external tools, error-code note, performance notes, capability domains, consultation-vs-execution, keyword translation gate. The HIGHEST PRIORITY action, Data Egress Guardrail (F33), HARD GATE integrity table, Quality Gate / Stop Rules, Outbound Authorization Gate and Bug Report stay in this file.

Agents: read `HIGHEST PRIORITY` and the HARD GATE list before any action; the operational sections above are reference material and never override the single-entry-point rule.
