# AGENTS.md — ct-advisor v0.9.70 (ct- series A-tier entry point)

> This document is ct-advisor's self-improvement contract. It follows ct-base AGENTS.md structure and is written in English per §4 (references·AGENTS are English-only for published ct- skills).

## Skill Overview

`ct-advisor`: the single front door for the entire `ct-*` clinical-trial skill family — a methodology & regulatory-evidence advisor (A-tier) that routes real-data / competitive-intel asks to sibling data skills (ct-registry / ct-safety / ct-literature / ct-samplesize / meta-analysis) and stitches the full competitive-intel brief in-house. Methodology knowledge (workflows A–J) is retrieved locally from the `knowledge/` pack.

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

### 3. Language Detection (ct-base bilingual policy)
- Default follows OS locale (English unless `zh-*`); one-sentence switch supported via `scripts/switch_lang.py <lang> [--permanent]` (session or permanent in `config.json` `language`).
- `scripts/i18n.py`: 147 keys, all EN+ZH paired (single source of truth).
- Code output always English.

### 4. Security Red Line (highest priority)
- Methodology knowledge (workflows A–J) is retrieved locally from the `knowledge/` pack.
- Answer refinement uses Coze — the one outbound path (forward-only, single call, no retry); `scripts/route.py` labels difficulty at entry; all payloads pass through `sanitize()` first.
- Never expose personal info, subject data, unpublished project data, private paths, or credentials.
- `permissions` block declared in SKILL.md top-level.

### 4.1 Outbound Authorization & config.json Red Line (ct-base §5, 2026-08-19 应用)
- **🔴 绝不自行修改 `config.json`**：agent 不得写入/改写 `config.json`（含 `auto_approve_endpoints` 白名单、`language` 等）。`auto_approve_endpoints` 白名单由**技能作者预置**（`ct-advisor.coze.site/run` 与统一错误报告端点 `https://ct-bugreport.coze.site/run` 已默认在内，故已预置端点实际永不弹确认）；若用户希望某端点跨会话免确认，须由**用户显式**将端点加入 `auto_approve_endpoints`（agent 可引导、可展示 JSON 片段，**不代写**）。
- **首次出站确认**：非白名单端点出站前，`refine_answer.py` 经 `_check_outbound_authorization` 在 stderr 打 `[AUTH-BLOCK]`，agent 向用户展示**全库统一确认文案**（目标服务器 / 发送内容 / 本地资料有限说明），确认后**告知用户**可将端点加入白名单（用户自己操作）。
- **授权不阻断流程**：未授权时脚本返回空串/本地草稿，agent 采用本地胜出方案，仅提示"本次未使用云端分析"，不中断。
- **出站披露**：README 已明确"数据将发送至 `ct-advisor.coze.site/run`"；文档不得出现 "zero-outbound"/"完全离线"/"fully offline" 绝对化表述（已用 "no outbound" 精确限定局部环节）。
- **错误报告出站（§20.3，可选）**：`adapters/bug_report.py` 为脱敏报告客户端，仅在检测到技能缺陷或用户显式请求时，经三阶段确认后向 `https://ct-bugreport.coze.site/run` 发送 11 键脱敏报告（不含原始输入）；公开凭证内嵌混淆（XOR+base64）于该文件，与 Coze 端点同属 `auto_approve_endpoints` 预置白名单。
- **会话授权语义**：`_SESSION_AUTHORIZED_ENDPOINTS` 为模块级内存集合，随每次脚本调用重置——同一运行内多次出站只确认一次，新一次调用重新确认（除非命中白名单）。
- **确认提示信息禁令**：确认文案禁止出现 step / 流程 / 触发机制 / 内部术语。

### 5. Reuse from base
- ct-advisor ships its own `scripts/i18n.py` (advisor-specific user prompts); reuses **vendored copies** of `i18n.py` / `excel_style.py` (from ct-base) for generic & Excel strings where applicable.
- **IMPORTANT (2026-08-11): ct-base is NEVER published.** All shared assets must be vendored into this skill directory. Runtime imports resolve from this skill's own `scripts/` only — never fall back to a ct-base sibling.
- Bilingual single source of truth: the embedded dict in `scripts/i18n.py` (no separate json file; `knowledge/prompts.md` is the agent-facing mirror of the key table and MUST stay in sync).

### 6. Interaction / Menu Design
- ct-advisor implements the code-based difficulty gate fully: `scripts/route.py` (deterministic, LLM-free) labels difficulty **once at entry**. `simple`/`middle`/`complex` → forward to Coze via `scripts/orchestrate.py` (data-intel preferred) or `refine_answer.py --ship` (fallback) with `query_meta.difficulty` set. `vague` → Local Clarify Loop (`scripts/clarify_loop.py`, bounded 1–3 questions/round, hard cap 3 rounds) to clarify intent, then re-gate and route (data-intel → `orchestrate.py`, else `--ship`) with `difficulty="vague"`. No local answer generation; Coze is the answer path (code decides, the LLM only delegates ct-skill calls + fallback).
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
