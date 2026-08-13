---
slug: ct-advisor
name: ct-advisor
displayName: 临床试验总顾问 / Clinical Trial Chief Advisor
cn_name: 临床试验总顾问
version: 0.9.60
invocable: true
required_commands: [python]
summary: "面向临床研发全生命周期的 ct 系列「总入口」，是方法学、法规证据、实际操作细节等各方面内容的总顾问：方法学/设计/合规/QC/语气类问题在内部走 A–J 工作流自行解答；统计计算转交 ct-samplesize，原始数据/竞品情报类需求通过 Skill 工具路由到 ct-registry / ct-safety / ct-literature 三个数据源；竞品情报总览由本技能自行缝合三源产出。"
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
trigger_scope: "触发词仅限临床试验方法学/法规/设计/合规/QC/情报类问题；不主动匹配非临床类通用问答；不含文件系统写入与系统级 API 调用。"
metadata:
  openclaw: { emoji: "🛠️", icon: "assets/icon.svg" }
  authors: ["medstatstar", "phoe-zip"]
  family: ct-series
  homepage: "https://github.com/medstatstar/ct-advisor"
permissions:
  scope: "user-space-only"
  network: "controlled-coze-opt-in"
  network_note: "Methodology (A–J) runs local-only from `knowledge/`; `simple` answers locally (no Coze), `middle` fires Coze race, `complex` serial Coze — Coze is the sole outbound path for `middle`/`complex`."
  filesystem: "Read-only to own files (writes only config.json + optional data/qa_log.jsonl, off by default); no confidential data leaves locally — Coze payloads sanitized, query_origin is a stable per-machine sha256 hash (sha256 of hostname + salt, non-PII, not host-readable)."
adapted_from: "https://github.com/A-xin946/clinical-trial-advisor"
dependencies:
  - {slug: ct-registry,   tier: B}
  - {slug: ct-safety,     tier: B}
  - {slug: ct-literature, tier: B}
  - {slug: ct-samplesize, tier: A}
  - {slug: meta-analysis, tier: B}
tier: B
---

# Clinical Trial Chief Advisor

## Language

- **English guide** → [README.md](https://github.com/medstatstar/ct-advisor/blob/main/README.md) ｜ **中文指南** → [README_zh-CN.md](https://github.com/medstatstar/ct-advisor/blob/main/README_zh-CN.md)
- Runtime language auto-follows the OS locale; switchable in one sentence (`scripts/switch_lang.py`, `--permanent` writes `config.json` `language`). This body is English-only (agent-facing); bilingual walkthroughs live in the two READMEs.

## Overview

Single entry point for the ct-series: methodology / design / compliance / QC / tone answered in-house (workflows A–J from `knowledge/`); sample-size hands off to `ct-samplesize`; raw-data / competitive-intel route to `ct-registry` / `ct-safety` / `ct-literature` (broad asks stitched in-house from the trio).

## Requirements

| Item | Requirement |
|---|---|
| Runtime | `python3` stdlib; read `knowledge/` directly |
| Sibling skills | `ct-registry` / `ct-safety` / `ct-literature` / `ct-samplesize` / `meta-analysis` (degrade gracefully if missing, never fabricate) |
| Refiner (Coze) | `scripts/refine_answer.py` POSTs 3 variables to `ct-advisor.coze.site/run` — the **only** outbound path (middle/complex only; simple local-only zero-outbound). Credential embedded in `config/keys.py` (shared public token — keep as-is). 60s timeout → degrade to local draft (fault fallback). |

## Knowledge Map & Read Discipline (2026-08-05)

`knowledge/` = 15 topic files (`ref-ops-*` / `ref-reg-*`). Route via `knowledge/reference-index.md`; search via `search_refs.py "<kw>" --context 3`; single Read ≤ 60 lines. Hard rules:

1. **🔴 ONE local lookup per turn (HARD GATE)** — a single locate/retrieve (`search_refs.py` or one Read), then stop regardless of hit/miss. Never chain a second lookup or multi-step local reads.
2. **🔴 On miss, go straight to Coze (HARD GATE)** — never re-Read `reference-index.md` / any `ref-*`; hand the original question directly to Coze remote (the single information authority).
3. **🔴 No external network retrieval after any local lookup (HARD GATE)** — never stack "local lookup + sibling-skill outbound" (incl. Skill-tool routing to ct-*). **Exception**: complex Step 3/4 sibling outbound is design-intended real-data supply.
4. `knowledge/system_prompt.md` = Coze-side deployment copy, do not read locally; `prompts.md` only when menu strings are needed. After editing any `ref-*`, rebuild the index via `update_reference_index.py`.
5. External search fallback: on local miss + Coze under-grounded, list authoritative sites from `references/search-sites.md` for the user to consult — never visit sites on their behalf / fabricate content.

## Answer Workflow (steps 0–6)

> **Core principle**: payload stays in-memory pipeline throughout (`--payload-inline` or stdin), **prohibit** Write/Bash temporary JSON files.
> **Detailed flow**: Full description, I/O, boundary conditions for each Step → `references/steps.md`

| Step | Responsibility | Local(simple) | Race(middle) | Serial(complex) |
|---|---|---|---|
| **0 Triage** | 🔴 run `route.py` (deterministic, zero-LLM) → label; agent MUST NOT self-judge difficulty | → 2→6 | → Auth→1→2→6 | → Auth→2→3→4→5→6 |
| **Auth Outbound Check** | 🔴 confirm if first / outside allowlist | skip → 2 | check auth → 1 | check auth → 2→5 |
| **1 Fire Gate** | 🔴 fire Coze in background right after Triage (no local lookup first) | — | fire-only → 2 | skip → 5 |
| **2 Collect + Route + Local Answer** | 🔴 collect --wait=race_window (spine) + Route match + local fallback | local answer → 6 | collect → 6 | Route + local answer |
| **3 External Data 1** | Read real data from sibling skills | — | — | as needed |
| **4 External Data 2** | Hand off parameter framework to ct-samplesize | — | — | as needed |
| **5 Serial Refine** | Coze refine (foreground wait) | — | — | check auth → foreground wait Coze |
| **6 Final Answer** | Return result directly | from local answer (step 2) | from step 2 | from step 5 |

### 🔴 Outbound Authorization Gate

Runs automatically inside `refine_answer.py` before each outbound HTTP call (agent never triggers it manually). Rules: ① endpoint in `config.json` → `auto_approve_endpoints` → allow; ② authorized earlier this session → allow; ③ otherwise → show the confirmation prompt below (first call only; never expose step / workflow / internal terminology):

```
⚠️ ct-advisor needs to send your question to an external server for intelligent analysis:
   Target server: https://ct-advisor.coze.site/run
   Content sent: your original question (no personal identifying information)
⚠️ Note: the local reference library is limited; most domain expertise relies on cloud-based
   search and analysis. If you decline, answer quality & coverage will be significantly reduced.
Allow this send? You will not be asked again this session.
```

### 🔴 Anti-shortcut & verbatim HARD GATES (summary)
- **Anti-shortcut**: `middle` MUST run step 1 fire-only; `complex` MUST run step 5 serial foreground; `simple` runs **local-only** (step 1 skipped entirely, answered from `knowledge/`). Never skip Coze for `middle`/`complex` via "KB already has the answer" — Coze is the referee, not the backup.
- **Local-retrieval discipline (HARD GATE)**: local DB retrieval capped at **ONE per turn** — never chain multi-step local reads, never stack local lookup with sibling-skill outbound (Knowledge Map rules 3/7/8; complex Step 3/4 exempt).
- **Race verbatim**: when step 2 `--collect` returns a Coze cache hit, ship the Coze stdout **as-is** (no re-write / re-order / injecting `knowledge/` citations / re-format / appended summary). The step-2 local answer is a **fallback only**, never merged into the Coze-winning output.
- Full lists + failure-mode notes → `references/steps.md` Step 0 (anti-shortcut) & Step 2 (verbatim).

> Race verbatim rule is summarized above and defined authoritatively in `references/steps.md` Step 2 (HARD GATE). Serial mode (complex, step 5) is unaffected — Coze returns the fully integrated answer there.

→ Step definitions, exception handling, invocation → `references/steps.md`

### Step 0.5 · Local Clarify Loop (pure-local, zero-outbound)

If `vague` or ambiguity would change the conclusion, run `python scripts/clarify_loop.py` (same in-memory pipeline as `refine_answer.py`) **before** the local / Coze branch: 1–3 high-value questions per round, hard-capped at **3 rounds** (hitting the cap still proceeds, never loops).

**Call style (zero temp files)**: priority ① stdin pipe `echo '{…}' | python refine_answer.py` (all fire-only & serial calls — Chinese punctuation safe); ② `--payload-inline` only when the JSON has **no** Chinese punctuation (curly quotes / Chinese commas break it); ③ file path only for `--collect` back-compat. **Forbidden**: Write/Bash temp JSON files, `/tmp` paths, file paths in fire-only/serial. PowerShell: here-string `@'…'@`. Full rules + encoding caveat → `references/steps.md` "Call-style summary".
**🔴 Payload MUST carry `query_meta.difficulty`** (blank breaks server-side routing + leaves Feishu collection blank; script defaults to `complex` when missing). Example: `echo '{"query_meta":"{\"difficulty\":\"middle\",\"category\":\"\",\"accuracy\":\"\"}","original_question":"…"}' | python refine_answer.py --fire-only`
**🩺 Coze failure diagnosis (user-friendly)**: on fallback (stderr `FALLBACK` / `ProxyError` / `Timeout`, or the stdout ask "…是否允许我自动进行问题诊断排查？"), **ask the user first** — "Coze 云端服务暂时不可用，是否允许我自动诊断排查？" If allowed → run `python scripts/check_coze.py` once, fix the root cause (stale system proxy / offline / token), retry; if declined → deliver the local answer **with a prominent warning**: 「无法连接 Coze 服务，答案未经过精校，请谨慎使用」. v0.9.60+ auto-retries bypassing the system proxy on `ProxyError`/`ConnectionError`.

---

### Session continuity
Once `@skill:ct-advisor` is invoked, its instructions + `knowledge/` stay in thread — **do NOT re-invoke the skill on follow-ups**; re-run gate 0 each turn. Off-topic / meta requests (e.g. "modify this skill") drop the framing and are handled as normal assistant work (no methodology workflow, no Coze refine).

### Personalization（tone writing + local user memory）— ⚠️ DEFERRED (not enabled)

Tone writing (`tone_profile`) and local user memory (`memory_context`) are **temporarily disabled**: the deployed Coze workflow (v1.5 contract) does not implement these fields, so local injection is silently ignored. The scripts (`tone_matcher.py` / `memory_manager.py`) and the `--tone` / `--memory` CLI flags remain in place for future use but **MUST NOT be invoked**. Re-enable only after the Coze workflow ships the v1.6 contract fields (2026-08-12 decision).

### Performance discipline (latency guards — keep these, they are why this skill is fast)

- **🔴 HARD GATE: nothing before `--fire-only` (for `middle`)** — for `middle`, the ONLY local action between receiving the question and firing Coze is **Step 0 Triage**: run `python scripts/route.py "<question>"` for the deterministic label (zero-LLM; NEVER read `knowledge/`, run `search_refs.py`, or judge difficulty yourself). Step 2 is **post-fire**; pre-fire reads historically cost 10–20 tool round-trips (≈3–4 min) — the #1 latency failure mode. Fire `refine_answer.py --fire-only` via `run_in_background` the instant Triage returns middle. **`simple` is exempt**: never fires Coze — straight to Step 2 local answer.
- **Search backoff**: on `search_refs.py` 0 hits → do NOT chain more local reads; hand the original question straight to Coze remote. **Long sessions**: prune stale context before step 2 (keep recent turns + final conclusion; never drop info still needed).

## 🔴 Difficulty bias rule (against misjudging as complex)

**Pure methodology questions → always judge `simple` or `middle` (never `complex`)**, unless ≥1 of: pulls data from ≥1 sibling skill / needs ct-samplesize n-power / asks multi-option comparison + recommendation / composite judgment spanning ≥2 workflows. Within pure methodology: **single fact / definition / standard-operation → `simple` (local-only, no Coze)** — `simple` also fires on the knowledge whitelist `SIMPLE_TOPICS` in `route.py` (standard-operation phrases verified covered by `knowledge/`; whitelist hit + no complex/exclude signal → local-only, deterministic, phrasing-drift-proof); explanation / comparison / multi-step reasoning → `middle` (race). **Semantic split: `middle` + `complex` both fire Coze** — they differ only in firing mode (race vs serial), the real binary is `simple` (local-only) vs non-simple (fire Coze).

Rationale + typical misjudgment example → `references/steps.md` Step 0.

## Routing & Total Entry

| Need | Route |
|---|---|
| Methodology / design / stats / GCP / QC / tone | In-house, workflows A–J (`knowledge/`) |
| Registered-trial landscape / safety signals / literature | `ct-registry` / `ct-safety` / `ct-literature` (broad ask → trio once each, stitch in-house) |
| Sample-size / power | `ct-samplesize` (handoff from workflow C) |
| Meta-analysis plots | `meta-analysis` |
| Unsure what you need | Local clarify loop (`scripts/clarify_loop.py`) |

Missing sibling skill → state what's required + give its GitHub address (`https://github.com/medstatstar/<slug>`), do the prep you can, label the reply **"data not retrieved"** (never fabricate).

> **🔴 Retrieval-division red line (HARD GATE, overrides table)**: sibling-skill outbound permitted **only** for pure-data needs with **no local lookup done this turn** (Knowledge Map rules 1–3) — never stack local + outbound. Exception: complex Step 3/4 sibling outbound.

## Boundaries with Sibling Skills

`ct-registry` / `ct-safety` / `ct-literature` → read real outputs for grounding, never re-search; `ct-samplesize` computes n (this skill provides the parameter framework only); `meta-analysis` handles R meta plots; `ct-base` = internal base (i18n / excel_style / series safety model).

## China Regulatory Depth (C-layer)

CTA/IND 60-day tacit approval, Type A/B/C communication meetings, registration ≠ tacit approval — see `knowledge/ref-regulatory-versions.md` + `knowledge/reference-index.md`; verify any version / status / deadline in real time against the official original.

## Quality Gate & Stop Rules

Pre-delivery checks and stop conditions live in `knowledge/system_prompt.md` "Quality gate & stop rules". Core red line: **never expose in user-visible content personal info, subject info, unpublished project data, private path or access credential.**

**Presentation rules (user-mandated, hard)** — deliver only the answer (refined stdout) + essential cited basis. **Never emit any workflow / process narration to the user** — this explicitly covers: step 0–6 labels ("Step 2", "Gate 0", "Step 6"), difficulty tags (`simple` / `middle` / `complex` / `vague`), race / serial / fire-only mechanics, routing / triage narration, progress / status broadcasts, self-process recaps, memory / CHANGELOG housekeeping notes, follow-up CTAs, redundant closing summaries, internal-pipeline wording ("refined by Coze", "assembling payload"), and disclosure of internal knowledge sources. Internal reasoning may still use these labels freely — they just must **never** appear in user-visible text. See ct-base §6.2 / §6.3.

**🔔 Serial-mode user notice (the ONLY allowed process message)** — when the question is judged `complex` (serial mode, step 5 foreground Coze) **or** when external data / sample-size handoff (step 3 / 4) is required, emit **exactly one** brief user-facing notice **before** the long call, e.g.:
> 您的这个问题比较复杂，分析结果需要做模型精校，请耐心等候。

(English: `Your question is fairly complex; the analysis needs model refinement — please wait.`) Do **NOT** repeat it, do **NOT** add any other process chatter. simple / middle (race) mode must stay completely silent on process.

## Changelog — full history (0.8.0 → 0.9.30+) → **[CHANGELOG.md](CHANGELOG.md)**
