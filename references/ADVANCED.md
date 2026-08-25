# ct-advisor — Advanced Reference (developer / maintainer)

> This file holds operational detail that the agent-facing `SKILL.md` only points to, per ct-base §4 ("technical detail descends to `references/ADVANCED.md`, SKILL.md keeps behavior rules + pointers only"). Step-by-step I/O and exception handling for steps 0–6 live in `references/steps.md`. This file covers latency observability, the bug-report protocol, attachment handling, and Coze-failure diagnosis.

## Latency observability (F, 2026-08-23)

`scripts/refine_answer.py` flags (all local, counter in `<ROOT>/.runtime/`, gitignored; no network call):

- `--latency-report --round-id <qid>` — tallies tool round-trips per question; counter file `latency_<round_id>.json`.
- `--latency-threshold <n>` (default 10) — emits `[WARN]` when a single round's round-trips exceed it; the pre-fire delay regression signal.
- `--latency-reset --round-id <qid>` — resets the counter for a round.

The invariant checklist (L1–L6) lives in `references/steps.md` "延迟护栏单测式检查表（F）":
- L1 `middle` MUST be fire-only, never pre-fire read `knowledge/`.
- L2 `simple` MUST skip Coze only when local-sufficient; otherwise fire.
- L3 fire MUST NOT happen after a local read in the same turn.
- L4 `complex` local pre-amble ≤ 200 chars single shot.
- L5 forward-only (no re-merge in the agent).
- L6 `vague` MUST NOT be sent directly; clarified first.

Use `--latency-report` whenever you change Step 0/1 to catch `middle` pre-fire reads or `simple` Coze calls creeping back.

## Bug-report protocol (§20.3 · ct-base)

`adapters/bug_report.py` — sanitized 11-key outbound (no raw input; only user-approved `description`).

- **Trigger:** detected defect (CLI≠0 / R engine error / user questions result) or explicit user request ("report a bug" / "反馈问题" / "提交错误报告").
- **Two-stage confirmation (mandatory):** (1) propose-with-preview — `render_report_text` shown together with the propose message; (2) one explicit user consent sends. Capped at 1 unsolicited offer/session; user-initiated unlimited.
- **Keys:** `skill` / `skill_version` / `test` / `error_type` / `error_code` / `engine_status` / `description` / `locale` / `query_origin` / `session_hash` / `attempts`. No raw input values or PII except `description` (user-authored).
- **Endpoint:** `https://ct-bugreport.coze.site/run`. Public credential embedded (obfuscated) in `adapters/bug_report.py`.
- **Invoke:** `python adapters/bug_report.py --error-type <t> --test <name> --description "<free text>" [--send]` (add `--send` ONLY after user confirms).
- **Receipt:** endpoint returns `history` (last submission for same `query_origin`, or `""`); reply = `confirm_thanks(locale)` + `build_followup(history, locale)`. `history` empty → end; `history.resultstr == "done"` → show fix note from `history.memo`; else "not yet fixed". All strings bilingual via `_MSGS` + `_current_locale()`.

## Attachment handling (docx / pdf / ppt) — detail

Governance (layered conversion, user prompts, confidentiality boundary) is consolidated into **ct-base §6.7** (`ct-base/docs/02-governance-redlines.md`); on conflict ct-base §6.7 wins. Implementation specifics for ct-advisor:

1. Convert the attachment to Markdown via `scripts/office_to_md.py` (same source as the base shared artifact `ct-base/scripts/office_to_md.py`, shipped with the package).
2. Append the converted text to `original_question` and run the normal pipeline (`route.py` → `refine_answer --ship`), wrapped as:
   `...要求：撰写完整规范。以下是模板内容：\n---\n{md}\n---`
3. Coze `full_analysis` "template induction" mode recognizes this format → generates the full spec body; gaps explicitly marked, never padded.
4. Local converter path: `scripts/office_to_md.py`. Confidentiality: only the converted text (no raw attachment metadata) crosses the boundary; Coze payloads are sanitized.

## Coze-failure diagnosis (user-friendly)

On fallback (stderr `FALLBACK` / `ProxyError` / `Timeout`, or stdout ask "…是否允许我自动进行问题诊断排查？"):

1. **Ask first:** "Coze 云端服务暂时不可用，是否允许我自动诊断排查？"
2. If allowed → `python scripts/check_coze.py` once; fix root cause (stale system proxy / offline / token); retry.
3. If declined → deliver the local `knowledge/` answer **with a prominent warning**: 「无法连接 Coze 服务，答案未经过精校，请谨慎使用」.
4. v0.9.60+ auto-retries bypassing the system proxy on `ProxyError`/`ConnectionError`.

## Call-style summary (zero temp files)

- Prefer stdin pipe: `echo '{…}' | python refine_answer.py --ship` (Chinese punctuation safe).
- **Forbidden:** Write/Bash temp JSON files, `/tmp` paths.
- PowerShell: here-string `@'…'@`.
- Full encoding caveats → `references/steps.md` "Call-style summary".

---

## Runtime & requirements (from README · Advanced Reference)

| Item | Requirement |
|---|---|
| Runtime | The agent reads `knowledge/` directly — **no mandatory dependency**. |
| Optional CLI helpers | `python3` (stdlib only). `scripts/*.py` load `scripts/*.json` via `json` — **no PyYAML**. |
| Sibling skills | `ct-registry`, `ct-safety`, `ct-literature`, `ct-samplesize` (only for data routing / grounding; the competitive-intel brief is stitched in-house from the three; missing ones degrade gracefully). They install from GitHub — `ct-registry`→`https://github.com/medstatstar/ct-registry`, `ct-safety`→`https://github.com/medstatstar/ct-safety`, `ct-literature`→`https://github.com/medstatstar/ct-literature`, `ct-samplesize`→`https://github.com/medstatstar/ct-samplesize` (clone into `~/.workbuddy/skills/<slug>`). When one is missing, the advisor prints its GitHub address directly. |
| Cloud analysis (Coze) | Every **non-vague** question is sent to the Coze endpoint once for analysis (vague ones clarified locally first, then forwarded) — needs `requests` (auto-installed if missing). Local `knowledge/` is the fault fallback only. |

## Architecture

```
ct-advisor/
├── SKILL.md              # agent-facing spec: difficulty gate → [vague: clarify-loop → re-route] / [non-vague: local orchestrator]
├── knowledge/            # portable methodology pack (the "brain")
├── scripts/              # stdlib-only, LLM-free CLI helpers (the code orchestration layer)
│   ├── route.py          # difficulty gate (vague / simple / middle / complex)
│   ├── route_tool.py     # high-confidence sibling-skill prefetch predictor (Mode B)
│   ├── orchestrate.py    # code orchestrator: parallel Coze + prefetch, merge, stitch; emits delegate block or wrapped answer
│   ├── refine_answer.py  # --ship / --card-inline: call Coze, run need_tool in code, wrap answer
│   ├── handle_need_tool.py # execute a need_tool card (run sibling skill, infer params)
│   ├── clarify_loop.py   # bounded Local Clarify Loop (heuristic, hard cap 3 rounds)
│   ├── menu.json         # clarification-menu tree
│   ├── workflows.json    # A–J routing & integration contract
│   ├── i18n.py           # bilingual single source of truth
│   ├── menu.py           # menu builder (Coze twin / local preview)
│   ├── check_deps.py     # local-only capability probe
│   └── search_refs.py    # topic-reference locator
├── adapters/             # reasoning-exit / data-grounding / Q&A seams (swappable)
└── config.json           # runtime backend selector (non-vague → orchestrate.py → Coze + local skill; vague clarified locally then re-routed; sibling skills executed locally via need_tool; local knowledge/ fallback on Coze failure)
```

## CLI examples (developers)

```bash
python3 scripts/check_deps.py     # local capability probe (no install, no network)
python3 scripts/menu.py --all     # dump the clarification menu as JSON
python3 scripts/menu.py --tier data_skill --human --lang zh   # preview one tier
```

## Security scanner false positives

Some automated scanners flag `adapters/` because it contains strings that look network- or credential-related. Distinguish two paths: (1) the **advisor backend** `CozeBackend.advise()` / `_post()` are inert stubs that raise `NotImplementedError` and are never executed unless you explicitly implement and enable Coze routing in `config.json` — no token read, no HTTP request on that path. (2) **Answer analysis uses Coze for every non-vague question** (vague ones are clarified locally via the Local Clarify Loop first, then forwarded): `scripts/refine_answer.py --ship` (data-intel questions use `scripts/orchestrate.py`) POSTs the payload to the Coze refiner on every answer, so `requests` is imported by the always-active refiner (not just an inactive path). Running the skill **is** outbound for every non-vague question — the question text is sent to `ct-advisor.coze.site/run` (PII sanitized via `sanitize()`; `query_origin` is a non-PII `sha256` machine id). The public credential is embedded (obfuscated, XOR+base64) in `adapters/coze_token_embedded.py` — **no plaintext secrets** in the repo.
