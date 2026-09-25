---
slug: ct-advisor
name: ct-advisor
displayName: Clinical Trial Chief Advisor / 临床试验总顾问
cn_name: 临床试验总顾问
version: 1.1.0
invocable: true
required_commands: [python]
summary: "面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问。所有问题（方法学/设计/合规/QC/现场执行/情报）统一提交云端 Coze 引擎分析处理。本地仅做确定性代码分级与附件解码，不保留知识库，不进行本地网络检索。"
description: "The single entry point for the ct-series across the full clinical-development lifecycle — a cloud-assisted clinical trial advisor. All questions (methodology / design / compliance / QC / site-execution / intelligence) are forwarded to the cloud Coze engine for analysis. The local side only performs deterministic code-based difficulty labeling and attachment decoding; no knowledge base is retained locally, and no local network retrieval occurs. / 面向临床研发全生命周期的 ct 系列「总入口」，云端辅助的临床试验总顾问。所有问题（方法学/设计/合规/QC/现场执行/情报）统一提交云端 Coze 引擎分析处理。本地仅做确定性代码分级与附件解码，不保留知识库，不进行本地网络检索。"
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
trigger_scope: "触发词仅限临床试验方法学/法规/设计/合规/QC/情报类问题；不主动匹配非临床类通用问答；不含文件系统写入与系统级 API 调用。"
metadata:
  openclaw: { emoji: "🛠️", icon: "assets/icon.svg" }
  authors: ["medstatstar", "phoe-zip"]
  family: ct-series
  homepage: "https://github.com/medstatstar/ct-advisor"
permissions:
  scope: "user-space-only"
  network: "controlled-coze-opt-in"
  network_note: "All questions are forwarded to Coze (single call, internal `scripts/orchestrate.py`). Local side performs NO knowledge base lookup, NO local network retrieval, NO web search. Attachment decoding is done locally via `scripts/office_to_md.py` (stdlib-only), then the decoded text is appended to the payload and forwarded to Coze. The Coze-side knowledge base is the single source of truth."
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

## Language

- **English guide** → [README.md](https://github.com/medstatstar/ct-advisor/blob/main/README.md) · **中文指南** → [README_zh-CN.md](https://github.com/medstatstar/ct-advisor/blob/main/README_zh-CN.md)
- **This SKILL.md body is English-only, agent-facing.** Bilingual walkthroughs live in the two READMEs.
- Bilingual auto-switch: the answer language follows the user's question language.

## 🔴 HIGHEST PRIORITY: entry.py is the ONLY permitted action

> **The local LLM is FORBIDDEN from making any decisions in this skill. Its ONE AND ONLY allowed action is:**
>
> ```bash
> python scripts/entry.py --q "<user question>" [--attach "<path>"]
> ```
>
> **and then pipe the stdout to the user verbatim.**

**HARD GATE — the following are absolutely PROHIBITED for the local LLM:**
- ❌ **NEVER** read, search, or reference any local knowledge base (the `knowledge/` directory has been removed)
- ❌ **NEVER** perform any local network retrieval or web search (`references/search-sites.md` has been removed)
- ❌ **NEVER** answer the question from the LLM's own knowledge — all domain expertise lives on the Coze side
- ❌ **NEVER** bypass `entry.py` by calling `route.py`, `refine_answer.py`, `orchestrate.py`, or any other script directly
- ❌ **NEVER** rewrite, rephrase, reorder, summarize, or "polish" the text between `<<<CT_ANSWER_START>>>` and `<<<CT_ANSWER_END>>>`
- ❌ **NEVER** append a summary, lead-in, closing remark, or "key takeaways" before or after the delimiters
- ❌ **NEVER** strip or alter the `checksum:` line that follows `<<<CT_ANSWER_END>>>`
- ❌ **NEVER** translate or align language (the code already handles that)
- ❌ **NEVER** inject process narration ("Step 2", "Coze returned", "assembling payload")
- ❌ **NEVER** decide whether to forward to Coze — ALL questions are forwarded (entry.py handles routing internally)

**Why this rule exists:** The local LLM's "helpful" instincts (answering from its own knowledge, pre-reading files, post-formatting answers) have repeatedly violated the pipeline contract, destroyed Coze-delivered content formatting, altered numeric precision, injected unsolicited content, and bypassed the cloud analysis entirely. This rule eliminates ALL local LLM decision space.

## How to use this skill

### With a question only:
```bash
python scripts/entry.py --q "在 III 期 NSCLC 患者中，对比 pembrolizumab 与化疗，主要终点 OS 的样本量如何估算？"
```

### With an attachment:
```bash
python scripts/entry.py --q "这个文档和医学有关吗" --attach "/path/to/file.docx"
```

**That's it.** The stdout is the final answer — pipe it to the user verbatim.

### What entry.py does internally (all code, zero LLM):
1. **Attachment decoding** — if `--attach` is provided, decodes OOXML (`docx`/`xlsx`/`pptx`) via `scripts/office_to_md.py` (stdlib-only) and appends the decoded text to the question
2. **Difficulty labeling** — runs `scripts/route.py` (deterministic regex, LLM-free) → `simple` / `middle` / `complex` / `vague`
3. **Clarify loop** (if `vague`) — runs `scripts/clarify_loop.py` (pure-local heuristic menu, ≤3 rounds) → asks the user up to 3 clarifying questions, then continues
4. **Forward to Coze** — calls `scripts/orchestrate.py` internally → parallel Coze fire + ct-skill prefetch → merge → emit `<<<CT_ANSWER_START>>>` ... `<<<CT_ANSWER_END>>>` wrapped answer with sha256 checksum
5. **Delegate handling** — if Coze returns a `<<<CT_TOOL_DELEGATE>>>` block, entry.py automatically executes `scripts/refine_answer.py --card-inline` (code runs the ct skill, stitches the result, re-wraps in delimiters)

### Output format:
```
<<<CT_ANSWER_START>>>
{answer text from Coze}
<<<CT_ANSWER_END>>>
checksum: {sha256[:16]}
```

### 🔴 sha256 Anti-tamper Check (HARD GATE):
After receiving the stdout from `entry.py`, the local LLM **MUST** verify the checksum before passing the answer to the user:

```python
import hashlib, re
stdout = "...(entry.py output)..."
m = re.search(r'<<<CT_ANSWER_START>>>\n(.*?)\n<<<CT_ANSWER_END>>>\nchecksum: (.+)', stdout, re.DOTALL)
if m:
    answer, expected_checksum = m.group(1), m.group(2).strip()
    actual_checksum = hashlib.sha256(answer.encode("utf-8")).hexdigest()[:16]
    if actual_checksum != expected_checksum:
        # TAMPER DETECTED — do NOT pass to user
        print("⚠️ 答案完整性校验失败，请重试。")
    else:
        # OK — pass answer verbatim
        print(answer)
```

**If the checksum does not match, the local LLM MUST NOT deliver the answer to the user.** This prevents any silent tampering.

## Requirements

| Item | Requirement |
|---|---|
| Runtime | `python3` stdlib only |
| Sibling skills | **Tier A · listed on SkillHub** (non-confidential input, publicly released): `ct-registry` / `ct-safety` / `ct-literature` / `ct-samplesize` — auto-routed via Coze `need_tool` (entry.py handles card-inline execution). **Tier A · NOT yet listed**: `ct-pipeline` / `ct-synthdata` → `unpublished_a`, answer from Coze draft. **Tier B** (confidential input, **not publicly released**): `ct-protocol` / `ct-csr` / `ct-analysis` / `ct-sdtm` / `ct-eligibility` etc. — never installable. |
| Refiner (Coze) | `scripts/entry.py` (internal orchestrator via `scripts/orchestrate.py`) POSTs payload to `ct-advisor.coze.site/run`. Credential embedded in `adapters/coze_token_embedded.py` (obfuscated public token — keep as-is). 90s timeout / 300s long timeout. |

## Attachment handling (docx / xlsx / pptx · doc / xls / ppt · pdf)

**Governance pointer (2026-08-19 rollback):** the layered conversion strategy, user prompts, and confidentiality boundary are consolidated into **ct-base §6.7** (`ct-base/docs/03-interaction-constraints.md`); this skill no longer re-declares them. The shared converter lives in `ct-base/scripts/office_to_md.py` (injected into each skill at publish).

**Format matrix (2026-09-23 · one gate = 5 MB, enforced by `office_to_md.py`)**

| Format | Decoded where | Mechanism |
|---|---|---|
| `.docx` / `.xlsx` / `.pptx` | **locally** | `scripts/office_to_md.py` (stdlib-only; no Office needed) → md → appended to question |
| `.doc` / `.xls` / `.ppt` (**legacy OLE2**) | **on the Coze end** | local forwards the **raw file bytes** (`doc_context.mode=file`); Coze decodes |
| `.pdf` | local `pdf` skill, else Coze `pypdf` | text layer only; a scanned/image PDF has no text → tell the user |
| `.txt` / `.md` / `.csv` / `.tsv` / `.json` | locally | read directly |

**Deliverable boundary — the revised document is never returned (v1.24).** This skill's deliverable is **text only**: it does not generate, export, or hand back a modified document file. When the user asks for the revised file back, state plainly on the **first line** that **this feature is not available — only written suggestions are provided**, then give the suggestions as text the user can copy.

## Quality Gate & Stop Rules

**Presentation rules (user-mandated, hard)** — deliver only the answer text between `<<<CT_ANSWER_START>>>` and `<<<CT_ANSWER_END>>>`. **Never emit any workflow / process narration to the user.**

**🔔 Forward-mode user notice (the ONLY allowed process message)** — entry.py emits a brief notice to stderr before firing the Coze call. The local LLM should not add any additional process chatter.

## Outbound Authorization Gate

Runs automatically inside `entry.py` → `scripts/orchestrate.py` before each outbound HTTP call (agent never triggers it manually). Endpoint `https://ct-advisor.coze.site/run` is in `auto_approve_endpoints` by default, so it never prompts. If the user wants another endpoint whitelisted across sessions, the USER adds it explicitly to `config.json` — **the agent MUST NOT edit `config.json`**.

## Bug Report (§20.3 · ct-base)

On defect detection or explicit user request, `adapters/bug_report.py` offers a sanitized 11-key report to `https://ct-bugreport.coze.site/run`. Two-stage confirmation mandatory.

## Changelog — full history (0.8.0 → 1.0.0+) → **[CHANGELOG.md](CHANGELOG.md)**

### v1.1.0 (2026-09-24) — Zero-LLM-intervention architecture

- **Removed `knowledge/` directory entirely** — all domain knowledge lives on the Coze side (single source of truth)
- **Removed `scripts/search_refs.py`, `scripts/update_reference_index.py`, `references/search-sites.md`** — no local knowledge lookup, no local network retrieval, no web search fallback
- **Added `scripts/entry.py`** — single code entry point that serializes: attachment decode → route.py → clarify_loop (if vague) → orchestrate.py → card-inline auto-execution. The local LLM's only action is to call entry.py and pipe stdout.
- **Removed all agent-side workflow steps (steps 0–6)** — replaced with the single entry.py call pattern
- **Removed all agent delegation language ("you must call ...", "you should ...")** — the code now orchestrates itself; the local LLM is a pure pipe
- **sha256 tamper-check** — entry.py emits a checksum after `<<<CT_ANSWER_END>>>`; the local LLM must verify it before delivering the answer
- **Eliminated all local fallback paths** — if Coze fails, the answer says "please retry" — the local LLM no longer has any knowledge base to fall back to
- **Updated AGENTS.md** to reflect the new zero-local-knowledge architecture
