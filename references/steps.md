---
file: steps.md
version: 2026-08-08
purpose: ct-advisor Answer Workflow step definitions — the SKILL.md step summary maps to this file's full flow, boundary conditions, and exception handling
---

# Answer Workflow — Steps 0-6 (Detailed)

> **Core principle**: payload always travels through the in-memory pipeline (`--payload-inline` or stdin), **never** Write/Bash temp JSON files.

---

## Step 0 — Triage (Gate 0)

**Goal**: classify difficulty + run pre-routing interception, deciding the downstream path.

| difficulty | trigger | downstream path |
|---|---|---|
| `simple` | single fact / definition / standard operation, no data pull or n computation | → step 1→2→6 (race mode; **Step 1 fire-only fires IMMEDIATELY after Triage, before Route**) |
| `middle` | needs explanation / comparison / multi-step reasoning, but no external data | → step 1→2→6 (race mode; **Step 1 fire-only fires IMMEDIATELY after Triage, before Route**) |
| `complex` | needs multi-angle decomposition, external data integration, or option selection | → step 2→3→4→5→6 (**serial**, await full Coze return; Step 1 Fire is race-only, skipped for complex) |
| `vague` | incomplete / ambiguous question, missing key parameters | → AskUserQuestion (≤ 4 questions) → back to step 0 |

**⚠️ Pre-routing interception (mandatory)**: when classifying difficulty, analyze the intent of `original_question` — if it requires calling an external skill for data (ct-registry / ct-safety / ct-literature → step 3 handoff) or computing sample size / power (→ step 4 handoff), **difficulty MUST NOT be simple/middle; only complex is allowed** (vague never reaches this gate). Reason: data pull / n computation depends on real external output and must await Coze's full return to integrate into the answer; a race-mode local fallback would lose that data.

**🔴 Difficulty bias rule (guardrail against misjudging as complex)**:

When the question **does not involve external data pull / sample size computation**, prefer `middle` (over `complex`) unless at least one of the following holds:
- requires pulling data from ≥1 sibling skill simultaneously (data grounding ≥1 route)
- requires ct-samplesize to compute n / power
- question explicitly asks for multi-option comparison + recommendation ("which one / best approach")
- composite judgment spanning ≥2 workflows

**Pure methodology questions (e.g., "how to do X", "what to watch for in X", "difference between X and Y") are always `middle`** — the local knowledge pack covers 80%+ of the content; in race mode the Coze-refined output is the final answer, no serial wait needed.
**Typical misjudgment example**: "How to ensure data integrity when migrating from paper CRF to EDC?" → although multi-step, the local knowledge pack (ref-ops-data §4.12) has complete guidance and no external data is needed → should be judged `middle` (race), not `complex` (serial).

**🚫 Anti-shortcut warning (HARD GATE)**: **simple/middle MUST run the full step 1→2→6 flow (fire BEFORE route); complex MUST run the full step 2→3→4→5→6 flow. Do NOT use any of the following "invisible pre-judgments" to skip steps:**
- ❌ "the knowledge base already has a clear answer, just retrieve and output it"
- ❌ "search_refs.py found it, no need to refine"
- ❌ "the question is too simple, Coze would just repeat"
- ❌ "the local answer is good enough, no need to wait for Coze"

**Coze is the referee, not the backup**: the race design lets Coze and the local answer run in parallel, with the winner outputting — **not letting the agent pre-judge "Coze is useless" and skip it.**

**Interaction strategy**:
- `simple` → answer directly (meaning: don't pop a clarification menu first; Coze refinement still requires step 1 fire-only, no exemption)
- `complex` → show the clarification menu (`scripts/menu.json` via `scripts/i18n.py`)
- `vague` → grill-me style `AskUserQuestion` (≤ 4 questions)
- when unsure between simple/middle/complex → brief direct answer + optional deep-dive menu

---

## Step 1 — Fire Gate

**Goal**: 🔴 for `simple`/`middle`, fire the Coze refinement request in the background **IMMEDIATELY after Step 0 Triage — BEFORE Step 2 local retrieval**. This is the single most important latency gate: Coze (≈20s) must start racing the local loop from T+0, not after Route / pre-reading.

| difficulty | behavior |
|---|---|
| `simple`/`middle` | 🔴 **HARD GATE**: **immediately** fire `refine_answer.py --fire-only` via background (`run_in_background`, stdin pipe), passing `original_question` + `query_meta.difficulty` (the Triage-judged `simple`/`middle`); leave `category`/`accuracy`/`draft_answer` empty. **No temp files**; **do not skip this step and write the local answer directly**. |
| `complex` | do not fire; await the serial call in step 5. |

> 🔴 **Key**: this step is the start of race mode and MUST execute right after Triage. simple/middle MUST fire fire-only here (before any local retrieval), so Coze is already computing while the agent does local work; by Step 2 `--collect` it is very likely already back (cache hit → verbatim ship). Firing late (after Route / pre-reading knowledge) is the #1 measured latency failure mode.

> 🔴 **出站授权门控（自动执行）**：`--fire-only` 出站前由脚本自动检查授权：
> - 端点在 `config.json` `auto_approve_endpoints` 白名单中 → 直接放行
> - 本会话已授权过 → 直接放行（脚本内存记忆）
> - 未授权 → 脚本返回空串（本地胜出），agent 应提示用户确认后将端点加入白名单

---

## Step 2 — Collect + Route + Local Answer (race core)

**Goal**: 🔴 The single most important race step. **Begin by calling `--collect --wait=race_window` (the main blocking point)**; do lightweight local work (Route match + prepare fallback) *within* the collect wait window. Coze hit → verbatim ship (see HARD GATE below); timeout → use local fallback.

### Race mode (simple/middle)

```
step 1 fired fire-only → Coze running in background
step 2 begins → main agent FIRST calls --collect --wait=race_window (main blocking point)
               ├─ Coze returns within window → **adopt Coze VERBATIM** → step 6
               └─ window exhausts, Coze not back → agent writes local answer
                     (Route match A–J from scripts/workflows.json + conclusion-first regulatory citations) → step 6
```

- 🔴 **HARD GATE (post-collect zero-processing)**: the instant `--collect` returns a cache hit, output the Coze stdout **as-is** — no re-write, no re-order, no injecting `knowledge/` citations the Coze output lacked, no re-formatting, no appended "local summary". Re-synthesis after Coze returns is the #2 measured latency failure mode. Ship Coze, full stop.
- 🔴 **Route is a window-internal side task, NEVER a blocker**: `fire-only` needs only `original_question`; the Route result is irrelevant to Coze. Do NOT read `workflows.json` / `knowledge/` *before* firing (Step 1) — and do NOT let Route retrieval delay the collect call. If local retrieval would take long, it only matters as fallback; Coze (≈20s) almost always wins, so the user never waits for the full local retrieval.
- Coze HTTP timeout = full 60s (`refiner.timeout`)
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

**Output**: await Coze's refined result; on timeout return local answer + external data results 1 and 2.

> 🔴 **出站授权门控（自动执行）**：串行精校出站前由脚本自动检查授权（同 Step 1 规则）。未授权时直接回退本地草稿，agent 应提示用户确认。

```
step 2 local answer + step 3/4 external data → foreground serial call to refine_answer.py (with draft_answer)
              ├─ Coze returns within 60s → adopt Coze result
              └─ Coze fails / times out  → fall back to local answer + external data
```

### Serial call style (stdin pipe preferred)

```bash
# Bash / Git Bash — stdin pipe (zero encoding risk; handles Chinese punctuation in draft_answer)
echo '{"original_question":"…","draft_answer":"…"}' | python scripts/refine_answer.py

# PowerShell here-string (recommended, no escaping needed)
@'
{"original_question":"…","draft_answer":"…"}
'@ | python scripts/refine_answer.py
```

---

## Step 6 — Final answer (Final Output)

**Goal**: return the final answer to the user. **Note: this step does almost no answer processing; it only returns the answer directly.**

| mode | source |
|---|---|
| Race (simple/middle) | the result from step 2 |
| Serial (complex) | the result from step 5 |

**Output**: the formal result returned to the user.

### 🔴 Final pre-output check (HARD GATE)

Before outputting **any** answer content, confirm item by item:

| difficulty | check items |
|---|---|
| `simple`/`middle` | ☐ **Step 1 fired Coze fire-only** (the most easily skipped gate) → ☐ step 2 already collected → ☐ winner decided → output = winner content |
| `simple`/`middle` (fallback) | ☐ if `--collect` errored / failed / returned empty → local answer adopted, **no appended Coze wait** |
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
