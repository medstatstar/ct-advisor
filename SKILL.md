---
slug: ct-advisor
name: ct-advisor
displayName: Clinical Trial Chief Advisor / 临床试验总顾问
cn_name: 临床试验总顾问
version: 1.3.46
invocable: true
required_commands: [python]
summary: "面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问。覆盖范围已扩大至合规应答 / 项目运营 / 交付物撰写 / 方案设计 / 统计分析 / 注册申报 / 安全性 / 数据管理 / 真实世界研究——仅当明确非医药/生命科学语境时才给建设性转介建议。本地侧在确定性二值闸门（是否 vague）与附件解码之外，新增会话上下文注入（多轮承接）；答案缓存与去重一律由云端承担（仅为独立问题服务，本地不缓存答案）；不保留知识库，不进行本地网络检索。外部参考：teal 临床数据交互探索框架。"
description: "The single entry point for the ct-series across the full clinical-development lifecycle — a cloud-assisted clinical trial advisor. Coverage has been broadened to regulatory-response / trial-operations / deliverable-drafting / study-design / statistics / submission / safety / data-management / real-world-evidence; only clearly non-medical / non-life-science questions receive a constructive referral. On the local side, in addition to the deterministic vague-gate and attachment decoding, it injects multi-turn session context (continuation of prior rounds); answer caching and deduplication are handled entirely in the cloud (serving standalone questions only — no answer cache is kept locally); no knowledge base is retained locally and no local network retrieval occurs. External reference: the teal clinical-data interactive exploration framework. / 面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问。覆盖范围已扩大至合规应答 / 项目运营 / 交付物撰写 / 方案设计 / 统计分析 / 注册申报 / 安全性 / 数据管理 / 真实世界研究——仅当明确非医药/生命科学语境时才给建设性转介建议。本地侧在确定性二值闸门（是否 vague）与附件解码之外，新增会话上下文注入（多轮承接）；答案缓存与去重一律由云端承担（仅为独立问题服务，本地不缓存答案）；不保留知识库，不进行本地网络检索。外部参考：teal 临床数据交互探索框架。"
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
  network_note: "All questions are forwarded to Coze (single call, internal `scripts/orchestrate.py`). Local side performs NO knowledge base lookup, NO local network retrieval, NO web search. Attachments under 5 MB are uploaded as original bytes to Coze `/upload_file` and shipped as the top-level `doc_context` field (Coze decodes natively); attachments over 5 MB are converted to Markdown locally via `scripts/office_to_md.py` (stdlib-only) and the resulting .md is uploaded through the SAME doc_context channel. The Coze-side knowledge base is the single source of truth."
  filesystem: "Read-only to own files; no confidential data leaves locally — Coze payloads sanitized, query_origin is a stable per-machine sha256 hash (non-PII)."
adapted_from: "https://github.com/A-xin946/clinical-trial-advisor"
dependencies:
  - {slug: ct-registry,   tier: A}
  - {slug: ct-safety,     tier: A}
  - {slug: ct-literature, tier: A}
  - {slug: ct-samplesize, tier: A}
tier: A
---
## Data Egress Guardrail (CT family standard · F33)

This skill may call external endpoints (Coze services, shared third-party search
endpoints, public APIs or LLMs). **Internal confidential data must not leave the
local domain.** Mandatory rules:

- **Never outbound**: patient-level records, unpublished protocols / CSRs / internal
  documents, personal identifiers or sponsor-confidential content — as query terms,
  attachments or prompt payload.
- **Allowed minimum**: public search terms and non-content metadata only (machine
  hash, skill version, entry point, language, request id). Results from public
  registries (ct.gov / CDE / FAERS / OpenAlex / PubMed, etc.) are processed locally.
- **Local first**: computation, de-identification, aggregation and reporting stay on
  this machine; confirm the payload carries no confidential field before any cloud call.
- **Visible disclosure**: workbench search forms must state the outbound endpoint and
  this boundary in visible text, not only in a hover tooltip.
- **Fail loud**: stop and tell the user if any rule cannot be guaranteed; never
  degrade silently.

Machine-checked by `ct-base/scripts/spec_lint.py` rule **F33**.


# Clinical Trial Chief Advisor

## Language

- **English guide** → [README.md](https://github.com/medstatstar/ct-advisor/blob/main/README.md) · **中文指南** → [README_zh-CN.md](https://github.com/medstatstar/ct-advisor/blob/main/README_zh-CN.md)
- **This SKILL.md body is English-only, agent-facing.** Bilingual walkthroughs live in the two READMEs; the answer language follows the user's question language.

## 🔴 HIGHEST PRIORITY: scripts/entry.py is the ONLY permitted action

> **The local LLM is FORBIDDEN from making any decisions in this skill. Its ONE AND ONLY allowed action is:** Run the single entry point with the user's question (and optional attachment). Pipe the stdout to the user verbatim. CLI details live in `references/ADVANCED.md` — do not type commands from here.
>
> Since **v1.3.21** the stdout is **plain text followed by a trailing integrity line** and one
> ASCII pointer to the answer file — no decoding, no transcription, no second command:
>
> ```
> {the answer text, as many lines as it needs}
> <<<CT_ANSWER_END>>>
> checksum: {sha256[:16]}
> answer_file: C:/Users/<user>/.workbuddy/skills/ct-advisor/_answers/{checksum}.md
> ```
>
> **One entry point, one output shape, one protocol, one place where the protocol is produced.**
> Since v1.3.21 there is **no base64 anywhere in the pipeline** — not between code modules, not
> on the wire, not in the browser. The reason is historical: v1.3.9 introduced base64 to survive
> cp936 console mojibake, but that forced the LLM to hand-copy a ~2.6k-char random string into a
> second command (2026-10-16 incident: `5Lzd` typed for `5L+d`, a "checksum failure" that was
> pure transcription damage, then three real Coze calls for one question). The wrapper that fixed
> it left two parallel protocols, a 4× payload inflation, and — once the browser started taking
> the API directly — a decoder in *each* client. v1.3.21 removes the need instead of managing it:
> **encoding is no longer a decision made at the exit**. `entry.py` writes UTF-8 bytes straight to
> `stdout.buffer` (constant, no code-page inspection, no flags), the marker/checksum pair is
> produced in exactly one function, and the same bytes are also on disk. `scripts/ask.py` survives
> only as a zero-logic forwarding shim for stale callers.

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

> **`--stitch` is the sole non-forwarding mode.** It consumes skill outputs that
> already exist (no question is being answered, so no Coze call happens). It is
> still `entry.py`, still zero-LLM, still the one permitted action — see the
> Return path section below.

## How to use this skill

Run the single entry point with the user's question. Optionally attach a file (e.g. a CSR or protocol snippet). The stdout is the final answer — deliver it verbatim.

CLI invocation details, examples, and flag notes → `references/ADVANCED.md`.

### 🔴 Integrity check (HARD GATE · simplified in v1.3.19, final in v1.3.21)

Because the answer arrives as **plain text**, the whole check collapsed into one structural
question: **is the trailing `<<<CT_ANSWER_END>>>` marker there?**

| # | Observation | Meaning | Action |
|---|---|---|---|
| 1 | Marker + `checksum:` present, body non-empty | Capture complete | Deliver the body verbatim (`answer_file:` line included, it is not part of the answer). `checksum:` re-verification is optional here — the marker's presence already proves the capture was not cut. |
| 2 | Marker absent, or `checksum:` line missing | The tool channel truncated the capture | Re-capture the **same** command with Bash / Git Bash. **Do NOT re-run Coze.** |
| 3 | Marker present but checksum mismatch (code below) | Real corruption, not truncation | Do NOT deliver. Report expected vs actual and stop — never loop re-runs. |
| 4 | Body looks garbled but marker + checksum are intact | Display-layer code page, data intact | **Read the `answer_file:` path exactly as printed** (absolute ASCII — verified to survive the capture that destroyed the body) and deliver everything before `<<<CT_ANSWER_END>>>`. No re-run. **If that line is missing** (both candidate dirs unwritable), stop and report — never decode or guess the text. |

Re-running without capture evidence is a protocol violation: in the 2026-10-15/16 incidents it
made one question fire 2–3 times, dragging a single Q&A to minutes.

## Quality Gate & Stop Rules

**Presentation rules (user-mandated, hard)** — deliver only the plain-text answer printed by `scripts/entry.py` (everything above the trailing `<<<CT_ANSWER_END>>>` marker). **Never emit any workflow / process narration to the user.**

**🔔 Forward-mode user notice (the ONLY allowed process message)** — entry.py emits a brief notice to stderr before firing the Coze call. The local LLM should not add any additional process chatter.

## Outbound Authorization Gate

Runs automatically inside `entry.py` → `scripts/orchestrate.py` before each outbound HTTP call (agent never triggers it manually). Endpoint `https://ct-advisor.coze.site/run` is in `auto_approve_endpoints` by default, so it never prompts. If the user wants another endpoint whitelisted across sessions, the USER adds it explicitly to `config.json` — **the agent MUST NOT edit `config.json`**.

## Bug Report (§20.3 · ct-base)

On defect detection or explicit user request, `adapters/bug_report.py` offers a sanitized 11-key report to `https://ct-bugreport.coze.site/run`. Two-stage confirmation mandatory.



## Extended reference

The following sections were moved **verbatim** to [`references/ADVANCED.md`](references/ADVANCED.md)
on 2026-11-15 to keep this entry file within the 200-line limit (ct-base §16.1).
They remain authoritative; `ct-base/BASE.md §N.M` anchors and all cross-skill references are unchanged.

- Return path (`entry.py --stitch`), canonical `entry.py` pipeline and output format
- Integrity-check verification code and the full HARD GATE field table
- Performance / deployment notes; session, context, cache and routing
- Capability domains; client handoff contract; consultation vs execution
- Requirements; attachment handling; external tool references
- Retrieval keyword translation gate; error self-heal protocol

The HIGHEST PRIORITY action, the Data Egress Guardrail (F33), the HARD GATE integrity
table, Quality Gate / Stop Rules, Outbound Authorization Gate and Bug Report stay in this file.
