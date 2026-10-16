---
slug: ct-advisor
name: ct-advisor
displayName: Clinical Trial Chief Advisor / 临床试验总顾问
cn_name: 临床试验总顾问
version: 1.3.13
invocable: true
required_commands: [python]
summary: "面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问。所有问题（方法学/设计/合规/QC/现场执行/情报）统一提交云端 Coze 引擎分析处理。本地仅做确定性二值闸门（是否 vague）与附件解码，不保留知识库，不进行本地网络检索。外部参考：teal 临床数据交互探索框架。"
description: "The single entry point for the ct-series across the full clinical-development lifecycle — a cloud-assisted clinical trial advisor. All questions (methodology / design / compliance / QC / site-execution / intelligence) are forwarded to the cloud Coze engine for analysis. The local side only performs a deterministic binary vague-gate (vague | forwarded) and attachment decoding; no knowledge base is retained locally, and no local network retrieval occurs. External reference: the teal clinical-data interactive exploration framework. / 面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问。所有问题（方法学/设计/合规/QC/现场执行/情报）统一提交云端 Coze 引擎分析处理。本地仅做确定性二值闸门（是否 vague）与附件解码，不保留知识库，不进行本地网络检索。外部参考：teal 临床数据交互探索框架。"
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

# Clinical Trial Chief Advisor

## Published Application

| Item | Value |
|---|---|
| Share link | `https://ct-advisor.app.workbuddy.host/` |
| appId | `wbapp_FBxILYuXi6yMolY8CsYzA7` |
| Payload | `workbench/publish/` — in-skill, workspace-independent; deploy metadata in `workbench/app.config.json` (Python HTTP service) |

> **Re-publish rule**: always overwrite with the existing `appId` — the link must stay `https://ct-advisor.app.workbuddy.host/`; never `createNewApp`. After deploy, assert the returned `shareLink` equals the expected URL (ct-base §13.5 dirty-binding red line). Last republished 2026-09-26.

## Language

- **English guide** → [README.md](https://github.com/medstatstar/ct-advisor/blob/main/README.md) · **中文指南** → [README_zh-CN.md](https://github.com/medstatstar/ct-advisor/blob/main/README_zh-CN.md)
- **This SKILL.md body is English-only, agent-facing.** Bilingual walkthroughs live in the two READMEs; the answer language follows the user's question language.

## 🔴 HIGHEST PRIORITY: scripts/ask.py is the ONLY permitted action

> **The local LLM is FORBIDDEN from making any decisions in this skill. Its ONE AND ONLY allowed action is:**
>
> ```bash
> python scripts/ask.py --q "<user question>" [--attach "<path>"]
> ```
>
> **and then pipe the stdout to the user verbatim.**
>
> `ask.py` runs `entry.py` internally, then **decodes the base64 payload and verifies the
> sha256 checksum inside the script**. Its stdout is already the plain-text answer. The LLM
> never sees, copies, or transcribes the base64 payload — doing that by hand is what caused
> the 2026-10-16 incident (one character mistyped in a 2.6k-char payload → "checksum
> mismatch" → three Coze calls for one question).
>
> `entry.py` remains the underlying engine and the only Coze entry point. `ask.py` is a
> thin, contract-preserving wrapper: it generates nothing and rewrites nothing.

**HARD GATE — the following are absolutely PROHIBITED for the local LLM:**
- ❌ **NEVER** read, search, or reference any local knowledge base (the `knowledge/` directory has been removed)
- ❌ **NEVER** perform any local network retrieval or web search (`references/search-sites.md` has been removed)
- ❌ **NEVER** answer the question from the LLM's own knowledge — all domain expertise lives on the Coze side
- ❌ **NEVER** bypass `entry.py` by calling `route.py`, `refine_answer.py`, `orchestrate.py`, or any other script directly
- ❌ **NEVER** rewrite, rephrase, reorder, summarize, or "polish" the answer text obtained by base64-decoding the payload between `<<<CT_ANSWER_B64_START>>>` and `<<<CT_ANSWER_B64_END>>>`
- ❌ **NEVER** append a summary, lead-in, closing remark, or "key takeaways" before or after the decoded answer
- ❌ **NEVER** strip or alter the `checksum:` line that follows `<<<CT_ANSWER_B64_END>>>`
- ❌ **NEVER** translate or align language (the code already handles that)
- ❌ **NEVER** inject process narration ("Step 2", "Coze returned", "assembling payload")
- ❌ **NEVER** decide whether to forward to Coze — ALL questions are forwarded (entry.py handles routing internally)
- ❌ **NEVER** hand-copy, transcribe, or re-type the base64 payload into another command — a 2–3k-char random string cannot survive manual transcription, and a mismatch produced this way is a **false alarm**, not tampering (2026-10-16 incident)
- ❌ **NEVER** discard stderr with `2>$null` / `2>/dev/null` — stderr carries the answer-cache-hit / resident-service / `[ct-advisor][ERR]` signals that tell you whether a Coze call actually happened

**Why this rule exists:** The local LLM's "helpful" instincts (answering from its own knowledge, pre-reading files, post-formatting answers) have repeatedly violated the pipeline contract, destroyed Coze-delivered content formatting, altered numeric precision, injected unsolicited content, and bypassed the cloud analysis entirely. This rule eliminates ALL local LLM decision space.

## How to use this skill

### With a question only:
```bash
python scripts/ask.py --q "In phase III NSCLC patients, comparing pembrolizumab vs chemotherapy, how is the sample size for the primary endpoint OS estimated?"
```

### With an attachment:
```bash
python scripts/ask.py --q "Is this document related to medicine?" --attach "/path/to/file.docx"
```

**That's it.** The stdout is the final answer — pipe it to the user verbatim.

> **Debugging / advanced**: `python scripts/ask.py --q "..." --raw` prints entry.py's raw
> (still base64-wrapped) stdout; `python scripts/entry.py --q "..." --out <file>` writes the
> full raw stdout to a file so it can be re-verified **without re-running Coze**.

### What entry.py does internally (all code, zero LLM) — the canonical pipeline

```
STEP 1  Attachment gate (if --attach) — BOTH paths ship a FILE via doc_context
        ├─ < 5 MB   → doc_memory.build_file_payload(allow_upload=True): upload ORIGINAL file to Coze /upload_file, ship as `doc_context` (mode=file_id; base64-forward fallback on failure)
        └─ > 5 MB   → convert locally (office_to_md.py for OOXML / direct read for txt-like), upload the resulting **.md** through the SAME doc_context channel + ℹ️ notice that cloud answers from the md version
STEP 2  Vague gate (deterministic regex, scripts/route.py — binary: vague | forwarded, the ONLY local gate): vague → clarify_loop.py (≤3 rounds) → questions to user, stop; forwarded → continue (Coze re-judges difficulty with its own LLM; timeout tier via route.timeout_tier)
STEP 3  Forward to Coze — orchestrate.run_orchestrate(payload): parallel Coze /run fire + local ct-skill prefetch → merge
STEP 4  Delegate stitch — if Coze returns <<<CT_TOOL_DELEGATE>>>, entry.py auto-runs refine_answer.py --card-inline (code, no LLM)
STEP 5  Output — entry.py stdout carries a base64 ASCII-safe payload in <<<CT_ANSWER_B64_START/END>>> + sha256 checksum
STEP 6  Unwrap + verify (scripts/ask.py) — decode the payload, re-hash, compare checksum; stdout becomes the plain-text answer (exit code 2 on mismatch, reason on stderr)
```

> **LLM-forbidden zone**: every STEP above is executed by code. The local LLM
> never picks the channel, never judges difficulty, never decides forwarding.

### Output format

`scripts/ask.py` (what the LLM calls) — stdout is the **plain-text answer**:

```
{the verified answer text}
```

`scripts/entry.py` (internal protocol, wrapped by ask.py) — stdout is the ASCII-safe envelope:

```
<<<CT_ANSWER_B64_START>>>
{base64 of the LF-normalized answer}
<<<CT_ANSWER_B64_END>>>
checksum: {sha256[:16] of the LF-normalized answer}
```

> 🔴 **base64 ASCII-safe payload (v1.3.9)**: the answer is base64-encoded before output — the delimiters, payload and checksum line are pure ASCII (a subset of every console code page, incl. cp936/GBK). PowerShell 5.1 decoding captured stdout with the wrong code page therefore **cannot** corrupt the payload: this structurally closes the "GBK mojibake → byte-level checksum false-alarm → agent misreads it as encoding loss/tampering → pointless Coze re-run" loop. **Decode FIRST, then verify** (see the check code below). The checksum is still computed over the LF-normalized answer text (CRLF-tolerance retained). A plain-text `<<<CT_ANSWER_START>>>` (non-b64) block is legacy/debug output only — if you ever see one, apply the same decode-then-verify discipline but treat mojibake as possible.

### 🔴 sha256 Anti-tamper Check (HARD GATE):
**Since 2026-10-16 this check is performed by `scripts/ask.py`, not by the LLM.** `ask.py`
decodes the payload, re-hashes the LF-normalized answer and compares it against the
`checksum:` line; on mismatch it exits with code 2, prints nothing on stdout and puts the
reason on stderr. **A non-zero exit from `ask.py` means: deliver nothing, re-run nothing,
relay the stderr reason and stop.**

The equivalent logic (kept for debugging / manual reproduction only — never the normal path):

```python
import base64, hashlib, re
stdout = "...(entry.py output)..."
m = re.search(r'<<<CT_ANSWER_B64_START>>>\r?\n(.*?)\r?\n<<<CT_ANSWER_B64_END>>>\r?\nchecksum: (.+)', stdout, re.DOTALL)
if m:
    # Decode the base64 payload FIRST (v1.3.9): the b64 charset is pure ASCII,
    # so the payload survives ANY console code page (cp936 included) byte-for-byte.
    # Strip ALL whitespace before decoding (2026-10-15 audit): PowerShell
    # `Out-String` wraps long payloads (>80 display cols — a 1000-char answer is
    # ~1.3k+ b64 chars) with mid-payload newlines; Python's b64decode tolerates
    # them but strict decoders (e.g. .NET FromBase64String) do not. Then hash the
    # LF-normalized answer (CRLF-tolerance retained).
    answer = base64.b64decode(re.sub(r"\s+", "", m.group(1))).decode("utf-8")
    expected_checksum = m.group(2).strip()
    actual_checksum = hashlib.sha256(answer.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:16]
    if actual_checksum != expected_checksum:
        # DO NOT blindly re-run — work the "Checksum-mismatch decision table" below first.
        print("⚠️ answer integrity check failed, please retry.")
    else:
        # OK — pass answer verbatim
        print(answer)
```

**If the checksum does not match, the local LLM MUST NOT deliver the answer to the user.** This prevents any silent tampering.

> 🔴 **Capture stdout BYTE-FAITHFULLY (Windows PowerShell · 2026-10-15)**: since v1.3.9 the answer payload is base64 (pure ASCII), so the **checksum-relevant bytes survive any console code page** — verified end-to-end on a Chinese Windows with the default `gb2312`/cp936 `[Console]::OutputEncoding` (payload intact, checksum matched). Two residual notes: (1) setting `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` before invoking `entry.py` is still **recommended** — it keeps stderr diagnostics (Chinese log lines) readable, but is no longer load-bearing for the gate; (2) if you ever capture a legacy plain-text `<<<CT_ANSWER_START>>>` block (debug output), GBK mojibake IS possible again — decode-then-verify per the decision table. In Git Bash / `cmd /c` with file redirection / WSL the byte stream is faithful — no action needed. Do NOT "fix" encoding by writing stdout to a temp file (see the L3 discipline below).

> 🔴 **Checksum-mismatch decision table (HARD GATE · 2026-10-15)**: a mismatch is NOT a licence to re-run. Work the table IN ORDER and stop at the first hit:
>
> | # | Check | Action |
> |---|---|---|
> | 1 | Re-hash after CRLF normalization (`.replace("\r\n", "\n")` — see code above) | Match → deliver verbatim. Done. |
> | 1b | `b64decode` raised (e.g. strict decoder met mid-payload newlines from PowerShell `Out-String` line-wrapping of a long payload) | Strip ALL whitespace from the b64 field (`re.sub(r"\s+", "", m.group(1))`) and decode again — the verify code above already does this. Only if it still fails treat it as a corrupted capture → step 2. Never re-run Coze for this. |
> | 1c | stdout ends with a truncation marker (e.g. `…[输出截断]`) or the trailing `checksum:` line is missing entirely | The capture tool truncated the echo (PowerShell tool ≈20k chars; the absolute worst case — coze 1000-char answer + 4000-char skill result both maxed — is ~20,150 b64 chars, verified intact on Bash). **Switch to the Bash / Git Bash tool and re-capture — do NOT re-run Coze.** |
> | 2 | Is the captured answer visibly mojibake (CJK rendered as `鏈熶复…`-style garbage) or truncated? | With the v1.3.9 base64 payload this should no longer happen for the answer block — if it does, you are looking at legacy/debug plain-text output or a corrupted capture pipeline. **The corrupted text is NOT repairable in place** — cp936 mis-decodes some UTF-8 byte pairs as illegal (e.g. `0x9A`) and replaces them with U+FFFD, permanently destroying the original bytes (both deterministic byte-reversal and any LLM rewrite were tested and cannot restore them). Fix the capture (set `[Console]::OutputEncoding` to UTF-8, or re-capture in Git Bash reading the FULL stdout into a variable) and re-send Coze **at most once**, stating the reason to the user. Cost note: a re-run is now short-circuited locally by **`answer_cache.py`** (30-min TTL, keyed on the question + doc_context + difficulty fingerprint) — stderr shows `answer-cache hit: replayed local cached answer` and **no Coze call is made**. *(Before 2026-10-16 this note was wrong for the entry.py path: `dedup_guard` was wired only into the `refine_answer.py` CLI, and `entry.py` never set `query_origin`, so re-runs went straight to Coze — the exact defect that made one question cost three Coze calls.)* Even a genuine re-send is cheap: the Coze backend has a 4-gate server-side cache (cross-request hit, verified). |
> | 3 | Regex found NO `<<<CT_ANSWER_B64_START>>>` block at all (stdout structure destroyed, or empty stdout) | First rule out a real endpoint fault — check stderr for `[ct-advisor][ERR]` and run `check_coze.py` (token / dead proxy / network / unreachable). If the endpoint is healthy this is still a capture-layer failure → same repair as step 2, re-send ≤1. If the endpoint itself is down, report the diagnosis to the user and stop — do not re-send into a dead endpoint. |
> | 4 | Still mismatched, text looks clean | Treat as potential tampering: do NOT deliver; do NOT loop re-runs; report expected vs actual checksums to the user and stop. |
>
> Re-running without evidence from steps 2–3 is a protocol violation (it caused the observed incident: the same question fired 2–3 times, a single Q&A dragging to minutes).

> 🔴 **No host-model fallback (HARD GATE · 2026-10-15)**: ct-advisor is coze-only **by design** — there is no local knowledge base or database, so a host-model direct answer on a clinical question has no domain substrate and is **forbidden as a fallback** (a bare host-model answer was evaluated and rejected: quality cannot be guaranteed without the cloud knowledge base and tool chain). The same tiering rule means attachment / `doc_context` content must **never** leave the Coze channel. The ONLY sanctioned recovery for a broken capture is: **repair the capture → re-send once (≤1, dedup-cached in the common case)**. Everything else stops and reports.

> 🔴 **Short-circuit output is also GATE-wrapped (2026-10-15 · cache layer updated 2026-10-16)**: both short-circuit paths — `answer_cache.py` on the entry.py main chain, `dedup_guard` on the refine_answer.py serial path — emit their cached answer through the same `<<<CT_ANSWER_B64_START/END>>> + checksum` wrapper as a fresh Coze call (stderr marks `answer-cache hit` / `dedup short-circuit`). `ask.py` verifies it like any other answer — a cached answer is a legitimate delivery, not an error.

> 🔴 **Single-run discipline (performance · as mandatory as the HARD GATE)**: `entry.py` is one complete Coze remote call and the main time cost of a single Q&A. The default is **one call per question**; with `ask.py` this is structural — decode + sha256 happen inside the same script invocation, so there is nothing left for the LLM to "verify again". **Re-calling `ask.py` / `entry.py` purely to perform the check is strictly forbidden** (in practice this once caused "the same question sent 2–3 times, a single Q&A dragging to 4 minutes"). The single exception is decision-table steps 2–3: **at most one re-send to repair a broken CAPTURE** (mojibake/truncation/destroyed structure), with the reason stated to the user — never for a clean-text mismatch (step 4 → stop) and never without capture evidence. If you need to persist output, use `entry.py --out <file>` instead of re-running.

**Verification discipline (L3 · superseded by ask.py 2026-10-16)**: the sha256 integrity check MUST happen against the stdout of the SAME `entry.py` call, in memory. Since 2026-10-16 `scripts/ask.py` performs it inside the script, in one process, with zero LLM round-trips — the strongest form of this discipline. **Forbidden**: writing stdout to a temp file just for the check, extra tool round-trips, post-hoc temp-file cleanup, and (new) any attempt by the LLM to transcribe or re-type the base64 payload.

## Performance Optimization & Deployment Notes (L1/L2/L3, 2026-09-26)

This skill has implemented four performance optimizations; see `PERF_SOP.md` for details:
- **L1 Resident orchestration service** (`scripts/serve.py` + `entry.py` client): heavy modules are warmed up once, so local overhead → 0. Idle window raised 600s → 3600s (2026-10-16).
- **L2 Parallel warm-up** (`scripts/orchestrate.py`): eliminates stacked serial imports.
- **L3 Inline verification discipline**: sha256 is done inline in memory — since 2026-10-16 fully inside `scripts/ask.py`, with zero LLM round-trips.
- **L4 Single-command + local answer cache (2026-10-16)**: `scripts/ask.py` merges run + decode + verify + print into one call (the LLM never touches the base64 payload), and `scripts/answer_cache.py` gives the entry.py main chain a 30-min answer cache so a re-run costs **0 Coze calls**. Root cause fixed: the `dedup_guard` short-circuit had never been reachable from `entry.py` (guard wired only into the `refine_answer.py` CLI; `query_origin` never set by entry.py), so every re-run was a real Coze round-trip — three of them for a single question in the 2026-10-16 log.

**⚠️ Deployment restriction (important)**: the skill directory lives on a network share whose ACL is creator-owner — you can create new files, but **overwriting pre-installed existing files raises `PermissionError 13`**, and deletion is also blocked by a trash hook. Therefore, any change to `scripts/*.py` / `SKILL.md` should be written as a same-directory `.new` copy, then overwritten on the user's local machine with `move /Y` (command in `PERF_SOP.md` §4, or run `scripts/_perf_deploy.py`).

**Version drift**: the resident service caches code; after updating skill files, the old service still runs old code until its idle timeout (3600s since 2026-10-16; override with `CT_ADVISOR_IDLE`). `entry.py` has a built-in `/version` probe that, before reusing an old service, compares a **code fingerprint** — the max mtime across `scripts/*.py` + `adapters/**/*.py`, computed by `scripts/code_fingerprint.py` — against the value the service recorded at startup. If the local copy is newer it auto-shuts-down the old service and launches the new version. **No manual restart is ever required.** *(Before 2026-10-16 the probe compared only `orchestrate.py`'s mtime, so updating just `serve.py` or `adapters/**` silently failed to take effect — fixed in the same release.)*

`curl http://127.0.0.1:18771/shutdown` remains available as a manual escape hatch (e.g. the port is held by a stuck service), but it is **not part of any deployment procedure** — end users never need it.

## Requirements

| Item | Requirement |
|---|---|
| Runtime | `python3` stdlib only |
| Sibling skills | **Tier A · listed on SkillHub** (non-confidential input, publicly released): `ct-registry` / `ct-safety` / `ct-literature` / `ct-samplesize` — auto-routed via Coze `need_tool` (entry.py handles card-inline execution). **Tier A · NOT yet listed**: `ct-pipeline` / `ct-synthdata` → `unpublished_a`, answer from Coze draft. **Tier B** (confidential input, **not publicly released**): `ct-protocol` / `ct-csr` / `ct-analysis` / `ct-sdtm` / `ct-eligibility` etc. — never installable. |
| Refiner (Coze) | `scripts/ask.py` (LLM-facing wrapper) → `scripts/entry.py` (internal orchestrator via `scripts/orchestrate.py`) POSTs payload to `ct-advisor.coze.site/run`. Credential embedded in `adapters/coze_token_embedded.py` (obfuscated public token — keep as-is). 90s timeout / 300s long timeout. |
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

## Quality Gate & Stop Rules

**Presentation rules (user-mandated, hard)** — deliver only the plain-text answer printed by `scripts/ask.py` (which is the verified decode of the payload between `<<<CT_ANSWER_B64_START>>>` and `<<<CT_ANSWER_B64_END>>>`). **Never emit any workflow / process narration to the user.**

**🔔 Forward-mode user notice (the ONLY allowed process message)** — entry.py emits a brief notice to stderr before firing the Coze call. The local LLM should not add any additional process chatter.

## Outbound Authorization Gate

Runs automatically inside `entry.py` → `scripts/orchestrate.py` before each outbound HTTP call (agent never triggers it manually). Endpoint `https://ct-advisor.coze.site/run` is in `auto_approve_endpoints` by default, so it never prompts. If the user wants another endpoint whitelisted across sessions, the USER adds it explicitly to `config.json` — **the agent MUST NOT edit `config.json`**.

## External Tool References (v1.3.4 · external authoritative assets)

- **teal** (insightsengineering, `install.packages('teal')`) — clinical-data interactive exploration framework for building Shiny review apps; reference model for the data-review integration mode.
- **Docling** (`pip install docling`) — structured parsing of regulatory documents (protocol/IB/CSR PDFs → hierarchical Markdown/JSON); attachment-parsing enhancement layer.
- **Pinnacle 21 Validation Rules** (Certara, public API `standards.pinnacle21.certara.net/validation-rules/<STD>`, header `X-Requested-With: XMLHttpRequest`) — industry-standard CDISC validation rule set; snapshots archived in `ct-base/references/pinnacle21_validation_rules/` (SDTM 566 / SEND 581 / ADaM 456 / Define-XML 167). Authoritative benchmark for data-standard compliance Q&A; mirrored to Coze KB topic `ref-topic-p21-data-rules`.
- **ICH M12 DDI Thresholds** (Step 4/5 official PDFs archived alongside `ct-base/references/m12_thresholds.md`) — CYP 50× / intestinal 10×, TDI 1.25, induction R-ratio, transporter Table 1, AUCR 0.80–1.25, GMR 90% CI 80–125%. Authoritative benchmark for DDI interaction Q&A; mirrored to Coze KB topic `ref-topic-m12-ddi`.

## Bug Report (§20.3 · ct-base)

On defect detection or explicit user request, `adapters/bug_report.py` offers a sanitized 11-key report to `https://ct-bugreport.coze.site/run`. Two-stage confirmation mandatory.


## Error Self-Heal Protocol (stderr machine signals · 2026-10-15)

**Scope — failure paths ONLY.** On a successful run (`scripts/ask.py` exits 0 and prints the answer, and **no `[ct-advisor][ERR]` line on stderr**), the agent delivers the answer and stops. **The agent MUST NOT enter self-healing when no error was reported** — no proactive health checks, no proactive dependency installs, no proactive config/env edits, no speculative retries. The `[ct-advisor][ERR]` signal is the **only** trigger.

> **Where signals live (2026-10-16)**: the resident service (`scripts/serve.py`) is spawned with `stderr=DEVNULL`, so anything written inside the service process — including an `[ct-advisor][ERR]` emitted on the service path — is redirected by the service itself to **`config/serve.log`** (auto-truncated at 1 MB). If `ask.py` fails with "no B64 block found" while stderr carries no `[ERR]` line, read the tail of `config/serve.log` before concluding anything.

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
