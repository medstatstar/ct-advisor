---
file: steps.md
version: 2026-08-09
purpose: ct-advisor Answer Workflow step definitions — the SKILL.md step summary maps to this file's full flow, boundary conditions, and exception handling
---

# Answer Workflow — Steps 0-6 (Detailed)

> **Core principle**: payload always travels through the in-memory pipeline (`--payload-inline` or stdin), **never** Write/Bash temp JSON files.

---

## Step 0 — Triage (Gate 0)

**Goal**: classify difficulty + run pre-routing interception, deciding the downstream path.

| difficulty | trigger | downstream path |
|---|---|---|
| `simple` | single fact / definition / standard operation, no data pull or n computation | → step 2→6 (**local-only**, no Coze; answered directly from `knowledge/`, Step 1 skipped) |
| `middle` | needs explanation / comparison / multi-step reasoning, but no external data | → step 1→2→6 (race mode; **Step 1 fire-only fires IMMEDIATELY after Triage, before Route**) |
| `complex` | needs multi-angle decomposition, external data integration, or option selection | → step 2→3→4→5→6 (**serial**, await full Coze return; Step 1 Fire is race-only, skipped for complex) |
| `vague` | incomplete / ambiguous question, missing key parameters | → AskUserQuestion (≤ 4 questions) → back to step 0 |

**⚠️ Pre-routing interception (mandatory)**: when classifying difficulty, analyze the intent of `original_question` — if it requires calling an external skill for data (ct-registry / ct-safety / ct-literature → step 3 handoff) or computing sample size / power (→ step 4 handoff), **difficulty MUST NOT be simple/middle; only complex is allowed** (vague never reaches this gate). Reason: data pull / n computation depends on real external output and must await Coze's full return to integrate into the answer; a race-mode local fallback would lose that data.

**🔴 Difficulty bias rule (guardrail against misjudging as complex)**:

When the question **does not involve external data pull / sample size computation**, prefer `simple` or `middle` (over `complex`) unless at least one of the following holds:
- requires pulling data from ≥1 sibling skill simultaneously (data grounding ≥1 route)
- requires ct-samplesize to compute n / power
- question explicitly asks for multi-option comparison + recommendation ("which one / best approach")
- composite judgment spanning ≥2 workflows

**Pure methodology questions (e.g., "how to do X", "what to watch for in X", "difference between X and Y") are always `simple` or `middle` (never `complex`)** — the local knowledge pack covers 80%+ of the content: `simple` answers directly from `knowledge/` (local-only, no Coze); `middle` runs race mode (Coze-refined output is the final answer, no serial wait). Among them: **single fact / definition / standard operation → `simple`**; explanation / comparison / multi-step reasoning → `middle`.
**Typical misjudgment example**: "How to ensure data integrity when migrating from paper CRF to EDC?" → although multi-step, the local knowledge pack (ref-ops-data §4.12) has complete guidance and no external data is needed → should be judged `middle` (race), not `complex` (serial).

**🚫 Anti-shortcut warning (HARD GATE)**: **`middle` MUST run the full step 1→2→6 flow (fire BEFORE route); `complex` MUST run the full step 2→3→4→5→6 flow; `simple` runs step 2→6 local-only (Step 1 skipped, no Coze).** Do NOT use any of the following "invisible pre-judgments" to skip steps (applies to `middle`/`complex`; `simple` is local-only by design, not a shortcut):
- ❌ "the knowledge base already has a clear answer, just retrieve and output it"
- ❌ "search_refs.py found it, no need to refine"
- ❌ "the question is too simple, Coze would just repeat"
- ❌ "the local answer is good enough, no need to wait for Coze"

**Coze is the referee, not the backup**: the race design lets Coze and the local answer run in parallel, with the winner outputting — **not letting the agent pre-judge "Coze is useless" and skip it.**

**Interaction strategy**:
- `simple` → answer directly from local `knowledge/` (don't pop a clarification menu first; **no Coze — local-only mode, Step 1 skipped entirely**)
- `complex` → show the clarification menu (`scripts/menu.json` via `scripts/i18n.py`)
- `vague` → grill-me style `AskUserQuestion` (≤ 4 questions)
- when unsure between simple/middle/complex → brief direct answer + optional deep-dive menu

---

## Step 1 — Fire Gate

**Goal**: 🔴 for `middle`, fire the Coze refinement request in the background **IMMEDIATELY after Step 0 Triage — BEFORE Step 2 local retrieval**. This is the single most important latency gate: Coze (≈20s) must start racing the local loop from T+0, not after Route / pre-reading. `simple` never enters this step (local-only — see Step 2 Local-only mode).

| difficulty | behavior |
|---|---|
| `simple` | **skipped (local-only)** — never fire Coze; go straight to Step 2 local answer. No outbound call, no authorization gate. |
| `middle` | 🔴 **HARD GATE**: **immediately** fire `refine_answer.py --fire-only` via background (`run_in_background`, stdin pipe), passing `original_question` + `query_meta.difficulty` (the Triage-judged `middle`); leave `category`/`accuracy`/`draft_answer` empty. **No temp files**; **do not skip this step and write the local answer directly**. |
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

> 🔴 **Outbound Authorization Gate (auto-executed)**: the script checks authorization automatically before the serial refinement outbound call (same rules as Step 1). If unauthorized, it falls back to the local draft directly; agent should prompt the user to confirm.

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
