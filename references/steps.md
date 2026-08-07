---
file: steps.md
version: 2026-08-07
purpose: ct-advisor Answer Workflow step definitions — the SKILL.md step summary maps to this file's full flow, boundary conditions, and exception handling
---

# Answer Workflow — Steps 0-7 (Detailed)

> **Core principle**: payload always travels through the in-memory pipeline (`--payload-inline` or stdin), **never** Write/Bash temp JSON files.

---

## Step 0 — Triage (Gate 0)

**Goal**: classify difficulty + run pre-routing interception, deciding the downstream path.

| difficulty | trigger | downstream path |
|---|---|---|
| `simple` | single fact / definition / standard operation, no data pull or n computation | → step 1→2→3→7 (race mode; **Step 2 MUST be fire-only, never skip Coze**) |
| `middle` | needs explanation / comparison / multi-step reasoning, but no external data | → step 1→2→3→7 (race mode; **Step 2 MUST be fire-only, never skip Coze**) |
| `complex` | needs multi-angle decomposition, external data integration, or option selection | → step 1→2→3→4→5→6→7 (**serial**, await full Coze return) |
| `vague` | incomplete / ambiguous question, missing key parameters | → AskUserQuestion (1–3 questions) → back to step 0 |

**⚠️ Pre-routing interception (mandatory)**: when classifying difficulty, analyze the intent of `original_question` — if it requires calling an external skill for data (ct-registry / ct-safety / ct-literature → step 4 handoff) or computing sample size / power (→ step 5 handoff), **difficulty MUST NOT be simple/middle; only complex is allowed** (vague never reaches this gate). Reason: data pull / n computation depends on real external output and must await Coze's full return to integrate into the answer; a race-mode local fallback would lose that data.

**🔴 Difficulty bias rule (guardrail against misjudging as complex)**:

When the question **does not involve external data pull / sample size computation**, prefer `middle` (over `complex`) unless at least one of the following holds:
- requires pulling data from ≥1 sibling skill simultaneously (data grounding ≥1 route)
- requires ct-samplesize to compute n / power
- question explicitly asks for multi-option comparison + recommendation ("which one / best approach")
- composite judgment spanning ≥2 workflows

**Pure methodology questions (e.g., "how to do X", "what to watch for in X", "difference between X and Y") are always `middle`** — the local knowledge pack covers 80%+ of the content; in race mode the Coze-refined output is the final answer, no serial wait needed.
**Typical misjudgment example**: "How to ensure data integrity when migrating from paper CRF to EDC?" → although multi-step, the local knowledge pack (ref-ops-data §4.12) has complete guidance and no external data is needed → should be judged `middle` (race), not `complex` (serial).

**🚫 Anti-shortcut warning (HARD GATE)**: **simple/middle MUST run the full step 1→2→3→7 flow; complex MUST run the full step 1→2→3→4→5→6→7 flow. Do NOT use any of the following "invisible pre-judgments" to skip steps:**
- ❌ "the knowledge base already has a clear answer, just retrieve and output it"
- ❌ "search_refs.py found it, no need to refine"
- ❌ "the question is too simple, Coze would just repeat"
- ❌ "the local answer is good enough, no need to wait for Coze"

**Coze is the referee, not the backup**: the race design lets Coze and the local answer run in parallel, with the winner outputting — **not letting the agent pre-judge "Coze is useless" and skip it.**

**Interaction strategy**:
- `simple` → answer directly (meaning: don't pop a clarification menu first; Coze refinement still requires step 2 fire-only, no exemption)
- `complex` → show the clarification menu (`scripts/menu.json` via `scripts/i18n.py`)
- `vague` → grill-me style `AskUserQuestion` (≤ 3 questions)
- when unsure between simple/middle/complex → brief direct answer + optional deep-dive menu

---

## Step 1 — Route

**Goal**: match a workflow A–J (or composite route) from `scripts/workflows.json`.

- methodology / design / GCP / compliance / QC / statistics → local `knowledge/` workflow
- registered-trial landscape / safety signals / literature → mark step 4 data-trigger
- sample size / power → mark step 5 handoff trigger

---

## Step 2 — Fire Gate

**Goal**: based on difficulty, decide whether to immediately fire the Coze refinement request in the background, starting the race.

| difficulty | behavior |
|---|---|
| `simple`/`middle` | 🔴 **HARD GATE**: **immediately** fire `refine_answer.py --fire-only --payload-inline '{…}'` via background (`run_in_background`), containing only `original_question` (with `draft_answer` left empty). **No temp files**; **do not skip this step and write the local answer directly**. |
| `complex` | do not fire; await the serial call in step 6. |

> **Key**: this step is the start of race mode. simple/middle MUST fire fire-only here, so that when entering step 3, Coze is already computing the answer.

---

## Step 3 — Local Answer

**Goal**: collect Coze result first; if Coze returns within the window, use it verbatim—otherwise write the local answer as fallback. **When Coze wins, output Coze verbatim — do NOT re-synthesize or merge with the local fallback.**

### Race mode (simple/middle)

```
step 2 fired fire-only → Coze running in background
step 3 begins  → main agent first --collect --wait=race_window (wait for Coze, capped at race_window seconds)
               ├─ Coze returns within window → **adopt Coze VERBATIM** → step 7
               └─ window exhausts, Coze not back → main agent writes local answer (conclusion first + regulatory citations) → step 7
```

- Coze HTTP timeout = full 60s (`refiner.timeout`)
- race_window = 30s (config.json `refiner.race_window`; caller can override with `--wait N`)
- **once the winner is decided → jump directly to step 7 and output the final answer**
- **⚠️ --collect MUST pass complete payload**: the cache path is derived from the hash of original_question + query_meta; without the payload the cache cannot be located. When the agent calls --collect in step 3, it MUST pass the same payload from step 2 (or at least the minimal payload containing original_question), otherwise the script fails JSON parsing → local win (but wastes one tool call)

### Serial mode (complex)

- write the complete local answer (conclusion first + regulatory citations + concise); do NOT call `--collect`
- the answer becomes the input to step 6 serial refinement

### query_meta self-assessment

`accuracy` = `good` (precise regulatory citations) or `normal` (generic answer).

---

## Step 4 — External data 1 (Data Grounding, on demand)

**Goal**: pull real data from external skills to support the answer.

**Trigger**: only when step 1 marked a data route (ct-registry / ct-safety / ct-literature).

**Action**:
1. read sibling-skill output (configured in `workflows.json` as `integration.data_grounding`)
2. label "Data source: ct-xxx on <date>"
3. pure-methodology questions may skip (label "no data grounding performed")

**Note**: keep it light; Coze handles expansion and integration.

---

## Step 5 — External data 2 / sample-size handoff (Handoff, on demand)

**Goal**: hand a complete parameter framework to `ct-samplesize`; this skill does NOT compute n.

**Trigger**: step 1 marked workflow C parameters ready.

**Payload**: design type, comparator, test (α/power), effect size, dropout rate.

---

## Step 6 — Send to Coze for refinement (Serial Refine)

**Goal**: send the local answer to Coze to produce the final answer.

**Trigger**: `complex` difficulty.

**Input**: local answer + external data results 1 and 2.

**Output**: await Coze's refined result; on timeout return local answer + external data results 1 and 2.

```
step 3 local answer + step 4/5 external data → foreground serial call to refine_answer.py (with draft_answer)
              ├─ Coze returns within 60s → adopt Coze result
              └─ Coze fails / times out  → fall back to local answer + external data
```

### Serial call style (`--payload-inline` preferred)

```bash
# Bash / Git Bash (JSON wrapped in single quotes; inner double quotes NOT escaped)
python scripts/refine_answer.py --payload-inline '{"original_question":"…","draft_answer":"…"}'

# PowerShell (JSON wrapped in double quotes; inner \" escaped)
python scripts/refine_answer.py --payload-inline '{\"original_question\":\"…\",\"draft_answer\":\"…\"}'

# PowerShell here-string (recommended, no escaping needed)
@'
{"original_question":"…","draft_answer":"…"}
'@ | python scripts/refine_answer.py
```

---

## Step 7 — Final answer (Final Output)

**Goal**: return the final answer to the user. **Note: this step does almost no answer processing; it only returns the answer directly.**

| mode | source |
|---|---|
| Race (simple/middle) | the result from step 3 |
| Serial (complex) | the result from step 6 |

**Output**: the formal result returned to the user.

### 🔴 Final pre-output check (HARD GATE)

Before outputting **any** answer content, confirm item by item:

| difficulty | check items |
|---|---|
| `simple`/`middle` | ☐ **Step 2 fired Coze fire-only** (the most easily skipped gate) → ☐ step 3 already collected → ☐ winner decided → output = winner content |
| `simple`/`middle` (fallback) | ☐ if `--collect` errored / failed / returned empty → local answer adopted, **no appended Coze wait** |
| `complex` | ☐ step 6 already called Coze serially in foreground (with draft_answer) or timed out and fell back → output = winner content |
| in-session follow-up (not a new question) | ☐ step 0 classified as **not a new question** (a follow-up / clarification on an existing answer) → output local answer directly (difficulty no longer constrained) |

**Any unchecked item → forbidden to output content; must roll back and complete the missing step.**

---

## Call-style summary (zero temp files · cross-platform safe)

| priority | style | command template | when to use |
|---|---|---|---|
| **1 (preferred)** | `--payload-inline` | `python refine_answer.py --payload-inline '{…}'` | **all** fire-only and serial calls |
| **2** | stdin pipe | `echo '{…}' \| python refine_answer.py` | serial with long payload |
| **3 (fallback)** | file path | `python refine_answer.py /path/to/file.json` | **only** `--collect` (legacy compat) |

**Forbidden**:
- ❌ `Write`/`Bash cat >` to write temp JSON files (encoding risks: Chinese quotes / BOM / line endings)
- ❌ `/tmp` paths (Git Bash ↔ Python path mismatch under Windows)
- ❌ file paths in fire-only / serial (completely unnecessary)

**Encoding strategy (with `--payload-inline`)**:
- **Bash / Git Bash**: wrap JSON in **single quotes** (`'{"key":"中文"}'`), inner double quotes **NOT escaped**
- **PowerShell**: wrap JSON in **double quotes** + `\"` escaping; or use here-string `@'…'@` (no escaping needed)
- **cmd.exe**: same as PowerShell
