---
slug: ct-advisor
name: ct-advisor
displayName: Clinical Trial Chief Advisor / 临床试验总顾问
cn_name: 临床试验总顾问
version: 1.3.46
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
> **One entry point, one output shape, one protocol, one place where the protocol is produced.** Since v1.3.21 there is **no base64 anywhere in the pipeline** — not between code modules, not on the wire, not in the browser. The reason is historical: v1.3.9 introduced base64 to survive cp936 console mojibake, but that forced the LLM to hand-copy a ~2.6k-char random string into a second command (2026-10-16 incident: `5Lzd` typed for `5L+d`, a "checksum failure" that was pure transcription damage, then three real Coze calls for one question). The wrapper that fixed it left two parallel protocols, a 4× payload inflation, and — once the browser started taking the API directly — a decoder in *each* client. v1.3.21 removes the need instead of managing it: **encoding is no longer a decision made at the exit**. `entry.py` writes UTF-8 bytes straight to `stdout.buffer` (constant, no code-page inspection, no flags), the marker/checksum pair is produced in exactly one function, and the same bytes are also on disk. `scripts/ask.py` survives only as a zero-logic forwarding shim for stale callers.

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
- ❌ **NEVER** wrap, encode, base64-ify, or otherwise re-transport the answer on your own — the pipeline already emits the final form
- ❌ **NEVER** present the `answer_file:` line as part of the answer (it is a pointer, not content)
- ❌ **NEVER** discard stderr with `2>$null` / `2>/dev/null` — stderr carries the answer-cache-hit / resident-service / `[ct-advisor][ERR]` signals that tell you whether a Coze call actually happened

**Why this rule exists:** The local LLM's "helpful" instincts (answering from its own knowledge, pre-reading files, post-formatting answers) have repeatedly violated the pipeline contract, destroyed Coze-delivered content formatting, altered numeric precision, injected unsolicited content, and bypassed the cloud analysis entirely. This rule eliminates ALL local LLM decision space.

### 🔴 When the local LLM may act at all

Normal path: `scripts/entry.py` runs, the answer is delivered verbatim, and the local LLM analyzes nothing. It may intervene **only** when code-level parsing actually fails — a missing `<<<CT_ANSWER_END>>>` marker, a checksum mismatch, a garbled stdout body, or an `[ct-advisor][ERR]` signal on stderr. Parse-shape failures follow the Integrity check table above; `[ERR]` alone triggers self-healing below. Even then the action is mechanical only: re-capture the **same** command, read the printed `answer_file:` path, or relay the machine signal. **Never** decode, repair, reconstruct, summarise or author answer content, and never fall back to the host model's own knowledge. Parse-failure byte-level rules: `ADVANCED.md` §9.

> **`--stitch` is the sole non-forwarding mode.** It consumes skill outputs that already exist (no question is being answered, so no Coze call happens). It is still `entry.py`, still zero-LLM, still the one permitted action — see the Return path section below.

## How to use this skill

Run the single entry point with the user's question. Optionally attach a file (e.g. a CSR or protocol snippet). The stdout is the final answer — deliver it verbatim.

CLI invocation details, examples, and flag notes → `references/ADVANCED.md`.

### What entry.py does internally (all code, zero LLM) — the canonical pipeline

```
STEP 1  Attachment gate (if --attach) — BOTH paths ship a FILE via doc_context
        ├─ < 5 MB   → doc_memory.build_file_payload(allow_upload=True): upload ORIGINAL file to Coze /upload_file, ship as `doc_context` (mode=file_id; base64-forward fallback on failure)
        └─ > 5 MB   → convert locally (office_to_md.py for OOXML / direct read for txt-like), upload the resulting **.md** through the SAME doc_context channel + ℹ️ notice that cloud answers from the md version
STEP 2  Vague gate (deterministic regex, scripts/route.py — binary: vague | forwarded, the ONLY local gate): vague → clarify_loop.py (≤3 rounds) → questions to user, stop; forwarded → continue (Coze re-judges difficulty with its own LLM; timeout tier via route.timeout_tier)
STEP 3  Forward to Coze — orchestrate.run_orchestrate(payload): Coze async submit (/async_run, ms-level → task_id) + local prefetch (handoff card by default; brief only when explicitly enabled) → poll /task/{id} until terminal → merge (sync /run only as fallback when the async endpoint is unavailable)
STEP 4  Delegate stitch — if Coze returns <<<CT_TOOL_DELEGATE>>>, entry.py auto-runs refine_answer.py --card-inline (code, no LLM); since 2026-11-09 this normally emits a client handoff card (@skill:<slug>) instead of executing the sibling CLI
STEP 5  Output — entry.py writes the answer file (UTF-8), then the same bytes + `<<<CT_ANSWER_END>>>` + `checksum:` + `answer_file:` to stdout.buffer (single protocol, single producer since v1.3.21)
```

> **LLM-forbidden zone**: every STEP above is executed by code. The local LLM never picks the channel, never judges difficulty, never decides forwarding.

## Session, Context, Cache & Routing

Local modules enrich the Coze payload: multi-turn `conversation_history`, 30-min cross-session answer cache, 10-min near-duplicate dedup, and a controlled-vocabulary domain router (`scope_guard`). All four capabilities are wired into both `entry.py` and the workbench proxy. Module details, API tables, and endpoint contracts → `references/ADVANCED.md`.

## Requirements

| Item | Requirement |
|---|---|
| Runtime | `python3` stdlib only |
| Sibling skills | **Client-callable since 2026-11-09**: the client can invoke every locally registered `ct-*` skill directly. Availability is decided by `scripts/sibling_registry.json` (`skills[*].installed`) plus `<SKILLS_DIR>/<slug>/SKILL.md`, implemented in `handle_need_tool._client_callable()` — **not** by SkillHub listing. `need_tool` therefore defaults to a **code-generated `handoff` card** (`@skill:<slug>` + extracted params + the skill's real deliverables + Tier-B confidentiality note) instead of running the sibling's CLI on the user's behalf. `published` is a distribution fact only; `tier` remains the confidentiality boundary (protocols / subject data stay local, F33). `unpublished_a` / `unreleased_b` / `install_required` now fire only when the skill is genuinely absent locally (or `CT_ADVISOR_HANDOFF=0`). |
| Refiner (Coze) | `scripts/entry.py` (the **only** entry point; internal orchestrator via `scripts/orchestrate.py`) sends payload to `ct-advisor.coze.site` — **async-first** (v1.3.14): `POST /async_run` (ms-level → task_id) + `GET /task/{id}` polling, because sync `/run` / `/stream_run` are both hard-killed at 60.0s by the Coze gateway (stgw) and duration cannot be reliably predicted; sync `/run` remains only as fallback when `/async_run` is unavailable (404/405/5xx), and `CT_ADVISOR_ASYNC=0` disables async entirely. Credential embedded in `adapters/coze_token_embedded.py` (obfuscated public token — keep as-is). 90s timeout / 300s long timeout (= polling deadline in async mode). |
| External Refs | **teal** (insightsengineering) — clinical-data interactive exploration framework; **Docling** — structured PDF parsing. See "External Tool References". |

## Attachment handling (docx / xlsx / pptx · doc / xls / ppt · pdf)

**Single gate = 5 MB, decided FIRST inside `entry.py` (v1.1.0 workflow correction, 2026-09-25). BOTH paths deliver a FILE to Coze through the same `doc_context` channel.**

| Size | Behavior | Channel |
|---|---|---|
| `< 5 MB` | **Upload the original file directly** — never converted locally | `doc_memory.build_file_payload(allow_upload=True)` → Coze `/upload_file` → `doc_context` (`mode=file_id`); on upload failure auto-degrades to the base64 forward channel (`mode=file`) |
| `> 5 MB` | Convert to Markdown locally, then **upload the resulting `.md` as the attachment** — same `doc_context` channel — plus an ℹ️ notice that the cloud answers from the md version | `scripts/office_to_md.py` (stdlib-only; OOXML) or direct read (`.txt/.md/.csv/.tsv/.json`); unsupported formats get an explicit user prompt |

Coze decodes the original file natively for **any** Office format (OLE2 `.doc/.xls/.ppt` included), so fidelity is higher than any local conversion — this is why the <5 MB path uploads instead of converting.

**Governance pointer**: layered conversion strategy, user prompts and confidentiality boundary are consolidated in **ct-base §6.7**; the shared converter lives in `ct-base/scripts/office_to_md.py` (vendored copy).

**Deliverable boundary — the revised document is never returned (v1.24).** This skill's deliverable is **text only**: it does not generate, export, or hand back a modified document file. When the user asks for the revised file back, state plainly on the **first line** that **this feature is not available — only written suggestions are provided**, then give the suggestions as text the user can copy.

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

## Outbound Authorization Gate

Runs automatically inside `entry.py` → `scripts/orchestrate.py` before each outbound HTTP call (agent never triggers it manually). Endpoint `https://ct-advisor.coze.site/run` is in `auto_approve_endpoints` by default, so it never prompts. If the user wants another endpoint whitelisted across sessions, the USER adds it explicitly to `config.json` — **the agent MUST NOT edit `config.json`**.

## Bug Report (§20.3 · ct-base)

On defect detection or explicit user request, `adapters/bug_report.py` offers a sanitized 11-key report to `https://ct-bugreport.coze.site/run`. Two-stage confirmation mandatory.

## External Tool References (v1.3.4 · external authoritative assets)

- **teal** (insightsengineering, `install.packages('teal')`) — clinical-data interactive exploration framework for building Shiny review apps; reference model for the data-review integration mode.
- **Docling** (`pip install docling`) — structured parsing of regulatory documents (protocol/IB/CSR PDFs → hierarchical Markdown/JSON); attachment-parsing enhancement layer.
- **Pinnacle 21 Validation Rules** (Certara, public API `standards.pinnacle21.certara.net/validation-rules/<STD>`, header `X-Requested-With: XMLHttpRequest`) — industry-standard CDISC validation rule set; snapshots archived in `ct-base/references/pinnacle21_validation_rules/` (SDTM 566 / SEND 581 / ADaM 456 / Define-XML 167). Authoritative benchmark for data-standard compliance Q&A; mirrored to Coze KB topic `ref-topic-p21-data-rules`.
- **ICH M12 DDI Thresholds** (Step 4/5 official PDFs archived alongside `ct-base/references/m12_thresholds.md`) — CYP 50× / intestinal 10×, TDI 1.25, induction R-ratio, transporter Table 1, AUCR 0.80–1.25, GMR 90% CI 80–125%. Authoritative benchmark for DDI interaction Q&A; mirrored to Coze KB topic `ref-topic-m12-ddi`.

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

**Note on `[DEP-MISS]`:** before 2026-10-15 a missing `requests` library surfaced as `[DEP-MISS]` + an install prompt. The transport now uses stdlib `urllib`, so this failure class no longer exists; the handler remains as dormant defensive code.

---

## Extended reference

The sections below remain in [`references/ADVANCED.md`](references/ADVANCED.md) (moved 2026-11-15); they are authoritative and `ct-base/BASE.md §N.M` anchors are unchanged. Pulled back into this file during the 2026-11-15 compaction: the canonical `entry.py` pipeline, session/context/cache/routing, requirements, attachment handling, external tool references and the Error Self-Heal Protocol.

- Return path (`entry.py --stitch`) and the full output-format contract
- Integrity-check verification code and the extended HARD GATE field table
- Performance / deployment notes; capability domains; client handoff contract
- Consultation vs execution; retrieval keyword translation gate

The HIGHEST PRIORITY action, the Data Egress Guardrail (F33), the HARD GATE integrity table, Quality Gate / Stop Rules, Outbound Authorization Gate and Bug Report stay in this file.

Agents: read `HIGHEST PRIORITY` and the HARD GATE list before any action; the operational sections above are reference material and never override the single-entry-point rule.
