---
displayName: 临床试验顾问 / Clinical Trial Advisor
name: ct-advisor
cn_name: 临床试验顾问
slug: ct-advisor
version: 0.8.0
triggers:
  - "ct console"
  - "ct 控制台"
  - "ct 技能入口"
  - "临床试验技能入口"
  - "ct skills hub"
  - "临床试验情报"
  - "ct-advisor"
  - "临床试验顾问"
  - "临床试验方法学顾问"
dependencies:
  - {slug: ct-registry,   tier: B, purpose: "Trial-registry landscape (CT.gov / CDE / WHO ICTRP / EU-CTR / ChiCTR / ISRCTN / DRKS)"}
  - {slug: ct-safety,     tier: B, purpose: "Safety signals (FAERS PRR / ROR / IC)"}
  - {slug: ct-literature, tier: B, purpose: "Published literature (OpenAlex / Europe PMC / Semantic Scholar)"}
  - {slug: ct-samplesize, tier: A, purpose: "Sample-size & power computation (handoff from workflow C)"}
summary: 面向临床研发全生命周期的 ct 系列「总入口」，是方法学、法规证据、实际操作细节等各方面内容的总顾问：方法学/设计/合规/QC/语气类问题在内部走 A–J 工作流自行解答；统计计算转交 ct-samplesize，原始数据/竞品情报类需求通过 Skill 工具路由到 ct-registry / ct-safety / ct-literature 三个数据源；竞品情报总览由本技能自行缝合三源产出。所有回答均经双大模型交叉核查，确保结论正确可靠。
description: "面向临床研发全生命周期的 ct 系列「总入口」，是方法学、法规证据与实操细节的总顾问：方法学/设计/合规/QC/语气类问题在内部走 A–J 工作流自行解答；统计计算转交 ct-samplesize；原始数据/竞品情报类需求通过 Skill 工具路由到 ct-registry / ct-safety / ct-literature 三个数据源；竞品情报总览由本技能自行缝合三源产出。所有回答均经双大模型交叉核查，确保结论正确可靠。 / The ct-series TOTAL ENTRY POINT across the full clinical-development lifecycle — your overall advisor for methodology, regulatory evidence, and hands-on operational detail. Methodology / design / compliance / QC / tone questions are answered in-house through workflows A–J; sample-size computation is handed to ct-samplesize; raw-data and competitive-intel needs are routed via the Skill tool to the three sibling data skills (ct-registry / ct-safety / ct-literature); the full competitive-intel picture is stitched in-house from those three sources. Every answer is cross-checked by a dual-model review to ensure correctness and reliability."
license: MIT
tier: B
metadata:
  openclaw: { emoji: "🛠️", icon: "assets/icon.svg" }
  authors: ["medstatstar", "phoe-zip"]
  family: ct-series
  homepage: "https://github.com/medstatstar/ct-advisor"
---

# Clinical Trial Advisor

## Language

- **English guide** → [README.md](https://github.com/medstatstar/ct-advisor/blob/main/README.md)
- **中文指南** → [README_zh-CN.md](https://github.com/medstatstar/ct-advisor/blob/main/README_zh-CN.md)

This skill responds in the user's input language and auto-switches; runtime prompts switch by locale. SKILL.md body is English-only (agent-facing); bilingual walkthroughs live in the two READMEs.

## Requirements

| Item | Requirement | Notes |
|---|---|---|
| Runtime | Agent (LLM) reads `knowledge/` directly | **No mandatory dependency** — pure methodology (workflows A–J) runs fully offline. |
| Optional CLI helpers | `python3` (stdlib only) | `scripts/menu.py`, `scripts/check_deps.py`, `scripts/search_refs.py` use only the Python standard library — **no third-party packages** (PyYAML removed; `scripts/*.json` is loaded via `json`). |
| Sibling data/compute skills | `ct-registry`, `ct-safety`, `ct-literature`, `ct-samplesize` | Only needed for `data_intel` routing & layer-B data grounding; missing ones degrade gracefully (never fabricate). Methodology works without them. The full competitive-intel brief is stitched in-house from the three data skills (no separate orchestrator skill). |
| Coze mode (optional) | `config.json` `backend: coze` + `coze.bot_id`; `requests` at runtime | Disabled by default. The `adapters/` Coze stubs are **not executed** in local mode. |
| Outbound network | None in default (local) mode | Only the routed sibling skills make network calls; this skill itself stays zero-outbound unless you invoke them. |

## This skill is an "orchestration front-door", not a "monolithic reasoner"

Seams pre-split for a future Coze endpoint (swappable adapter layers):

| Concern | Location | Local default | After Coze plug-in |
|---|---|---|---|
| Methodology knowledge (portable) | `knowledge/` | system_prompt.md + scripts/workflows.json + ref-*.md | push the whole pack to the bot as its knowledge base |
| Reasoning exit | `adapters/backend.py` | local mode **does not** go through this layer: the agent reads `knowledge/` directly to answer; this module is only for the Coze backend | `CozeBackend` (HTTP → bot, stub implemented) |
| Data grounding | `adapters/data_context.py` | `LocalDiskDataContext` (scans sibling-skill outputs) | `CozeApiDataContext` (stub) |
| Q&A persistence | `adapters/qa_store.py` | `JsonlStore` (local JSONL) | `RemoteDbStore` (stub) |
| Outbound sanitization | `adapters/sanitize.py` | always on | always on |
| Runtime selection | `config.json` | `backend: local` (zero outbound) | `backend: coze` + `coze.bot_id` |

## Local-mode execution flow (default, zero outbound)

> In local mode the agent **reads the knowledge pack under `knowledge/` directly** and answers; it does **not call** any Python in `adapters/` (those modules are only for the Coze backend and are unused in local mode). All outbound / sanitization logic only truly takes effect in Coze mode.

1. **Clarification gate (gate 0) — triage first (friendly menu policy)**: classify the user's first message as **simple** (specific, single-intent, answerable directly → answer in one pass, **no menu**), **complex** (multi-decision / needs a workflow choice → present the clarification menu, confirm step by step), or **vague** (need unclear / user undecided → enter **grill-me clarify mode**, Workflow K, to scope step by step). Default to the friendliest path: when in doubt between simple and complex, give a short direct answer + an optional deeper-menu offer (`clarify.triage_simple`) rather than forcing a menu. Only open the full menu when step-by-step confirmation genuinely helps. For a vague ask present the **clarification menu** (`scripts/menu.json`, rendered via canonical strings in `scripts/i18n.py` / `knowledge/prompts.md`) or invite grill-me (`clarify.vague_invite`): Tier 0 profile (role / stage / input) → intent area → workflow A–J → within-workflow sub-intent → output format. For a still-vague ask use `AskUserQuestion` to ask **only 1–3** conclusion-changing high-value questions per round (e.g. comparison type / estimand strategy / primary endpoint / population) until the problem profile is complete; for high-risk formal answers confirm the profile with one sentence before answering (rule in `scripts/workflows.json` `gate`).
2. **Route**: pick workflow A–J or a composite route from `scripts/workflows.json` (e.g. "confirmatory trial design" = 0 → B → C → D → E).
3. **Assemble payload (documentation only, no outbound)**: `question + workflow + jurisdiction + data_refs + constraints`; local mode sends no network request, this step is only a self-check for completeness.
4. **Answer**: combine `knowledge/system_prompt.md` methodology rules + `scripts/workflows.json` routing + `ref-*.md` topic notes to produce advice; never fill factual gaps with fluent wording.
5. **Data grounding (layer B, on demand)**: when advice needs real-data support, read sibling-skill outputs per `scripts/workflows.json` `integration.data_grounding` (CDE trial count, FAERS signals, literature, competitor brief), explicitly label "Data source: ct-xxx on <date>". **Pure methodology / design / compliance questions with no data need may skip this step** and state "no data grounding performed".
6. **Handoff (workflow C)**: when sample-size / power parameters are complete → hand off to `ct-samplesize` for actual computation. Handoff payload template:
- Design: two independent samples / paired / survival etc.; comparator type (placebo / active); superiority / non-inferiority / equivalence; allocation ratio
- Test: one- / two-sided, α, power
- Effect size: continuous → Δ + pooled SD; binary → two-group rates; survival → HR
- Add: dropout / unevaluable rate `dropout` → `n_adj = n / (1 − dropout)`
- computed by `ct-samplesize`; **this skill does not compute n in-house**.
7. **Persist (workflow J)**: when the user explicitly asks to remember a preference / decision → use the existing WorkBuddy memory mechanism (explicit authorization required), do not create files and do not call `qa_store.py`.

## Boundaries with other ct skills

| Skill | What it does | Relationship with this skill (ct-advisor) |
|---|---|---|
| `ct-registry` | Search trial registries & normalize | It "finds trials"; this skill "explains / designs / ensures compliance", reads its output for data grounding, does not re-search. |
| `ct-safety` | FAERS signal detection | It "computes signals"; this skill does qualitative classification & report-path judgment, reads its signals to support monitoring advice. |
| `ct-literature` | Public-literature search & normalization | It "finds literature"; this skill reads its output to argue methodology precedent, does not re-search. |
| `ct-samplesize` | Sample-size & power computation | It "computes n"; this skill "gives the parameter framework in workflow C", hands off once complete. |
| `ct-base` | Internal base (D-tier) | This skill is a B-tier published skill; reuses ct-base's `i18n.py` / `excel_style.py` for generic & Excel strings, and ships its own `scripts/i18n.py` for advisor-specific user prompts. |

## Routing & total-entry (absorbs the `ct` console router)

ct-advisor is now the **single entry point** for the whole ct series. It absorbed the former `ct` console: you no longer open a separate dispatcher — say "ct console / 临床试验技能入口" (or just ask) and this skill routes. It **re-implements no retrieval/analysis logic**; it delegates real-data and compute work to the sibling skills via the Skill tool, exactly as the old console did.

**Three entry capabilities** (see `scripts/menu.json` `flows:`; the clarification menu asks which one):

| Need | Route | How |
|---|---|---|
| Methodology / design / statistics / estimand / GCP / DSUR / CSR / methodology QC / tone writing / local memory | **Answered in-house** (workflows A–J) | No Skill-tool handoff; this skill reasons from `knowledge/`. |
| Not sure what I need / want help scoping the question | **Clarify mode (grill-me)** | In-house; agent asks 1–3 branching questions per round (each with a recommended default), builds a needs portrait + recommends a route (methodology workflow A–J or data_intel skill). No Skill-tool handoff, no network. |
| A drug's / indication's **registered trials** (planned / recruiting / completed, competitor landscape) | **ct-registry** | Skill tool `skill="ct-registry"`; cross-source (CT.gov / CDE / WHO ICTRP / EU-CTR / ChiCTR / ISRCTN / DRKS). |
| **Safety signals** for a drug–event pair (PRR / ROR / IC on FAERS) | **ct-safety** | Skill tool `skill="ct-safety"`; FDA FAERS via openFDA. |
| **Published evidence** (papers / systematic reviews / RCTs) | **ct-literature** | Skill tool `skill="ct-literature"`; OpenAlex + Europe PMC + Semantic Scholar. |
| **Full competitive-intel picture** of a drug / indication (one consolidated Strategic Brief) | **ct-registry + ct-safety + ct-literature (stitched in-house)** | Call all three data skills (`skill="ct-registry"` / `skill="ct-safety"` / `skill="ct-literature"`) once each, then stitch the Strategic Brief yourself. **Recommended default for broad asks.** |
| Sample-size / power computation | **ct-samplesize** | Handoff from workflow C once parameters are complete. |

When the ask is **broad** ("竞争情报 / 格局 / 某药全貌 / strategic brief"), call **ct-registry + ct-safety + ct-literature** once each and stitch the brief in-house; when **narrow** (one specific dimension), route to the matching focused skill. When the ask is **methodology / design / compliance / QC / tone**, answer in-house via the clarification menu → workflow A–J. **Skip the menu** when the user's first message already names a clear target.

> **🚫 HARD RULE — trio for broad asks, single atomic for narrow, never redundant**: there is no one-stop orchestrator skill anymore. For a broad ask, call `ct-registry` + `ct-safety` + `ct-literature` **once each** and stitch the Strategic Brief yourself; for a narrow ask, call **only** the one matching skill. Do **not** call all three when the user asked a single dimension (that is redundant retrieval and double counting against any usage quota).

> The data/compute skills stay modular and independent; this skill only *routes* to them and reads their REAL outputs for data grounding. Deleting the old `ct` console is safe — its routing table is reproduced above.

> **A sibling data/compute skill is missing?** This skill *routes* but does **not** re-implement retrieval or computation logic — so a target skill must be installed to actually fetch data. Handle it gracefully (never fabricate, never fail silently):
> - **If you already know it is missing** (the user told you, or `python3 scripts/check_deps.py` reports it missing), **skip the Skill call**. Tell the user: (1) which skill is required; (2) how to install it — *same source as ct-advisor* (SkillHub / GitHub / local copy); (3) the **methodology prep** you can still do (draft the query, list the registries / fields that matter, outline the analysis framework); (4) explicitly label the reply **"未实际取数 / data not retrieved"**.
> - **If you already called the Skill tool and it errored** (skill not found), catch it and degrade the same way — never invent trials, signals, literature or sample size to fill the gap.
> - `ct-samplesize` missing → workflow C still outputs the sample-size **framework** + information gap; tell the user to install it to compute `n`.

> To see which sibling skills are installed right now, run `python3 scripts/check_deps.py` (local-only probe; it installs nothing and makes no network calls). Methodology (workflows A–J) works fully offline regardless.

## China regulatory depth (C-layer)

CTA / IND 60-day tacit approval, communication meetings (Type A / B / C), registration ≠ tacit approval, etc. — see `knowledge/ref-regulatory-versions.md` (controlled version quick-reference, with ⚠️ and check fields) + `ref-regulatory-statistical.md`. Any version / status / deadline conclusion must be verified in real time against the official original per the snapshot's "fields to check".

## Switching to Coze (future, no methodology rewrite needed)

`adapters.build_backend(config.json)` reads the `backend` field; once `coze.bot_id` is ready, take `CozeBackend`, push the same `knowledge/` to the bot as its knowledge base, and fill in the Coze implementations of `DataContextProvider` / `QASessionStore`. Outbound payload always goes through `sanitize()` first — never carry PII / confidential fields / token (per ct-base §11).

## Quality gate & stop rules

Pre-delivery checks and stop conditions are in `knowledge/system_prompt.md` "Quality gate & stop rules". Core red line: **never expose in user-visible content personal info, subject info, unpublished project data, private path or access credential.**

## Topic reference routing

- Cross-domain synthesis / full lifecycle / comprehensive QC: `knowledge/ref-clinical-operations.md`
- ICH E2 / E3 / E6 / E9, CTD / M4, NMPA / CDE, DSUR / CSR: `knowledge/ref-regulatory-statistical.md` + `ref-regulatory-versions.md`
- Clarification / tone writing / local memory: `knowledge/ref-interaction-style.md`
- Locate topic content: `python3 scripts/search_refs.py "estimand|intercurrent event|sensitivity"`

---

## Changelog

Full version history (0.1.0 → 0.7.11, 30+ entries) lives in **[CHANGELOG.md](CHANGELOG.md)**.
