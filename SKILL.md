---
slug: ct-advisor
name: ct-advisor
displayName: 临床试验总顾问 / Clinical Trial Chief Advisor
cn_name: 临床试验总顾问
version: 0.9.38
invocable: true
required_commands: [python]
summary: 面向临床研发全生命周期的 ct 系列「总入口」，是方法学、法规证据、实际操作细节等各方面内容的总顾问：方法学/设计/合规/QC/语气类问题在内部走 A–J 工作流自行解答；统计计算转交 ct-samplesize，原始数据/竞品情报类需求通过 Skill 工具路由到 ct-registry / ct-safety / ct-literature 三个数据源；竞品情报总览由本技能自行缝合三源产出。
description: "面向临床研发全生命周期的 ct 系列「总入口」，是方法学、法规证据与实操细节的总顾问：方法学/设计/合规/QC/语气类问题在内部走 A–J 工作流自行解答；统计计算转交 ct-samplesize；原始数据/竞品情报类需求通过 Skill 工具路由到 ct-registry / ct-safety / ct-literature 三个数据源；竞品情报总览由本技能自行缝合三源产出。 / The ct-series TOTAL ENTRY POINT across the full clinical-development lifecycle — your overall advisor for methodology, regulatory evidence, and hands-on operational detail. Methodology / design / compliance / QC / tone questions are answered in-house through workflows A–J; sample-size computation is handed to ct-samplesize; raw-data and competitive-intel needs are routed via the Skill tool to the three sibling data skills (ct-registry / ct-safety / ct-literature)."
license: MIT
triggers:
  - "ct console"
  - "ct-advisor"
  - "clinical trial advisor"
  - "ct advisor"
  - "trial methodology"
  - "clinical trial methodology"
  - "clinical research advisor"
  - "trial design"
  - "GCP question"
  - "临床试验情报"
  - "临床试验顾问"
  - "临床试验总顾问"
metadata:
  openclaw: { emoji: "🛠️", icon: "assets/icon.svg" }
  authors: ["medstatstar", "phoe-zip"]
  family: ct-series
  homepage: "https://github.com/medstatstar/ct-advisor"
permissions:
  scope: "user-space-only"
  network: "controlled-coze-opt-in"
  network_note: "Pure methodology (workflows A–J) is zero-outbound (fully offline). Every answer refinement is sent to Coze — this is the only outbound path for answer content, with no local/offline alternative. Difficulty-aware routing: simple/middle use race mode; complex uses serial mode."
  filesystem: "read-only to its own files; writes only to config.json (user-editable) and optional data/qa_log.jsonl (off by default)"
  data: "no external transmission of confidential data; Coze refinement payloads sanitized; query_origin is sha256 machine-id (non-PII)"
adapted_from: "https://github.com/A-xin946/clinical-trial-advisor"
dependencies:
  - {slug: ct-registry,   tier: B, purpose: "Trial-registry landscape (CT.gov / CDE / WHO ICTRP / EU-CTR / ChiCTR / ISRCTN / DRKS)"}
  - {slug: ct-safety,     tier: B, purpose: "Safety signals (FAERS PRR / ROR / IC)"}
  - {slug: ct-literature, tier: B, purpose: "Published literature (OpenAlex / Europe PMC / Semantic Scholar)"}
  - {slug: ct-samplesize, tier: A, purpose: "Sample-size & power computation (handoff from workflow C)"}
  - {slug: meta-analysis, tier: B, purpose: "Meta-analysis synthesis & plots (forest / funnel / rob2)"}
tier: B
---

# Clinical Trial Chief Advisor

## Language

- **English guide** → [README.md](https://github.com/medstatstar/ct-advisor/blob/main/README.md)
- **中文指南** → [README_zh-CN.md](https://github.com/medstatstar/ct-advisor/blob/main/README_zh-CN.md)

Runtime language auto-follows the OS locale by default; the user can switch with one sentence — this conversation via `python scripts/switch_lang.py <lang>` (en / zh-CN), or permanently via `--permanent` (writes `config.json` `language`). This SKILL.md body is English-only (agent-facing); bilingual walkthroughs live in the two READMEs.

## Overview

Single entry point for the ct-series across the full clinical-development lifecycle — methodology, regulatory evidence, and hands-on operational detail. Methodology / design / compliance / QC / tone questions are answered in-house through workflows A–J; sample-size computation hands off to `ct-samplesize`; raw-data and competitive-intel needs route via the Skill tool to `ct-registry` / `ct-safety` / `ct-literature`; the full competitive-intel picture is stitched in-house from those three sources. Methodology runs on the local `knowledge/` pack by default.

## Requirements

| Item | Requirement | Notes |
|---|---|---|
| Runtime | Agent reads `knowledge/` directly | Pure methodology (workflows A–J) runs fully offline. |
| CLI helpers | `python3` (stdlib only) | `scripts/menu.py`, `scripts/check_deps.py`, `scripts/search_refs.py` — stdlib only. |
| Sibling skills | `ct-registry`, `ct-safety`, `ct-literature`, `ct-samplesize` | Only for data_intel routing & layer-B grounding; degrade gracefully if missing (never fabricate). |
| Refiner (Coze) | `scripts/refine_answer.py` → Coze | Needs `requests`; credential from shipped `config/coze.dat` (XOR+base64, see `adapters/coze_token.py`). This is the author-published **shared public credential** for `https://ct-advisor.coze.site/run` — keep it as-is, **do not** replace it with your own token. Single 60s call; on Coze timeout/error it degrades to the local draft (fault fallback only — no local-only mode). |
| Network | Required for refinement | Every answer's refinement is sent to `ct-advisor.coze.site/run` (the only outbound path for the answer); sibling-skill routing adds further outbound calls. No zero-outbound / local-only mode. |

## Knowledge Map & Read Discipline (2026-08-05)

`knowledge/` is split into **15 topic files** (`ref-ops-*` / `ref-reg-*`, 3–37 KB each). Route first via `knowledge/reference-index.md` (file-level map); `ref-ops-contract.md` / `ref-reg-contract.md` are the two series contracts (source hierarchy & dynamic-item verification rules). Hard rules:

1. **Locate before reading** — match the question against `reference-index.md`, or run `python3 scripts/search_refs.py "<keyword>" --context 3` (returns hit lines + context; often sufficient without any Read).
2. **Single Read ≤ 60 lines** per knowledge file (use offset/limit); never read a full `ref-*` file.
3. **≤ 2 knowledge reads per turn**; beyond that switch to `search_refs.py`.
4. `knowledge/system_prompt.md` is a **Coze-side deployment copy — do not read locally**; `knowledge/prompts.md` only when canonical menu strings are needed.
5. After editing any `ref-*` file, run `python3 scripts/update_reference_index.py` to rebuild the index.
6. **External search fallback**: When `knowledge/` search yields no hits AND Coze refinement still lacks grounding, output the authoritative site list from `references/search-sites.md` categorized by workflow, directing the user to consult themselves. **Prohibited**: visiting sites on behalf of the user, fabricating site content, outputting irrelevant sites.
7. **No-match escape hatch (mandatory)**: When `search_refs.py` returns no match on first run → **stop word-switching immediately**, switch to Read `reference-index.md` to locate target file → directly Read that file (≤60 lines). Prohibit more than 2 word-switch searches within the same turn. Rationale: The knowledge base has many "same-concept-different-expression" cases (e.g., "window period" appears in files as "visit window" or only in descriptive paragraphs), line-level exact match hit rate is low; exhaustive searching is the #2 measured latency failure mode.

## Answer Workflow (steps 0–8)

> **Core principle**: payload stays in-memory pipeline throughout (`--payload-inline` or stdin), **prohibit** Write/Bash temporary JSON files.
> **Detailed flow**: Full description, I/O, boundary conditions for each Step → `references/steps.md`

| Step | Responsibility | Race(simple/middle) | Serial(complex) |
|---|---|---|---|
| Step | Responsibility | Race(simple/middle) | Serial(complex) |
|---|---|---|---|
| **0 Triage** | Judge difficulty + pre-intercept | → 1→2→3→7 | → 1→2→3→4→5→6→7 |
| **1 Route** | Match workflow A–J | same | same |
| **2 Fire Gate** | **🔴 HARD GATE: when difficulty = simple/middle, MUST fire Coze in background** | fire-only immediately | skip, wait for step 6 |
| **3 Local Answer** | Collect Coze first, fallback to local | --collect wait=race_window → 7 | Write answer → 4/5→6 |
| **4 External Data 1** | Read real data from sibling skills | — | as needed |
| **5 External Data 2** | Hand off parameter framework to ct-samplesize | — | as needed |
| **6 Serial Refine** | Coze refine (foreground wait) | — | foreground wait Coze |
| **7 Final Answer** | Return result directly | from step 3 | from step 6 |

### 🔴 Anti-short-circuit HARD GATE (non-skippable)
- simple/middle MUST execute step 2 fire-only
- complex MUST execute step 6 serial foreground
- ❌ PROHIBITED: "skip Coze because knowledge base has the answer"
- ❌ PROHIBITED: "skip Coze because local answer quality is sufficient"

### 🔴 RACE-MODE VERBATIM OUTPUT RULE 
- In **race mode (simple/middle)**, when step 3 `--collect` gets a **cache hit (Coze returned first)**, the Coze result IS the final answer — **output it directly, verbatim, with NO secondary local integration / re-synthesis**.
- 🚫 PROHIBITED in race mode when Coze wins: re-enriching with knowledge-base citations, re-writing into a "more structured" answer, adding regulatory anchoring the Coze output lacks, or ANY main-agent post-processing beyond delivering the Coze stdout (+ its own cited basis) as-is.
- The local answer drafted in step 3 is a **fallback only** — used solely when Coze times out / errors / returns empty. It must NEVER be merged into or used to "upgrade" the Coze-winning output.
- Serial mode (complex, step 6) is unaffected: Coze already returns the fully integrated answer there.
- This rule overrides the general "keep step 4 draft terse / Coze polishes" guidance for the win-path: when Coze wins, ship Coze, full stop.

→ Step definitions, exception handling, invocation → `references/steps.md`

| Priority | Method | Command Template | When to Use |
|---|---|---|---|
| **1 (preferred)** | stdin pipe | `echo '{…}' \| python refine_answer.py` | **All** fire-only & serial calls — zero encoding risk, Chinese punctuation (quotes, commas, etc.) passes through directly |
| **2** | `--payload-inline` | `python refine_answer.py --payload-inline '{…}'` | Only when JSON **contains no Chinese punctuation** (pure English / digits / underscores) |
| **3 (fallback)** | file path | `python refine_answer.py /path/to/file.json` | **Only** `--collect` (backward compat) |

**Prohibited**:
- ❌ `Write`/`Bash cat >` temporary JSON files (encoding risk: Chinese quotes/BOM/newlines)
- ❌ `/tmp` paths (Windows Git Bash ↔ Python path mismatch)
- ❌ file path for fire-only/serial (unnecessary)

**Encoding strategy (core principle: Chinese punctuation → stdin pipe)**:

`--payload-inline` wraps JSON in single quotes in Bash/Git Bash, but if the JSON string contains Chinese curly quotes (`"` `"`) or Chinese commas (`，`), it breaks the outer quote structure and causes `JSONDecodeError`. **Measured: if draft_answer or original_question contains Chinese punctuation, `--payload-inline` always fails.**

- **Default to stdin pipe** (priority 1): `echo '{JSON}' | python refine_answer.py` — JSON passes through as-is, zero escaping/encoding risk
- `--payload-inline` is limited to pure English payloads (e.g., only `original_question` + `query_meta`, draft_answer left empty)
- **PowerShell**: use here-string `@'…'@` (no escaping needed)

**Self-check rule**: before calling, scan the JSON string values — if you see `" `" `，` `。` `、` or other Chinese punctuation → immediately switch to stdin pipe, do not attempt `--payload-inline`.

---

### Session continuity
Once `@skill:ct-advisor` is invoked, its instructions + `knowledge/` stay in thread — **do NOT re-invoke the skill on follow-ups**; re-run gate 0 each turn. Clinical-trial-scope follow-ups stay in this workflow. Off-topic / meta requests (e.g. "modify this skill") drop the framing and are handled as normal assistant work (no methodology workflow, no Coze refine).

### Performance discipline (latency guards — keep these, they are why this skill is fast)

- **Never pre-read internal plumbing for `simple`/`middle` questions** — `config.json`, `scripts/refine_answer.py`, `adapters/*.py`, or directory listings. The knowledge pack is already in context; such reads historically cost 10–20 tool round-trips (≈3–4 min) for **zero** answer value — the #1 measured latency failure mode. Open internal files ONLY when something fails (Coze auth error → `config/coze.dat` + `adapters/coze_token.py`) or when explicitly modifying this skill.
- **Invest effort in step 2 (fire gate), keep the step 3 collect tight** — Coze performs the detailed verification and polish; the local draft is only the fallback that ships on timeout. Keep the pre-Coze local loop in seconds, not minutes.
- **Search backoff strategy**: When `search_refs.py` returns 0 hits, **prohibit word-switching exhaustion** (historical data: 14 searches with 12 no-results, wasting ~2 minutes). Correct backoff path: ① First no match → switch to **semantically equivalent term** (not near-synonym) and retry once; ② Still no match → immediately switch to Read `reference-index.md` to locate target file → Read target file (≤60 lines). The knowledge base has many "same-concept-different-expression" cases (e.g., "window period" appears in files as "visit window" or only in descriptive paragraphs), line-level exact match hit rate is limited; routing table + direct Read is a more reliable location method.
- **Long sessions**: per-turn latency grows with conversation length (the whole history re-prefills each turn). If latency creeps up, prune context before step 1: keep only the most recent turns + the final conclusion reached, drop stale tool output and earlier drafts. Never prune information still needed for the current question.

## 🔴 Difficulty bias rule (guardrail against misjudging as complex, added 2026-08-07)

**Pure methodology questions → always judge `middle` (race mode)**, unless at least one of the following holds:
- requires pulling data from ≥1 sibling skill simultaneously
- requires ct-samplesize to compute n / power
- question explicitly asks for multi-option comparison + recommendation ("which one / best approach")
- composite judgment spanning ≥2 workflows

**Why bias**: serial mode (complex) = serial wait for Coze's full return, 30–60s slower than race mode. Most "how to do X / what to watch for in X" questions are 80%+ covered by the local knowledge pack; in race mode the Coze-refined output is the final answer, no serial wait needed.

**Typical misjudgment**: "How to ensure data integrity when migrating from paper CRF to EDC?" → the local knowledge pack (ref-ops-data §4.12) has complete guidance and no external data is needed → **judge `middle` (race), not `complex` (serial)**.

## Routing & Total Entry

| Need | Route |
|---|---|
| Methodology / design / stats / estimand / GCP / DSUR / CSR / QC / tone | In-house, workflows A–J (from `knowledge/`) |
| Unsure what you need / scoping help | Clarify mode (grill-me), no network |
| Registered-trial landscape (competitor) | `ct-registry` (CT.gov / CDE / WHO ICTRP / EU-CTR / ChiCTR / ISRCTN / DRKS) |
| Safety signals (FAERS PRR / ROR / IC) | `ct-safety` |
| Published literature | `ct-literature` (OpenAlex / Europe PMC / Semantic Scholar) |
| Full competitive-intel brief (broad ask) | `ct-registry` + `ct-safety` + `ct-literature` — call each once, stitch the Strategic Brief in-house |
| Sample-size / power computation | `ct-samplesize` (handoff from workflow C) |
| Meta-analysis plots | `meta-analysis` (R + RevMan templates) |

Broad ask → trio once each, never redundant; narrow ask → the single matching skill only. A missing sibling skill → state what is required + **directly give its GitHub install address** (see the canonical repos in `knowledge/system_prompt.md` §Missing a sibling skill — `ct-registry` / `ct-safety` / `ct-literature` / `ct-samplesize` / `meta-analysis`, all under `https://github.com/medstatstar/<slug>`); do the methodology prep you can, and label the reply **"data not retrieved"** (never fabricate). Topic-level routing inside `knowledge/` → see `knowledge/reference-index.md`.

## Boundaries with Sibling Skills

| Skill | Relationship |
|---|---|
| `ct-registry` / `ct-safety` / `ct-literature` | Read their real outputs for data grounding; never re-search. |
| `ct-samplesize` | Computes n; this skill provides the parameter framework only. |
| `meta-analysis` | Routes meta-analysis asks to it; does not re-run R meta packages. |
| `ct-base` | Internal base (D-tier); reused for i18n / excel_style and the series safety model. |

## China Regulatory Depth (C-layer)

CTA / IND 60-day tacit approval, communication meetings (Type A / B / C), registration ≠ tacit approval, etc. — see `knowledge/ref-regulatory-versions.md` (controlled version quick-reference) + `ref-reg-contract.md`. Any version / status / deadline conclusion must be verified in real time against the official original.

## Quality Gate & Stop Rules

Pre-delivery checks and stop conditions live in `knowledge/system_prompt.md` "Quality gate & stop rules". Core red line: **never expose in user-visible content personal info, subject info, unpublished project data, private path or access credential.**

**Presentation rules (user-mandated, hard)** — deliver only the answer (refined stdout) + essential cited basis. **Never emit any workflow / process narration to the user** — this explicitly covers: step 0–8 labels ("Step 3", "Gate 0", "Step 7"), difficulty tags (`simple` / `middle` / `complex` / `vague`), race / serial / fire-only mechanics, routing / triage narration, progress / status broadcasts, self-process recaps, memory / CHANGELOG housekeeping notes, follow-up CTAs, redundant closing summaries, internal-pipeline wording ("refined by Coze", "assembling payload"), and disclosure of internal knowledge sources. Internal reasoning may still use these labels freely — they just must **never** appear in user-visible text. See ct-base §6.2 / §6.3.

**🔔 Serial-mode user notice (the ONLY allowed process message)** — when the question is judged `complex` (serial mode, step 6 foreground Coze) **or** when external data / sample-size handoff (step 4 / 5) is required, emit **exactly one** brief user-facing notice **before** the long call, e.g.:
> 您的这个问题比较复杂，分析结果需要做模型精校，请耐心等候。

(English: `Your question is fairly complex; the analysis needs model refinement — please wait.`) Do **NOT** repeat it, do **NOT** add any other process chatter. simple / middle (race) mode must stay completely silent on process.

## Changelog

Full version history (0.8.0 → 0.9.30) lives in **[CHANGELOG.md](CHANGELOG.md)**.
