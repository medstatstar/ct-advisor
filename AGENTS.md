# AGENTS.md — ct-advisor v1.1.0 (ct- series A-tier entry point)

> This document is ct-advisor's self-improvement contract. It follows ct-base AGENTS.md structure and is written in English per §4 (references·AGENTS are English-only for published ct- skills).

## Skill Overview

`ct-advisor`: the single front door for the entire `ct-*` clinical-trial skill family — a methodology & regulatory-evidence advisor (A-tier) that routes real-data / competitive-intel asks to sibling data skills (ct-registry / ct-safety / ct-literature / ct-samplesize / meta-analysis). **All domain expertise lives on the Coze cloud side. The local side retains ZERO knowledge base and performs ZERO local network retrieval.**

## 🔴 Core Architecture (v1.1.0, 2026-09-24)

**The local LLM is a PIPE, not an author.** Its ONE AND ONLY action is:

```bash
python scripts/entry.py --q "<user question>" [--attach "<path>"]
```

**Everything else — difficulty labeling, attachment decoding, clarify loops, Coze forwarding, skill delegation — is done by code inside entry.py. The local LLM has NO decision space.**

---

## Core Rules

### 1. Environment Detection
- Python via Anaconda (`C:\Tools\anaconda3\python.exe`).
- R via `C:\Tools\R-4.6.1\bin\x64\Rscript.exe`.

### 2. Code Execution
- **No code execution by the agent.** The agent calls `entry.py` which internally orchestrates everything.
- The agent MUST NOT call `route.py`, `refine_answer.py`, `orchestrate.py`, `clarify_loop.py`, or any other pipeline script directly.

### 3. Language Detection
- Follows OS locale; bilingual auto-switch via code (no agent action needed).

### 4. Security Red Line
- **No local knowledge base** — the `knowledge/` directory has been removed entirely.
- **No local network retrieval** — `search_refs.py`, `update_reference_index.py`, and `search-sites.md` have been removed.
- **No web search fallback** — if Coze fails, the user is told to retry; the LLM does not fabricate answers from its own knowledge.
- **Outbound authorization** — `ct-advisor.coze.site/run` is pre-whitelisted; the agent MUST NOT edit `config.json`.

### 5. Self-Improving
- Record LRN / ERR / FEAT entries per the self-improving-agent skill format.
- Promote recurring patterns to long-term memory automatically.
- Workflow/tool changes → workspace `AGENTS.md`; behavior → `~/.workbuddy/SOUL.md`.

---

## Self-Improving Trigger Conditions
- Record LRN / ERR / FEAT entries per the self-improving-agent skill format.
- Promote recurring patterns (Recurrence-Count ≥ 3, across ≥ 2 tasks) to long-term memory automatically.
- Behavior/communication/UX → `~/.workbuddy/SOUL.md`; workflow/tool/infrastructure → workspace `AGENTS.md`; cross-project user prefs → `~/.workbuddy/MEMORY.md`; project-level → `.workbuddy/memory/MEMORY.md`.

---

## Dependencies

### Sibling data/compute skills (routed via Coze, not embedded)
- `ct-registry` — trial-registry landscape
- `ct-safety` — FAERS safety signals
- `ct-literature` — published literature
- `ct-samplesize` — sample-size & power handoff
- `meta-analysis` — referral-only (forest / funnel / rob2 plots)

### Internal base
- `ct-base` (library, not invocable) — shared helpers and canonical BASE.md spec.

## Attachment formats (v1.23 · 2026-09-23)

| 格式 | 处理 |
|---|---|
| `.docx` / `.xlsx` / `.pptx` | 本地 `scripts/office_to_md.py`（先过 5 MB 体积门）→ 把 md 追加进 question |
| `.doc` / `.xls` / `.ppt`（老格式） | **原样转发字节**：`scripts/doc_memory.py::build_file_payload()` → `doc_context.mode=file`；**由 Coze 端**纯标准库解码 |
| `.pdf` | Coze 端 `pypdf` 兜底 |

## Deliverable boundary (v1.24 · 2026-09-23)

The deliverable of this skill is **text only**. When the user asks for the revised document back, say on the **first line** that this feature is **not available** — only written suggestions — and then provide the suggestions as copy-ready text.
