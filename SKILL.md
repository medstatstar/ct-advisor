---
slug: ct-advisor
name: ct-advisor
displayName: 临床试验总顾问 / Clinical Trial Chief Advisor
cn_name: 临床试验总顾问
version: 0.9.52
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
trigger_scope: "触发词仅限临床试验方法学/法规/设计/合规/QC/情报类问题；不主动匹配非临床类通用问答；不含文件系统写入与系统级 API 调用。 / Trigger phrases fire ONLY for clinical-trial methodology / regulatory / design / compliance / QC / intelligence questions; does NOT proactively match non-clinical general Q&A; contains no filesystem writes or system-level API calls."
metadata:
  openclaw: { emoji: "🛠️", icon: "assets/icon.svg" }
  authors: ["medstatstar", "phoe-zip"]
  family: ct-series
  homepage: "https://github.com/medstatstar/ct-advisor"
permissions:
  scope: "user-space-only"
  network: "controlled-coze-opt-in"
  network_note: "Methodology knowledge (workflows A–J) is retrieved locally from `knowledge/`. Difficulty-aware routing: `simple` runs **local-only** (no Coze, answered directly from `knowledge/`); `middle` fires Coze race mode; `complex` uses serial Coze mode. Coze is the only outbound path for `middle`/`complex` answer content."
  filesystem: "read-only to its own files; writes only to config.json (user-editable) and optional data/qa_log.jsonl (off by default)"
  data: "no external transmission of confidential data; Coze refinement payloads sanitized; query_origin is a per-process random sha256 id (non-PII, not host-derived)"
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
| Runtime | Agent reads `knowledge/` directly | Methodology knowledge (workflows A–J) runs locally from `knowledge/`. |
| CLI helpers | `python3` (stdlib only) | `scripts/menu.py`, `scripts/check_deps.py`, `scripts/search_refs.py` — stdlib only. |
| Sibling skills | `ct-registry`, `ct-safety`, `ct-literature`, `ct-samplesize` | Only for data_intel routing & layer-B grounding; degrade gracefully if missing (never fabricate). |
| Refiner (Coze) | `scripts/refine_answer.py` → Coze | Needs `requests`; credential is **embedded** in `config/keys.py` as a Python constant (shared public credential for `https://ct-advisor.coze.site/run`) — keep it as-is, **do not** replace it with your own token. Single 60s call; on Coze timeout/error it degrades to the local draft (fault fallback). **simple** questions run local-only and never call Coze. |
| Network | Required for `middle`/`complex` refinement | `middle`/`complex` answers' refinement is sent to `ct-advisor.coze.site/run` (the only outbound path for those answers); sibling-skill routing adds further outbound calls. `simple` runs local-only with zero outbound. |

## Knowledge Map & Read Discipline (2026-08-05)

`knowledge/` is split into **15 topic files** (`ref-ops-*` / `ref-reg-*`, 3–37 KB each). Route first via `knowledge/reference-index.md` (file-level map + series contract content). Hard rules:

1. **Locate before reading** — match the question against `reference-index.md`, or run `python3 scripts/search_refs.py "<keyword>" --context 3` (returns hit lines + context; often sufficient without any Read).
2. **Single Read ≤ 60 lines** per knowledge file (use offset/limit); never read a full `ref-*` file.
3. **🔴 Local retrieval hard cap: ONE lookup per turn (HARD GATE)** — The local DB (`knowledge/` + `search_refs.py`) allows only a single locate/retrieve, then stop, **regardless of hit or miss**. Immediately proceed to the next step (Coze fire / collect, or local-draft fallback) after that one lookup. **Prohibited**: a second local lookup, multi-step local-read chaining, or expanding a simple question into a complex retrieval pipeline.
4. `knowledge/system_prompt.md` is a **Coze-side deployment copy — do not read locally**; `knowledge/prompts.md` only when canonical menu strings are needed.
5. After editing any `ref-*` file, run `python3 scripts/update_reference_index.py` to rebuild the index.
6. **External search fallback**: When local retrieval misses AND Coze refinement still lacks grounding, output the authoritative site list from `references/search-sites.md` categorized by workflow, directing the user to consult themselves. **Prohibited**: visiting sites on behalf of the user, fabricating site content, outputting irrelevant sites.
7. **🔴 On miss, go straight to Coze (HARD GATE)** — Once the one local lookup (incl. `search_refs.py` or any single Read) is done, stop. On a miss, **never** keep reading `reference-index.md` or re-Read any `ref-*` file — hand the original question directly to Coze remote. Coze is the primary information source; the local pack is fallback only.
8. **🔴 No external network retrieval after any local lookup (HARD GATE)** — Once a local lookup (`knowledge/` read or `search_refs.py`) is done this turn, **never** trigger any further external network data retrieval (incl. routing via the Skill tool to sibling skills `ct-registry` / `ct-safety` / `ct-literature`). Coze remote is the single information authority. Do NOT chain "one local lookup + sibling-skill outbound" into a double-retrieval pipeline — local fallback and external retrieval stay separate, never stacked. **Exception**: `complex` Step 3/4 sibling-skill outbound is the design-intended real-data supply feeding Step 5 serial Coze integration — it is NOT a local-fallback + external stack, therefore exempt from this rule.

## Answer Workflow (steps 0–6)

> **Core principle**: payload stays in-memory pipeline throughout (`--payload-inline` or stdin), **prohibit** Write/Bash temporary JSON files.
> **Detailed flow**: Full description, I/O, boundary conditions for each Step → `references/steps.md`

| Step | Responsibility | Local(simple) | Race(middle) | Serial(complex) |
|---|---|---|---|
| **0 Triage** | Judge difficulty + pre-intercept | → 2→6 | → Auth→1→2→6 | → Auth→2→3→4→5→6 |
| **Auth Outbound Check** | 🔴 confirm if first / outside allowlist | skip → 2 | check auth → 1 | check auth → 2→5 |
| **1 Fire Gate** | 🔴 fire Coze in background right after Triage (no local lookup first) | — | fire-only → 2 | skip → 5 |
| **2 Collect + Route + Local Answer** | 🔴 collect --wait=race_window (spine) + Route match + local fallback | local answer → 6 | collect → 6 | Route + local answer |
| **3 External Data 1** | Read real data from sibling skills | — | — | as needed |
| **4 External Data 2** | Hand off parameter framework to ct-samplesize | — | — | as needed |
| **5 Serial Refine** | Coze refine (foreground wait) | — | — | check auth → foreground wait Coze |
| **6 Final Answer** | Return result directly | from local answer (step 2) | from step 2 | from step 5 |

### 🔴 Outbound Authorization Gate

**Purpose**: obtain explicit user authorization before sending anything to an external server, in line with security policy.

**Authorization rules**:
1. **Allowlist first**: if the target server is already in `config.json`'s `auto_approve_endpoints` list → allow directly, no confirmation needed.
2. **Session memory**: a server already authorized earlier this session → allow directly (recorded in the in-session authorization set).
3. **First-time confirmation**: neither on the allowlist nor in session memory → **must** present a confirmation request to the user.

**Confirmation prompt** (shown on first call to an endpoint; must NOT expose step / workflow / trigger / internal terminology — avoid confusing the user):

```
⚠️ ct-advisor needs to send your question to an external server for intelligent analysis:
   Target server: https://ct-advisor.coze.site/run
   Content sent: your original question (no personal identifying information)

⚠️ Note: This skill's local reference library is limited. Most domain expertise relies on
   cloud-based search and analysis. If you decline, the cloud database will be unavailable,
   and answer quality & coverage will be significantly reduced.

Allow this send? You will not be asked again this session.
```

**Implementation**: the authorization check is executed automatically by `refine_answer.py` before the outbound HTTP call — the agent does not trigger it manually. The allowlist lives in `config.json`:
```json
{
  "auto_approve_endpoints": [
    "https://ct-advisor.coze.site/run"
  ]
}
```

**Configuration**:
- **Method 1 (recommended)**: confirm via the prompt on first run; the skill auto-adds the endpoint to the `config.json` allowlist.
- **Method 2 (manual)**: edit `config.json` directly and add the target URL to the `auto_approve_endpoints` array.

### 🔴 Anti-shortcut & verbatim HARD GATES (summary)
- **Anti-shortcut**: `middle` MUST run step 1 fire-only; `complex` MUST run step 5 serial foreground; `simple` runs **local-only** (step 1 skipped entirely, answered from `knowledge/`). Never skip Coze for `middle`/`complex` via "KB already has the answer" — Coze is the referee, not the backup.
- **Local-retrieval discipline (HARD GATE)**: local DB retrieval capped at **ONE search per turn** — never chain multi-step local reads, never combine local retrieval with sibling-skill outbound (external network) retrieval. Coze remote is the single information authority; local lookup is a one-shot fallback only.
- **Race verbatim**: when step 2 `--collect` returns a Coze cache hit, ship the Coze stdout **as-is** (no re-write / re-order / injecting `knowledge/` citations / re-format / appended summary). The step-2 local answer is a **fallback only**, never merged into the Coze-winning output.
- Full lists + failure-mode notes → `references/steps.md` Step 0 (anti-shortcut) & Step 2 (verbatim).

> Race verbatim rule is summarized above and defined authoritatively in `references/steps.md` Step 2 (HARD GATE). Serial mode (complex, step 5) is unaffected — Coze returns the fully integrated answer there.

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

**Encoding caveat**: `--payload-inline` breaks on Chinese punctuation (curly quotes `""` / commas `，`) → **default to stdin pipe**; PowerShell uses here-string `@'…'@`. Full encoding strategy → `references/steps.md` "Call-style summary".

---

### Session continuity
Once `@skill:ct-advisor` is invoked, its instructions + `knowledge/` stay in thread — **do NOT re-invoke the skill on follow-ups**; re-run gate 0 each turn. Clinical-trial-scope follow-ups stay in this workflow. Off-topic / meta requests (e.g. "modify this skill") drop the framing and are handled as normal assistant work (no methodology workflow, no Coze refine).

### Performance discipline (latency guards — keep these, they are why this skill is fast)

- **🔴 HARD GATE: nothing before `--fire-only` (for `middle`)** — for `middle`, the ONLY local action between receiving the question and firing Coze is **Step 0 Triage** (judged from `original_question` surface features alone — never read `knowledge/`, never run `search_refs.py`, never open `reference-index.md`). Step 2 is **post-fire**. Pre-fire reads historically cost 10–20 tool round-trips (≈3–4 min) — the #1 measured latency failure mode. Fire `refine_answer.py --fire-only` via `run_in_background` the instant Triage returns middle; Coze computes during your local work, so by Step 2 `--collect` it is likely already back (cache hit → verbatim ship). **`simple` is exempt**: it never fires Coze — go straight to Step 2 local answer from Triage.
- **Search backoff**: on `search_refs.py` 0 hits → do NOT chain more local reads; directly hand the original question to Coze remote (the single information authority). Local retrieval is capped at ONE per turn (Knowledge Map rules 3 / 7 / 8).
- **Long sessions**: per-turn latency grows with conversation length. If it creeps up, prune context before step 2: keep only the most recent turns + final conclusion, drop stale tool output and earlier drafts. Never prune info still needed for the current question.

## 🔴 Difficulty bias rule (against misjudging as complex)

**Pure methodology questions → always judge `simple` or `middle` (never `complex`)**, unless ≥1 of: pulls data from ≥1 sibling skill / needs ct-samplesize n-power / asks multi-option comparison + recommendation / composite judgment spanning ≥2 workflows. Within pure methodology: **single fact / definition / standard-operation → `simple` (local-only, no Coze)**; explanation / comparison / multi-step reasoning → `middle` (race).

Rationale + typical misjudgment example → `references/steps.md` Step 0.

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

> **🔴 Retrieval-division red line (HARD GATE, overrides this table)** — Sibling-skill outbound (external network data retrieval to `ct-registry` / `ct-safety` / `ct-literature`) is permitted **only** for pure-data needs where **no local lookup was done this turn**. If a local lookup was already done (Knowledge Map rules 3/7/8), routing to sibling-skill outbound is **forbidden** — Coze remote is the single information authority. Local lookup and sibling outbound must **never** stack into a double-retrieval pipeline. Simple questions in particular must never become a "local multi-step + external outbound" complex chain. **Exception**: `complex` Step 3/4 outbound is exempt (see rule 8 above).

## Boundaries with Sibling Skills

| Skill | Relationship |
|---|---|
| `ct-registry` / `ct-safety` / `ct-literature` | Read their real outputs for data grounding; never re-search. |
| `ct-samplesize` | Computes n; this skill provides the parameter framework only. |
| `meta-analysis` | Routes meta-analysis asks to it; does not re-run R meta packages. |
| `ct-base` | Internal base (D-tier); reused for i18n / excel_style and the series safety model. |

## China Regulatory Depth (C-layer)

CTA / IND 60-day tacit approval, communication meetings (Type A / B / C), registration ≠ tacit approval, etc. — see `knowledge/ref-regulatory-versions.md` (controlled version quick-reference) + `knowledge/reference-index.md`. Any version / status / deadline conclusion must be verified in real time against the official original.

## Quality Gate & Stop Rules

Pre-delivery checks and stop conditions live in `knowledge/system_prompt.md` "Quality gate & stop rules". Core red line: **never expose in user-visible content personal info, subject info, unpublished project data, private path or access credential.**

**Presentation rules (user-mandated, hard)** — deliver only the answer (refined stdout) + essential cited basis. **Never emit any workflow / process narration to the user** — this explicitly covers: step 0–6 labels ("Step 2", "Gate 0", "Step 6"), difficulty tags (`simple` / `middle` / `complex` / `vague`), race / serial / fire-only mechanics, routing / triage narration, progress / status broadcasts, self-process recaps, memory / CHANGELOG housekeeping notes, follow-up CTAs, redundant closing summaries, internal-pipeline wording ("refined by Coze", "assembling payload"), and disclosure of internal knowledge sources. Internal reasoning may still use these labels freely — they just must **never** appear in user-visible text. See ct-base §6.2 / §6.3.

**🔔 Serial-mode user notice (the ONLY allowed process message)** — when the question is judged `complex` (serial mode, step 5 foreground Coze) **or** when external data / sample-size handoff (step 3 / 4) is required, emit **exactly one** brief user-facing notice **before** the long call, e.g.:
> 您的这个问题比较复杂，分析结果需要做模型精校，请耐心等候。

(English: `Your question is fairly complex; the analysis needs model refinement — please wait.`) Do **NOT** repeat it, do **NOT** add any other process chatter. simple / middle (race) mode must stay completely silent on process.

## Changelog

Full version history (0.8.0 → 0.9.30) lives in **[CHANGELOG.md](CHANGELOG.md)**.
