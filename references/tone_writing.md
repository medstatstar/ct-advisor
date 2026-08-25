# Tone Writing — ct-advisor personalized output

> ⚠️ **DEFERRED (2026-08-12)**: this feature is **temporarily disabled** — the deployed Coze workflow (v1.5 contract) does not implement the `tone_profile` field, so injection is silently ignored. `tone_matcher.py` and `refine_answer.py --tone` must **not** be invoked until the Coze workflow ships the v1.6 contract fields. Spec retained for future re-enable.

> Upgrade item: **P0-B · clarify_loop enhancement: user tone-writing mode**
> Implementation: `scripts/tone_matcher.py` + `refine_answer.py --tone` + contract field `tone_profile`

## Purpose

ct-advisor's default output follows the canonical tone of the deployed Coze system prompt (de-AI-ified, first-use acronym annotations, trimmed weak-advice words; the local contract snapshot lives under the cloud-deployment workspace, not in this skill). Different users have different writing habits — some prefer short colloquial sentences, some long formal ones, some like to build closeness with "you / we". Tone writing lets the user **provide their own writing samples**; the skill extracts the expression style and writes answers in a consistent voice.

## How it works (pure local, no network call)

```
user samples (article / email / report excerpts)
        │  scripts/tone_matcher.py
        ▼
tone_profile.json   (expression style only, no facts)
        │  refine_answer.py --tone tone_profile.json
        ▼
Coze refinement prompt (tone_profile shipped with the contract)
        ▼
final_answer written in the user's voice
```

## Extracted style features

`tone_profile.features` contains **style dimensions only — no facts**:

| Field | Meaning |
|---|---|
| `sentence_length` | short / medium / long (average sentence length) |
| `formality` | formal / semi-formal / casual |
| `second_person` | whether "you (你/您)" is used frequently |
| `first_person` | whether "I / we (我/我们)" is used frequently |
| `paragraph_avg_chars` | average paragraph length in characters |
| `uses_lists` | whether lists / bullet points are used |
| `rhetoric` | rhetoric devices (rhetorical question / parallel structure / example / enumerated points) |
| `transitions` | common connectives (style layer) |
| `term_style` | first-use annotation / acronym-first / mixed |
| `emoji` | whether emoji is used |
| `punctuation` | full-width / half-width |

## 🔴 Hard gate (HARD GATE, non-bypassable)

**Only expression style is migrated — factual content is NEVER migrated.**

- At extraction time `tone_matcher.py` uses regex to strip dates, project / study names, institution names, person names, and metric numbers — **these facts never enter `features`** (only recorded in `_factual_leak_warning` for human audit).
- A style hard-gate instruction is attached on injection into Coze: `[HARD GATE] only use the expression style above; do NOT copy dates / projects / people / opinions / numbers from the samples`.
- The Coze-side contract (v1.6 §Input / rule 6) states: `tone_profile` is used **only** for expression style, **never** to reuse sample facts; if style is absent, fall back to the default canonical tone.

Rationale: user samples may contain stale information (old projects, old data, old opinions); copying them verbatim would pollute the current answer.

## Usage

```bash
# 1) Extract a style profile from writing samples (--samples-inline takes a JSON array; --samples-file splits by blank line)
python scripts/tone_matcher.py \
  --samples-inline '["你看看这个设计，其实吧，关键在于把握度。比如 power 设 0.9 就好。", "咱们先算样本量，再定方案。"]' \
  --out tone_profile.json

# 2) Inject on refinement (--tone takes the profile path)
echo '{"query_meta":"{...}","original_question":"...","draft_answer":"..."}' \
  | python scripts/refine_answer.py --tone tone_profile.json

# 3) Preview the Coze-injectable style instruction (debugging)
python scripts/tone_matcher.py --samples-file samples.txt --as-prompt

# 4) Self-test
python scripts/tone_matcher.py --self-test
```

## Compatibility

- Incremental: only adds the `--tone` option and the `tone_profile` contract field; the existing simple / middle / complex flows are untouched.
- Without `--tone`, behavior is exactly unchanged (default canonical tone).
- Pure local: extraction and rendering both run locally, no network outbound.
