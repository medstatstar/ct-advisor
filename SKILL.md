---
slug: ct-advisor
name: ct-advisor
displayName: Clinical Trial Chief Advisor / 临床试验总顾问
cn_name: 临床试验总顾问
version: 1.3.20
invocable: true
required_commands: [python]
summary: "面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问。覆盖范围已扩大至合规应答 / 项目运营 / 交付物撰写 / 方案设计 / 统计分析 / 注册申报 / 安全性 / 数据管理 / 真实世界研究——仅当明确非医药/生命科学语境时才给建设性转介建议。本地侧在确定性二值闸门（是否 vague）与附件解码之外，新增会话上下文注入（多轮承接）与答案缓存/去重短路（省云端耗时）；不保留知识库，不进行本地网络检索。外部参考：teal 临床数据交互探索框架。"
description: "The single entry point for the ct-series across the full clinical-development lifecycle — a cloud-assisted clinical trial advisor. Coverage has been broadened to regulatory-response / trial-operations / deliverable-drafting / study-design / statistics / submission / safety / data-management / real-world-evidence; only clearly non-medical / non-life-science questions receive a constructive referral. On the local side, in addition to the deterministic vague-gate and attachment decoding, it now also injects multi-turn session context (continuation of prior rounds) and short-circuits via an answer cache / dedup store (saving cloud calls); no knowledge base is retained locally and no local network retrieval occurs. External reference: the teal clinical-data interactive exploration framework. / 面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问。覆盖范围已扩大至合规应答 / 项目运营 / 交付物撰写 / 方案设计 / 统计分析 / 注册申报 / 安全性 / 数据管理 / 真实世界研究——仅当明确非医药/生命科学语境时才给建设性转介建议。本地侧在确定性二值闸门（是否 vague）与附件解码之外，新增会话上下文注入（多轮承接）与答案缓存/去重短路（省云端耗时）；不保留知识库，不进行本地网络检索。外部参考：teal 临床数据交互探索框架。"
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

## 🔴 HIGHEST PRIORITY: scripts/entry.py is the ONLY permitted action

> **The local LLM is FORBIDDEN from making any decisions in this skill. Its ONE AND ONLY allowed action is:**
>
> ```bash
> python scripts/entry.py --q "<user question>" [--attach "<path>"]
> ```
>
> **and then pipe the stdout to the user verbatim.**
>
> Since v1.3.19 the stdout is **plain text followed by a trailing integrity line** — no
> decoding, no transcription, no second command:
>
> ```
> {the answer text, as many lines as it needs}
> <<<CT_ANSWER_END>>>
> checksum: {sha256[:16]}
> ```
>
> **One entry point, one output shape, one protocol.** The base64 envelope introduced in
> v1.3.9 is now strictly an *internal* transport between code modules (`orchestrate` →
> `serve` / `refine_answer` → `entry`); `entry.py` unwraps it exactly once at the process
> boundary. `scripts/ask.py` survives only as a zero-logic forwarding shim for stale callers.
> Since **v1.3.20** the same rule holds on the *return* side: the workbench proxy
> (`workbench/ct-advisor-proxy.py`) unwraps any base64 payload in the upstream JSON before
> forwarding it, so **every client receives plain text** — the browser no longer ships a
> decoder (`decodeB64Utf8` / `_raw_b64_result` were removed in the same commit).
>
> **Why the two-layer history is gone.** v1.3.9 introduced base64 to survive cp936 console
> mojibake, but that forced the LLM to hand-copy a ~2.6k-char random string into a second
> command — which it cannot do reliably (2026-10-16 incident: `5Lzd` typed for `5L+d`, a
> "checksum failure" that was pure transcription damage, then three real Coze calls for one
> question). The wrapper that fixed it left two parallel protocols plus a 4× payload
> inflation that pressed against the tool-output ceiling. Keeping base64 inside and emitting
> plain text outside resolves both at once.

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
- ❌ **NEVER** discard stderr with `2>$null` / `2>/dev/null` — stderr carries the answer-cache-hit / resident-service / `[ct-advisor][ERR]` signals that tell you whether a Coze call actually happened

**Why this rule exists:** The local LLM's "helpful" instincts (answering from its own knowledge, pre-reading files, post-formatting answers) have repeatedly violated the pipeline contract, destroyed Coze-delivered content formatting, altered numeric precision, injected unsolicited content, and bypassed the cloud analysis entirely. This rule eliminates ALL local LLM decision space.

## How to use this skill

### With a question only:
```bash
python scripts/entry.py --q "In phase III NSCLC patients, comparing pembrolizumab vs chemotherapy, how is the sample size for the primary endpoint OS estimated?"
```

### With an attachment:
```bash
python scripts/entry.py --q "Is this document related to medicine?" --attach "/path/to/file.docx"
```

**That's it.** The stdout is the final answer — pipe it to the user verbatim.

> **Debugging / advanced**: `python scripts/entry.py --q "..." --out <file>` writes the full
> stdout to a file so it can be re-verified **without re-running Coze**. `--b64` reproduces the
> legacy base64 envelope — an **escape hatch only**, for the rare console where plain CJK
> output cannot survive code-page conversion; if you use it you own the decode step.
>
> **Length is no longer a channel risk.** A 6000-char CJK answer now leaves `entry.py` as
> ≈6,000 characters. Under base64 it was 24,000 — past the PowerShell ~20,000 truncation line
> and hard against the Bash inline ceiling (~30,000 → persisted to a file with a 2 KB preview
> only). Decision table 1c covers the truncation signal.
>
> `scripts/ask.py` still exists but is **not** the entry point: it is a zero-logic forwarder
> that inherits `entry.py`'s stdout/stderr/exit code for stale callers.

### What entry.py does internally (all code, zero LLM) — the canonical pipeline

```
STEP 1  Attachment gate (if --attach) — BOTH paths ship a FILE via doc_context
        ├─ < 5 MB   → doc_memory.build_file_payload(allow_upload=True): upload ORIGINAL file to Coze /upload_file, ship as `doc_context` (mode=file_id; base64-forward fallback on failure)
        └─ > 5 MB   → convert locally (office_to_md.py for OOXML / direct read for txt-like), upload the resulting **.md** through the SAME doc_context channel + ℹ️ notice that cloud answers from the md version
STEP 2  Vague gate (deterministic regex, scripts/route.py — binary: vague | forwarded, the ONLY local gate): vague → clarify_loop.py (≤3 rounds) → questions to user, stop; forwarded → continue (Coze re-judges difficulty with its own LLM; timeout tier via route.timeout_tier)
STEP 3  Forward to Coze — orchestrate.run_orchestrate(payload): Coze async submit (/async_run, ms-level → task_id) + local ct-skill prefetch → poll /task/{id} until terminal → merge (sync /run only as fallback when the async endpoint is unavailable)
STEP 4  Delegate stitch — if Coze returns <<<CT_TOOL_DELEGATE>>>, entry.py auto-runs refine_answer.py --card-inline (code, no LLM)
STEP 5  Output — entry.py unwraps the internal envelope **once** and prints plain text + `<<<CT_ANSWER_END>>>` + `checksum:` (single protocol since v1.3.19; `--b64` restores the legacy envelope)
```

> **LLM-forbidden zone**: every STEP above is executed by code. The local LLM
> never picks the channel, never judges difficulty, never decides forwarding.

### Output format

`scripts/entry.py` — stdout is the **plain-text answer plus a trailing integrity line**:

```
{the answer text, as many lines as it needs}
<<<CT_ANSWER_END>>>
checksum: {sha256[:16] of everything before the marker, LF-normalized}
```

The marker sits at the **end** on purpose: any channel truncation removes it together with
the checksum, so a damaged capture is obvious at a glance instead of silently passing. The
checksum covers the answer body only (everything from the first byte up to and including the
newline immediately before the marker), so it is trivially reproducible.

> **Where base64 still lives (internal only)**: `orchestrate._wrap` emits the
> `<<<CT_ANSWER_B64_START/END>>>` envelope when passing results *between code modules* —
> process-to-process, where binary safety matters and no LLM is involved. `entry.py` decodes
> it exactly once at the boundary. Never ask an LLM to handle that envelope; if you ever see
> one in stdout, it means `--b64` was passed explicitly.

### 🔴 Integrity check (HARD GATE · simplified in v1.3.19)

Because the answer now arrives as **plain text**, the whole check collapsed into one
structural question: **is the trailing `<<<CT_ANSWER_END>>>` marker there?**

| # | Observation | Meaning | Action |
|---|---|---|---|
| 1 | Marker + `checksum:` present, body non-empty | Capture complete | Deliver the body verbatim. `checksum:` re-verification is optional here — the marker's presence already proves the capture was not cut. |
| 2 | Marker absent, or `checksum:` line missing | The tool channel truncated the capture | Re-capture the **same** command with Bash / Git Bash. **Do NOT re-run Coze.** |
| 3 | Marker present but checksum mismatch (code below) | Real corruption, not truncation | Do NOT deliver. Report expected vs actual and stop — never loop re-runs. |
| 4 | `--b64` was used (legacy escape hatch) | Base64 envelope | Strip all whitespace, decode, then hash-verify — see code below. |

Re-running without capture evidence is a protocol violation: in the 2026-10-15/16 incidents it
made one question fire 2–3 times, dragging a single Q&A to minutes.

Verification code — only needed for `--b64` or a suspected step-3 mismatch:

```python
import hashlib, re
stdout = "...(entry.py output)..."
MARK = "<<<CT_ANSWER_END>>>"
if MARK in stdout:
    body = stdout.split(MARK, 1)[0]                    # everything before the marker
    expected = re.search(r"checksum:\s*([0-9a-f]{16})", stdout).group(1)
    if hashlib.sha256(body.encode("utf-8")).hexdigest()[:16] != expected:
        print("⚠️ answer integrity check failed")      # do not deliver, do not re-run
    else:
        print(body)                                    # deliver verbatim
```

**If the checksum does not match, the local LLM MUST NOT deliver the answer to the user.** This prevents any silent tampering.

> 🔴 **Capture stdout byte-faithfully (2026-10-22, protocol simplified)**: `entry.py` forces
> UTF-8 on all three streams, so read it in a UTF-8-capable channel. Git Bash / `cmd /c` with
> file redirection / WSL are byte-faithful with no action needed. On a Chinese-Windows
> PowerShell host, set `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` **before**
> invoking it — with plain CJK output this setting is load-bearing again (under the old base64
> envelope it was not).
>
> 🔴 **Fallback for a skipped/mistyped encoding setting (automatic · 2026-10-22)**: because that
> one-line setting is easy to forget or to apply *after* the call (an in-effect-only-for-later-
> commands mistake), `entry.py` **always writes a second, intact copy** of the plain answer to
> `%TEMP%/ct-advisor/last_answer.md` (UTF-8, no BOM, overwritten per call; `--answer-file PATH`
> overrides the location, `--no-answer-file` disables it). If stdout shows `鏈熶复…`-style
> mojibake, or the ASCII warning line `[ct-advisor] WARN: console encoding=…` appears, the run
> itself still SUCCEEDED — **Read that file and deliver from it; never re-run Coze for an encoding
> problem** (a local `session_store` cache hit replays the same answer with **zero** outbound
> calls anyway). Reading the engine's own fallback artifact is sanctioned; hand-rolling a temp-file
> relay for stdout, or re-encoding/re-transporting the answer yourself, is not.
>
> One-line self-check before blaming the skill: `[Console]::OutputEncoding.WebName` must print
> `utf-8`. Note `$OutputEncoding` is a **different** variable (it governs stdin sent to native
> programs) and setting it alone does not help; and the setting is **per-process**, so it must be
> applied in the *same* shell invocation that runs `entry.py`, not in an earlier one.


> 🔴 **No host-model fallback (HARD GATE · 2026-10-15)**: ct-advisor is coze-only **by design** — there is no local knowledge base or database, so a host-model direct answer on a clinical question has no domain substrate and is **forbidden as a fallback** (a bare host-model answer was evaluated and rejected: quality cannot be guaranteed without the cloud knowledge base and tool chain). The same tiering rule means attachment / `doc_context` content must **never** leave the Coze channel. The ONLY sanctioned recovery for a broken capture is: **repair the capture → re-send once (≤1, usually served by the local cache)**. Everything else stops and reports.

> 🔴 **Short-circuit output obeys the same contract (2026-10-15 · unified into `session_store.py` 2026-10-22)**: both short-circuit paths — `session_store.cache_get` (exact-fingerprint answer cache, cross-session) and `session_store.dedup_check` (near-duplicate within a session window) — are wired into **both** the `entry.py` main chain AND the workbench `ct-advisor-proxy.py` (`/run` / `/async_run`). A short-circuited answer leaves `entry.py` through the **same plain-text exit** as a fresh Coze call (stderr marks `answer-cache hit` / `dedup short-circuit`; the proxy returns a local pseudo-task so the front-end is oblivious). A cached answer is a legitimate delivery, not an error.

> 🔴 **Single-run discipline (performance · as mandatory as the HARD GATE)**: `entry.py` is one complete Coze remote call and the main time cost of a single Q&A. The default is **one call per question**. **Re-calling `entry.py` purely to "verify" the output is strictly forbidden** — with the plain-text exit there is nothing left to verify locally. The single exception is decision-table row 2: **at most one re-send to repair a broken CAPTURE**, with the reason stated to the user — never for a checksum mismatch on clean text (row 3 → stop) and never without capture evidence. If you need to persist output, use `entry.py --out <file>` instead of re-running.

**Verification discipline (L3 · 2026-10-22)**: the sha256 check MUST be computed against the stdout of the SAME `entry.py` call, in memory, and only when `--b64` was used or a mismatch is suspected — the trailing marker already proves completeness in the normal path. **Forbidden**: writing stdout to a temp file just for the check, extra tool round-trips, post-hoc temp-file cleanup, and any attempt by the LLM to re-encode or re-transport the answer.

## Performance Optimization & Deployment Notes (L1/L2/L3, 2026-09-26)

This skill has implemented four performance optimizations; see `PERF_SOP.md` for details:
- **L1 Resident orchestration service** (`scripts/serve.py` + `entry.py` client): heavy modules are warmed up once, so local overhead → 0. Idle window raised 600s → 3600s (2026-10-16).
- **L2 Parallel warm-up** (`scripts/orchestrate.py`): eliminates stacked serial imports.
- **L3 Inline verification discipline**: sha256 is computed inline in memory — since 2026-10-22 the check is only needed on the `--b64` escape hatch, because the plain-text exit's trailing marker already proves completeness. Zero LLM round-trips.
- **L4 Single-command + unified session store (2026-10-16 · unified & multi-turn 2026-10-22 · **single path 2026-10-22**)**: `scripts/entry.py` now emits the **final plain-text answer in one call** — no decode step, no second script, and the payload shrinks from 4× (base64 of CJK) back to 1×. `scripts/ask.py` is retained only as a zero-logic forwarder for stale callers. The unified `scripts/session_store.py` (shared by **both** entry.py and the workbench proxy) gives a 30-min cross-session answer cache + a 10-min in-session near-duplicate dedup, so a re-send / repeated question costs **0 Coze calls**; it also injects multi-turn `conversation_history` into the Coze payload so context carries across rounds (previously the history was computed but never injected — root cause of 18% "承接上一轮" manual recaps). Root cause fixed: the `dedup_guard` short-circuit had never been reachable from `entry.py` (guard wired only into the `refine_answer.py` CLI; `query_origin` never set by entry.py), so every re-run was a real Coze round-trip — three of them for a single question in the 2026-10-16 log.
- **L5 Scope broadening via domain router (2026-10-22)**: `scripts/scope_guard.py` was rewritten as a controlled-vocabulary domain router (multi-label: compliance / ops / writing / design / stats / safety / registry / data / rws / methodology / medical / device / vet). The three real high-frequency blocks users actually use — **合规应答 / 项目运营 / 交付物撰写** — are now first-class in-scope core domains (a writing / outline / template question is NO LONGER treated as out-of-scope); only a clearly non-medical / non-life-science question (e.g. consumer electronics, finance, FMCG) emits a constructive referral. 0% out-of-scope on the 68 real questions from the past-30-day Feishu advisorlog.

**⚠️ Deployment restriction (important)**: the skill directory lives on a network share whose ACL is creator-owner — you can create new files, but **overwriting pre-installed existing files raises `PermissionError 13`**, and deletion is also blocked by a trash hook. Therefore, any change to `scripts/*.py` / `SKILL.md` should be written as a same-directory `.new` copy, then overwritten on the user's local machine with `move /Y` (command in `PERF_SOP.md` §4, or run `scripts/_perf_deploy.py`).

**Version drift**: the resident service caches code; after updating skill files, the old service still runs old code until its idle timeout (3600s since 2026-10-16; override with `CT_ADVISOR_IDLE`). `entry.py` has a built-in `/version` probe that, before reusing an old service, compares a **code fingerprint** — the max mtime across `scripts/*.py` + `adapters/**/*.py`, computed by `scripts/code_fingerprint.py` — against the value the service recorded at startup. If the local copy is newer it auto-shuts-down the old service and launches the new version. **No manual restart is ever required.** *(Before 2026-10-16 the probe compared only `orchestrate.py`'s mtime, so updating just `serve.py` or `adapters/**` silently failed to take effect — fixed in the same release.)*

`curl http://127.0.0.1:18771/shutdown` remains available as a manual escape hatch (e.g. the port is held by a stuck service), but it is **not part of any deployment procedure** — end users never need it.

## Session, Context, Cache & Routing Contract (2026-10-22)

Two new local modules close the gaps the past-30-day Feishu advisorlog exposed (no multi-turn context, 21% redundant sends, ~47% of real questions wrongly tagged "out-of-scope" because they were writing/ops/compliance tasks). **Both run purely locally; the Coze payload is enriched, not replaced.**

### A. `scripts/session_store.py` — unified per-session store

Single JSON store at `config/session_store.json` (cross-process file lock: `msvcrt` on Win / `fcntl` on POSIX; atomic replace; any exception silently degrades to "no-hit / no-record" so it never blocks the main flow). Three capabilities keyed by `session_id`:

| Capability | API | Policy |
|---|---|---|
| Multi-turn context | `history(session_id)` → `[{question, answer_summary}]` | Injected as `conversation_history` into the Coze payload. Pruned by OR-rule: ≤10 rounds **OR** ≤2h, hard cap 24h. Empty `session_id` → single-turn (no history, still global cache). |
| Answer cache | `cache_get(question, doc_context, difficulty)` | Exact sha256 fingerprint (question+attachment+difficulty), 30-min TTL (`CT_ADVISOR_ANSWER_TTL`), **cross-session** — same question anywhere returns the same answer, 0 Coze calls. |
| Near-dup dedup | `dedup_check(session_id, question)` → `(is_dup, prev_answer, secs_ago)` | Same session, 10-min window, `difflib.SequenceMatcher.quick_ratio ≥ 0.90`; on hit the caller short-circuits and replays `prev_answer`. |
| Record | `record(session_id, question, answer, …)` | Called **only after a real outbound** (never on a short-circuit) — writes history + global cache + session dedup. `clear_session(session_id)` starts a fresh session (keeps global cache). |

`entry.py` wires all three in `main()` (via `--session <id>`); the workbench `ct-advisor-proxy.py` imports the same module for `/run` and `/async_run`.

### B. `scripts/scope_guard.py` — domain router (replaces the old out-of-scope gate)

Controlled-vocabulary, multi-label classifier (`classify_domains(q)` → up to 3 of: `compliance / ops / writing / design / stats / safety / registry / data / rws / methodology / medical / device / vet`). `assess(q) → (in_scope, tag, referral)`:

- any domain hit **or** a weak life-science signal → in-scope (no referral);
- only a **clearly non-medical** signal (consumer electronics / finance / FMCG / real-estate / …) → out-of-scope with a **constructive** referral that names the coverage and suggests a next step (never a blank refusal).

The router writes two payload hints consumed by Coze (see C): `scope_hint` (only when out-of-scope) and `domain_hint` (the multi-label list). 15/15 offline selftest pass; **0% out-of-scope on the 68 real advisorlog questions**.

### C. Coze payload contract (request fields the engine should accept)

| Field | Set by | Meaning |
|---|---|---|
| `conversation_history` | entry.py / proxy (`session_store.history`) | Prior rounds (question + answer summary) so the engine can resolve "承接上一轮 / 继续" without the user re-typing context. **Front-end may also send its own `conversation_history`; the proxy injects the server-side one only when the field is absent.** |
| `scope_hint` | proxy (`scope_guard.assess`) | `"non_medical"` only when out-of-scope — engine should prepend the referral framing. |
| `domain_hint` | proxy (`scope_guard.classify_domains`) | e.g. `["compliance","ops"]` — lets the engine bias retrieval / sibling-skill routing. |
| `query_meta.output_format` | front-end (`auto/doc/outline/table/ppt`) | 期望答案形态；`doc`=交付物撰写模式（解除 C3 长度天花板、允许 `##`/`###`+表格），引擎现已按形态作答 |
| `session_id` | front-end (`X-Session-Id` header) **or** body | Stable per-machine id (mirrors `query_origin`); drives history + dedup. |

**Coze 侧已在本轮实现 `output_format=doc` 模式**（用户 2026-10-22 确认「方案 A：长文本 + 导出按钮」）：`full_analysis_node` 把 `query_meta.output_format` 注入提示词（此前从未进入，五选项仅 `auto` 生效）、doc 模式跳过 C14「不提供文件」声明、走 6000 字防御性安全天花板；`shared_contract.md` 与 `full_analysis_cfg.json` 的 `sp` 增加 C3-doc 条款。上下文/缓存/去重仍由 proxy 本地富化与短路，引擎仅收到更丰富的请求。本地侧另新增 `POST /api/export_docx`（零依赖 OOXML 生成）与前端的「📄 导出 docx」按钮——文件在本地生成、不回传云端，与 C14「引擎不返文件」不冲突。详见 `docs/answer_length_format_deviation_20261022.md`。

### D. Workbench proxy local endpoints (no Coze round-trip)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/history?session_id=` | GET | Returns `{ok, history:[{question, answer_summary}]}` from `session_store`. |
| `/api/turn` | POST | `{session_id, question, answer, doc_context, query_meta}` → `session_store.record(...)` (called by the front-end after a successful answer). |
| `/api/feedback` | POST | `{session_id, run_id, rating, note}` → appends a `type=rating` line to `workbench/feedback_log.jsonl` (satisfaction signal, local only). |
| `/api/export_docx` | POST | `{text, title}` → returns a stdlib-generated OOXML `.docx` as an attachment (local only; the cloud engine still returns text only, so C14 holds). |

Short-circuit return shape: cache/dedup hit on `/async_run` returns `{"task_id": <local>}`; on `/run` returns `{"result":{final_answer, cache_hit:true}}`; `/stream_run` is **never** short-circuited (it streams, proxy only injects context).

## Capability Domains — Expanded Coverage (2026-10-22)

Coverage was broadened per user mandate: the three previously-uncovered but high-frequency real-user blocks — **合规应答 / 项目运营 / 交付物撰写** — are now first-class in-scope core domains (mapped to `scope_guard` labels `compliance` / `ops` / `writing`). They are **never** empty-refused; only clearly non-medical / non-life-science questions get a constructive referral. Full sub-topic catalog + authoritative anchors (ICH / NMPA / CDE / TransCelerate / DIA / CASRAI / EQUATOR, searched 2026-10-22) live in **`docs/capability_domains.md`**. Summary:

| Domain (label) | What the advisor answers | Key authoritative anchors |
|---|---|---|
| 合规应答 `compliance` | GCP 原则与适用、中国 GCP 落地、核查/稽查 readiness、方案偏离与 CAPA、安全性报告、登记与信息公示（CTR 号 + 30 天时限）、监管函件/沟通交流、知情同意与弱势受试者保护 | ICH E6(R3) 11 原则（2025-07-23 生效）· NMPA GCP 2020 第 57 号 · CDE《登记与信息公示管理规范》2020 第 9 号 + 平台 chinadrugtrials.org.cn |
| 项目运营 `ops` | 研究中心启动、TMF / 必备文件（DIA TMF Reference Model v3 + MAGI ISF）、监查模式（RBM / 中心化 / hybrid）、RBQM（QTL 1–5 / KRI 10–25、CtQ 因素）、供应商/CRO 管理、入组留存、关中心与 DBL | TransCelerate RBM & QTL Framework · DIA TMF RM (tmfrefmodel.com) · ICH E8(R1) · CASRAI TMF 指南 |
| 交付物撰写 `writing` | 方案（CPT/eCPT）、SAP（ICH E9(R1) 估计目标五属性 + Gamble 55 项清单）、CSR、IB、ICF、器械文档（ISO 14155）、登记类文件 | TransCelerate CC&R（2026 对齐 ICH M11）· ICH E9(R1) · EMA addendum · CASRAI SAP 模板 · EQUATOR |

Assistance boundaries (enforced in-engine, documented in the doc): ✅ explain clauses / give decision frameworks / checklists / templates; ⚠️ never substitute legal, regulatory, or medical-writing conclusions — route to `ct-registry` / `ct-stats` / `ct-samplesize` / submission path as noted. The three domains are **locally routed**; Coze only needs to honour `domain_hint`.

## Requirements

| Item | Requirement |
|---|---|
| Runtime | `python3` stdlib only |
| Sibling skills | **Tier A · listed on SkillHub** (non-confidential input, publicly released): `ct-registry` / `ct-safety` / `ct-literature` / `ct-samplesize` — auto-routed via Coze `need_tool` (entry.py handles card-inline execution). **Tier A · NOT yet listed**: `ct-pipeline` / `ct-synthdata` → `unpublished_a`, answer from Coze draft. **Tier B** (confidential input, **not publicly released**): `ct-protocol` / `ct-csr` / `ct-analysis` / `ct-sdtm` / `ct-eligibility` etc. — never installable. |
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

## Quality Gate & Stop Rules

**Presentation rules (user-mandated, hard)** — deliver only the plain-text answer printed by `scripts/entry.py` (everything above the trailing `<<<CT_ANSWER_END>>>` marker). **Never emit any workflow / process narration to the user.**

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

## AI 生成治理（ct-base §22）

> 本技能受 `ct-base/BASE.md §22`（AI 生成资产治理，2026-10-18 新增）约束。来源依据：`ct-base/references/cdisc2026_ai_challenge.md`。作为总入口路由，本技能是 §22.5（ALCOA+ 审计 + 版本锁定）与 §22.6（Control Mode 自治阶梯）的主要承载。

| §22 义务 | 适用项 | 本技能状态 |
|---|---|---|
| §22.5 ALCOA+ 审计 | basis + processDefinitionVersion | 🟡 规划——每次 AI 建议须落 `basis`（基于什么规则/数据源）+ `processDefinitionVersion`；引用 `ct-base/assets/audit_event.schema.json` |
| §22.5 工作流版本锁定 | skill_version / coze_version | 🟢 已部分——coze 出参已带 `skill_version` + `coze_version`（§20.13）；须扩展到每次路由决策的 `processDefinitionVersion` |
| §22.6 Control Mode 自治阶梯 | CM0–CM4 每步配置 | 🔴 规划——路由须把每步的 Control Mode 显式写入定义；风险点（AI 建议采纳）默认 CM3，确定性调度 CM0，绝不默认 CM4 处理涉监管资产 |
| §22.1 HITL 闸门 | 生成前 gate | 🟡 部分——已设人工确认门（与下游技能 §6.9 协同）；须显式化"歧义即停"触发清单 |
| §22.15 影子模式准入阈值 | CM 升级量化闸门 | 🔴 规划——总入口路由/建议能力升级 Control Mode 前须过影子阶段（锁定版本 + 与人工基准决策离线比对），由技能负责人定义量化阈值（性能/稳定性/时效），全达标才升级，触发熔断即降回 CM3；**扩写（AI-201 落地建议 #5/#6）**：影子期与传统人工路由并行对跑积累一致性证据；SAP 登记模型版本 + skill 版本 + 规则集版本三要素 |
| §22.16 RAG 三列待核对清单 | 问题 / 原文位置 / 依据 | 🔴 规划——路由/问答输出的检索类内容（指南、SOP、方案初审）禁止只给结论，必须附三列待核对清单；"漏项"显式列出（依据：Waikar et al. 2026 CPT PSP，DOI `10.1002/psp4.70201`——RAG 概念验证漏掉方案主要终点、带入不适用要求） |
| §22.18 规格就绪度 Gate 传播 | 路由到生成类技能前确认 | 🔴 规划——总入口把 spec/规格类请求路由给 ct-sdtm/ct-adam/ct-tlf 等生成技能前，先提示调用方过六项就绪度评分；规格缺项直接退回上游作者，不转发（§22.18；AI-201 Gate 1 范式） |

**红线**：AI 建议须可审计（basis + 版本）；自治级必须显式配置，禁止隐含 CM4（§22.7）。
