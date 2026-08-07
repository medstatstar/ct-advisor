# AGENTS.md — ct-advisor v0.9.13 (ct- series B-tier entry point)

> This document is ct-advisor's self-improvement contract. It follows ct-base AGENTS.md structure and is written in English per §4 (references·AGENTS are English-only for published ct- skills).

## Skill Overview

`ct-advisor`: the single front door for the entire `ct-*` clinical-trial skill family — a methodology & regulatory-evidence advisor (B-tier) that routes real-data / competitive-intel asks to sibling data skills (ct-registry / ct-safety / ct-literature / ct-samplesize / meta-analysis) and stitches the full competitive-intel brief in-house. Pure methodology (workflows A–J) runs fully offline from the local knowledge pack under `knowledge/`.

---

## Core Rules

### 1. Environment Detection
- Python via Anaconda (`C:\Tools\anaconda3\python.exe`); R via `C:\Tools\R-4.5.1\bin\x64\Rscript.exe`.
- Optional CLI helpers (`scripts/*.py`) use stdlib only — no third-party packages.

### 2. Code Execution
- Default: SAFE PREVIEW (dry-run). Generated code is displayed, NOT executed unless `--yes` / `-y`.
- Runtime I/O: prefer stdin/stdout pipes over temp files (ct-base §6.1). The step-7 payload is piped via heredoc (`<<'PYEOF'`); never write intermediate payload files.
- ⚠️ Quoting red line (2026-08-04): never use `python3 -c "..."` for nested-quote payloads — ASCII apostrophes / full-width parens break the string and cause silent fallback to local draft. Use quoted heredoc only.
- ⚠️ **Windows heredoc + Chinese JSON — definitive solution (updated 2026-08-05)**
  - **Root cause**: when a Windows bash heredoc passes Chinese JSON containing full-width parens `（）`, it raises `SyntaxError: invalid character '）' (U+FF09)`, silently falling back to the local draft (Coze not called).
  - **Preferred: in-memory `refine_direct` call (agent imports in a Python context)**
    ```python
    import sys
    sys.path.insert(0, r"C:\Users\WintoneFileSrv\.workbuddy\skills\ct-advisor")
    from scripts.run_refined import refine_direct

    answer = refine_direct(
        query_meta={"category": "design", "difficulty": "middle", "accuracy": "good"},
        original_question="设计一个III期双盲RCT评估新抗肿瘤药物的PFS终点",
        draft_answer="草稿...",
    )
    ```
    - completely avoids JSON encoding / command-line arg passing; zero encoding issues
    - Coze result is written directly into a variable, ready for further processing or output
  - **Alternative: base64 command-line call to `run_refined.py`**
    ```powershell
    # PowerShell (recommended)
    $payload = @{query_meta='{...}'; original_question='...'} | ConvertTo-Json -Compress
    $b64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($payload))
    python scripts/run_refined.py --payload-b64 $b64
    ```
    - base64 encoding fully bypasses Chinese / full-width character encoding issues
    - only for environments where import is impossible (e.g. non-Python contexts)
  - **Hard prohibitions**:
    - never create temp files inside the skill dir / workspace (the safe-delete hook blocks relative-path deletion)
    - never use `python -c "..."` to pass JSON containing full-width symbols (uncontrolled encoding)
- ⚠️ **Windows heredoc Chinese-JSON pitfall (2026-08-05)**: a Windows bash heredoc passing Chinese JSON with full-width parens/quotes raises `SyntaxError: invalid character '）' (U+FF09)`, causing a silent fallback to the local draft (Coze not called). Alternatives:
  - Option A (recommended): use `tempfile.mkstemp(suffix='.py', text=True)` to write an absolute-path .py file + `os.unlink()` to clean up
  - Option B: use `python -c "..."` + `sys.stdin.buffer` byte stream (still mind nested quotes)
  - hard prohibition: never create temp files inside the skill dir / workspace (the safe-delete hook blocks relative-path deletion)

### 3. Language Detection (ct-base bilingual policy)
- Default follows OS locale (English unless `zh-*`); one-sentence switch supported via `scripts/switch_lang.py <lang> [--permanent]` (session or permanent in `config.json` `language`).
- `scripts/i18n.py`: 147 keys, all EN+ZH paired (single source of truth).
- Code output always English.

### 4. Security Red Line (highest priority)
- Methodology (workflows A–J) runs zero-outbound from the knowledge pack.
- Answer refinement uses Coze — the one outbound path; difficulty-aware: simple/middle race, complex serial; all payloads pass through `sanitize()` first.
- Never expose personal info, subject data, unpublished project data, private paths, or credentials.
- `permissions` block declared in SKILL.md top-level.

### 5. Reuse from base
- ct-advisor ships its own `scripts/i18n.py` (advisor-specific user prompts); reuses ct-base `i18n.py` / `excel_style.py` for generic & Excel strings where applicable.
- Bilingual single source of truth: the embedded dict in `scripts/i18n.py` (no separate json file; `knowledge/prompts.md` is the agent-facing mirror of the key table and MUST stay in sync).

### 6. Interaction / Menu Design
- ct-advisor implements the §6.2 triage policy fully: `simple` → direct answer (no menu); `complex` → popup routing menu with "explain the differences" entry; `vague` → grill-me branch-by-branch probing (1–3 questions/round).
- Clarification menu (`scripts/menu.json`) + canonical strings (`scripts/i18n.py` / `knowledge/prompts.md`).

### 7. Grounding Hard Rule (§6.1, inherited)
- Every factual / normative assertion must be traceable — cite `ref-*.md` §N or official clause; untraceable claims must be flagged `⚠️ 官方核实`.
- `grounding.require_cite` / `official_verify` / `low_confidence` keys in `prompts.md` and `i18n.py` are mirror images — always consistent.

---

## Self-Improving Trigger Conditions
- Record LRN / ERR / FEAT entries per the self-improving-agent skill format.
- Promote recurring patterns (Recurrence-Count ≥ 3, across ≥ 2 tasks) to long-term memory automatically.
- Behavior/communication/UX → `~/.workbuddy/SOUL.md`; workflow/tool/infrastructure → workspace `AGENTS.md`; cross-project user prefs → `~/.workbuddy/MEMORY.md`; project-level → `.workbuddy/memory/MEMORY.md`.

---

## Dependencies

### Sibling data/compute skills (routed, not embedded)
- `ct-registry` (B) — trial-registry landscape
- `ct-safety` (B) — FAERS safety signals
- `ct-literature` (B) — published literature
- `ct-samplesize` (A) — sample-size & power handoff (workflow C)
- `meta-analysis` (B) — forest / funnel / rob2 plots

### Internal base
- `ct-base` (library, not invocable) — shared i18n/r_libs helpers and canonical BASE.md spec.
