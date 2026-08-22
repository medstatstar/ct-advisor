# Clinical Trial Chief Advisor (ct-advisor)

[🇨🇳 中文](./README_zh-CN.md) | [🇺🇸 English (Current)](#)

<div align="center">
<img src="assets/icon.svg" width="240" height="240" alt="ct-advisor logo"/>
</div>

> **The single front door for the whole `ct-*` clinical-trial skill family — a methodology & regulatory-evidence advisor. Every **non-vague** question is first passed through a deterministic, LLM-free local orchestrator (`scripts/orchestrate.py`): it may prefetch the needed sibling data skill (ct-registry / ct-safety / ct-literature / ct-samplesize) **in parallel** with the Coze cloud workflow, then merge and stitch the result **in code** — the agent only relays the final answer verbatim. A `vague` question is first clarified locally via the Local Clarify Loop (`scripts/clarify_loop.py`), then re-routed. When Coze (or the prefetch) needs a sibling data skill, the call runs **locally** and the result is stitched in by code; local `knowledge/` serves only as the Coze-failure fallback.**

> 💡 **Performance Tip**: Every **non-vague** question is handled by the local orchestrator (`scripts/orchestrate.py`), which forwards to the Coze endpoint in a **single call** (usually returns in **~20s**; data-intel questions also run the needed sibling skill locally in parallel). A `vague` question is clarified locally first (a few seconds via the Local Clarify Loop), then re-routed. Because the orchestrator, prefetch, merge, and stitching are all **code** (not the LLM), the skill's dependence on the local model's performance is low. That said, reasoning models (e.g. Hunyuan-3, DeepSeek-R1) have been observed to spend a lot of time on meaningless deep thinking when running this skill locally. **If a single reply routinely takes longer than 3 minutes, we recommend switching to a simple standard / flash model to speed things up.**

> No commands or manual needed. Just describe your trial question **in plain language inside a chat** — the advisor passes it to the local orchestrator, which forwards to the Coze cloud workflow for methodology / design / statistics / GCP / safety / regulatory / QC / tone answers, and for real-data or competitive-intel needs runs the right sibling skill (`ct-registry` / `ct-safety` / `ct-literature` / `ct-samplesize`) **locally** and stitches the result in **code**. It **re-implements no** retrieval or computation logic. A-tier. **Note:** every non-vague question is sent via the local orchestrator to the Coze endpoint for analysis (a `vague` question is clarified locally via the Local Clarify Loop first, then re-routed; see the privacy notice below); local `knowledge/` is only the fault fallback when Coze is unavailable.

> ⚠️ **Data outbound & privacy notice — read before installing.** Your question is sent over the network to the author-hosted endpoint **`https://ct-advisor.coze.site/run`** for analysis — this is the one outbound path (**every** question — `vague` ones are clarified locally first, then forwarded; all others forwarded directly, no difficulty split in the outbound path). Before sending, `sanitize()` automatically strips PII (ID numbers, phone numbers, emails, and a small set of sensitive keywords), and a non-reversible sha256 machine id is attached as `query_origin` (no plaintext; **stable per-device — identical on every request from the same machine**, used for audit / attribution / rate-limiting). Your OS display language is also attached as `locale` (e.g. `zh-CN` / `en-US`) for answer-language matching — a system locale string, no PII. **Auto-redaction is not bulletproof — do NOT enter other sensitive or confidential information**: real patient names, unpublished trial data, trade secrets, passwords, API keys, or any other personally identifiable / restricted content. The public credential for that endpoint is embedded (obfuscated, XOR+base64) in `adapters/coze_token_embedded.py` (published by the author) — keep it as-is; do not replace it with your own token. See §5 for details.

---

## Who This Is For

The `ct-*` clinical-trial skill family is built to address needs across the entire clinical-trial lifecycle, mainly for three groups:

- **Clinical-trial practitioners at pharmaceutical companies** — sponsors, CROs, and medical / statistical / regulatory roles;
- **Clinicians and nurses who design, manage clinical-trial projects, or take part in hands-on trial conduct in medical institutions**;
- **Medical students who want to learn clinical-trial methodology in a structured way**.

## 1. How to Use It in a Chat (the Core)

ct-advisor is a **conversational skill**: you simply tell the assistant what you're working on — no commands, no parameter names to remember. Once installed as a WorkBuddy skill, you invoke it in a chat via the Skill tool; there is no extra setup, but it activates only when you call it — not automatically in the background.

Below are 6 real conversational examples ordered from simple to advanced. Each shows **"You say"** and a sketch of **"The assistant replies"**, plus how to get the actual data / computation.

### Example 1 · A simple methodology question (forwarded, no menu) 
**You say:** 
Superiority design, two parallel groups — how should I set the primary estimand?

**Assistant replies (sketch):** 
Per the ICH E9(R1) estimand framework, a two-arm superiority trial defines: ① **treatment effect** (difference in the chosen endpoint), ② **population** (default "unless an intercurrent event is clinically critical, use the 'while on treatment' strategy"), ③ **variable** (e.g. change from baseline), ④ **summary** (difference + 95% CI). Give me the endpoint and I can draft the full estimand statement.

**📌 No data needed** — this is forwarded to Coze in a single call; you get the answer directly, no menu.

### Example 2 · A narrow data ask (one data skill) 
**You say:** 
Pull the registered trials for semaglutide in type-2 diabetes, 2021–2026.

**Assistant replies (sketch):** 
Routing you to **ct-registry** (CT.gov + WHO ICTRP + CDE + EU-CTR + ChiCTR + ISRCTN + DRKS). Here is the normalized landscape — N trials, phase mix, region mix, top sponsors — with each row labeled "Data source: ct-registry on <date>".

**📌 Get the real data:** By default the advisor dispatches to **ct-registry** and the sibling skills, returning the live landscape directly (data_intel dispatched directly, no extra confirmation needed); every row labeled "Data source: ct-registry on <date>".

### Example 3 · A broad competitive-intel ask (three sources stitched in-house ⭐) 
**You say:** 
Give me the full competitive-intel picture for GLP-1 RA in obesity — trials, safety signals, and literature.

**Assistant replies (sketch):** 
This is a broad ask, so the **local code orchestrator** (`orchestrate.py`) will dispatch **ct-registry + ct-safety + ct-literature** as needed and **stitch the Strategic Brief in code** — I just relay the result (no separate manual step). Plan: (1) registry landscape, (2) FAERS safety signals, (3) published evidence — then a merged brief with a "Data source: ct-xxx on <date>" label on every claim.

**📌 Get the real brief:** By default the advisor's **local code orchestrator dispatches ct-registry + ct-safety + ct-literature as needed and stitches the Strategic Brief in code** (data_intel dispatched directly, no extra confirmation needed; the agent only relays). (This replaces the old one-stop `ct-pipeline` route — the local orchestrator now does the dispatch + stitching automatically.)

### Example 4 · A multi-part design task (forwarded, Coze decomposes) 
**You say:** 
I'm planning a Phase II oncology trial and also need the sample size — help me decide the design.

**Assistant replies (sketch):** 
This is a multi-part ask, so the local orchestrator (`orchestrate.py`) runs the needed data skill (e.g. **ct-samplesize**) **in parallel with** the Coze cloud workflow (single Coze call). Coze returns a structured plan — it lays out the key Phase II oncology design decisions (endpoint, control arm, randomization, sample-size basis) and, since you also need the sample size, the computed n is stitched in by code. I'll show you the plan and the result, then we can drill into any piece.

**📌 Note:** Multi-part and data-intel requests are handled by the **local code orchestrator** — there is no local popup routing menu anymore. The orchestrator forwards to Coze and runs any needed sibling skill locally, then stitches in code; the agent just relays.

### Example 5 · Not sure what you need (vague → Local Clarify Loop) 
**You say:** 
I'm not sure what I actually need — I have a half-written protocol and some questions.

**Assistant replies (sketch):** 
No problem — `route.py` tagged this `vague`, so I'll run the Local Clarify Loop (`scripts/clarify_loop.py`) to pin down what you need. A few bounded questions (up to 3 rounds) will locate the right help:
> 1. Who is the **target population** (disease, stage, line of therapy, age)?
> 2. What **comparator** do you want to compare against (SoC, placebo, another drug)?
> 3. Which **endpoint / outcome** matters (OS, PFS, ORR, AE rate)?

> (After you answer, I clarify until the need is clear, then re-run the difficulty gate on the enriched question; for data-intel it goes through the local orchestrator, otherwise it forwards to Coze — no full menu dumped on you in the meantime.)

**📌 Note:** When you say "not sure what I want" (e.g. "I'm not sure what I actually need", "我不知道该从哪里开始"), the advisor runs the **Local Clarify Loop** (`scripts/clarify_loop.py`, bounded 1–3 questions/round, hard cap 3 rounds) instead of guessing. The loop asks the PICO dimensions that actually change the answer — target **population / comparator / outcome** — and accumulates a `question_profile`. Once clarified, it re-runs the difficulty gate on the enriched question and routes to the local orchestrator (data-intel) or Coze with `difficulty="vague"`.

### Example 6 · Switch the output language
**You say:** 
switch to English.  /  > Always reply in English.

**Assistant replies (sketch):** 
Sure, I'll answer in English from now on. (Output language auto-follows your OS by default — Chinese OS → Chinese, otherwise English — but you can switch with one sentence.)

**📌 Note:** Language is one-sentence switchable:
- **This conversation only** — say "switch to English" / "用中文回复".
- **Permanently (all future sessions)** — say "always reply in English" / "永久用中文" (the choice is remembered).

---

### Example 7 · A published-safety evidence check (ct-literature --safety)
**You say:** 
One of our PD-1 products has case reports of interstitial lung disease; QA suspects a new safety signal. Search the **published literature** (case reports, pharmacovigilance studies, reviews) for how much support this signal has, and give me a citable evidence summary for the signal-evaluation meeting.

**Assistant replies (sketch):** 
This needs *published* evidence, so I'll route to **ct-literature --safety** (OpenAlex + Europe PMC/MeSH, 2021–2026, CSM bias focused on case reports / PV studies / reviews) and hand you a de-duplicated, citation-verified evidence base — layered by evidence strength (systematic reviews / cohort / case series / case reports), each entry with a verifiable DOI/PMID.

**📌 Note:** **ct-safety** gives structured FAERS numbers (PRR/ROR/IC); **ct-literature** surfaces **qualitative published evidence** — they complement each other: a signal is strongest when the spontaneous-report statistics *and* the published case literature point the same way. Citation verification + a provenance log make every reference clickable (anti-hallucination).

### Example 8 · Protocol background evidence + sample-size handoff (ct-literature + ct-samplesize)
**You say:** 
We're drafting a phase-3 protocol in this indication. Give me the published RCT + systematic-review evidence from the last 5 years for the introduction, then compute the sample size for a superiority design using the key assumptions I'll provide.

**Assistant replies (sketch):** 
Two handoffs: (1) **ct-literature** for the evidence base (RCTs + systematic reviews, 2021–2026, de-duplicated, citation-linked) for the introduction; (2) **ct-samplesize** for the n computation once you confirm assumptions (α, power, effect size, dropout). The advisor carries the evidence-derived parameter framework (e.g. expected event rates) straight into the computation.

**📌 Note:** Cross-skill collaboration — literature evidence (A-tier retrieval) feeds the protocol background, and the same evidence-based assumptions flow into the sample-size calculation (A-tier compute). Every claim is labeled with its data source and date.

---

## 2. What Can It Do — Scenarios

The advisor covers the entire clinical-trial lifecycle through ten in-house workflows (A–J) plus routing to four sibling skills. Each row gives the typical **situation** and a line you can **copy verbatim** under "Try saying".

### ① Methodology & regulatory advice (answered in-house, A–J)
| Situation | Try saying in chat |
|:---|:---|
| Define a term / find the regulatory basis | "What does ICH E6(R3) say about risk-proportionate monitoring?" |
| Trial design review | "Review my Phase III oncology design for feasibility" |
| Statistics / estimand / sample size framework | "Help me set the primary estimand for a superiority trial" |
| GCP / deviation / audit readiness | "What makes a site audit-ready under GCP?" |
| Safety & operations (SUSAR / DSUR / signal) | "How do I handle a SUSAR in a multinational trial?" |
| Documents & QC (CSR / protocol / SAP) | "Redline my CSR discussion section" |
| Reply tone / rewrite | "Rewrite this patient letter in a warmer tone" |

### ② Real data & competitive intel (routed to sibling skills)
| Situation | Try saying in chat |
|:---|:---|
| Trial-registry landscape | "Pull registered trials for semaglutide in T2D, 2021–2026" |
| Safety signals (FAERS) | "Any FAERS disproportionality signals for drug X?" |
| Published literature | "Find systematic reviews on GLP-1 RA in obesity" |
| **Full competitive-intel brief (three sources stitched ⭐)** | "Full competitive-intel picture for GLP-1 RA in obesity" |

### ③ Compute handoff (to ct-samplesize)
| Situation | Try saying in chat |
|:---|:---|
| Actual n / power | "Sample size: two means, d=0.5, power 80%, α=0.05 two-sided" |

### ④ Clarify mode (Local Clarify Loop, no sibling skill, no network)
| Situation | Try saying in chat |
|:---|:---|
| Not sure what you need | "I'm not sure what I need — help me figure it out" |

> The underlying sibling skills are described in their own READMEs; ordinary users only need to say what they want in plain language — the advisor routes and stitches.

---

## 3. First-Time FAQ

**Q: I only gave a partial description — will it still help?** A: Yes. For methodology it answers from the knowledge pack with whatever you provide, and flags anything it can't verify as `⚠️ needs official verification`. Data asks are routed to the relevant sibling skill by default; if you want to limit the scope, just say so in your question.

**Q: How are data sources labeled in the answer?** A: Every data-grounded claim carries a "Data source: ct-xxx on <date>" label, so you can trace each number back to the sibling skill that produced it.

**It calls the sibling skills for real data by default.** `data_intel` asks are dispatched to the relevant sibling skill (ct-registry / ct-safety / ct-literature / ct-samplesize) by default to complete the analysis and return live results — no need to say "please fetch the data now". If you only want the plan and not the data yet, say "just show the plan".

**Q: On a Chinese system, is the output in Chinese?** A: Yes. Output language follows your OS setting by default (Chinese on a Chinese-OS, English otherwise), and you can force-switch anytime with one sentence (e.g. "switch to English").

**Q: How is the full competitive-intel brief generated now?** A: The advisor calls **ct-registry + ct-safety + ct-literature** once each and **stitches the Strategic Brief itself** — no separate `ct-pipeline` orchestrator. This keeps the same three-source coverage while removing the extra dependency.

**Q: Does pure methodology need the network?** A: Yes — every **non-vague** question is sent to the Coze endpoint (`https://ct-advisor.coze.site/run`) for analysis in a **single call**; a `vague` question is clarified locally via the Local Clarify Loop first, then forwarded. The local `knowledge/` pack is the **fault fallback only**: if Coze is unreachable you still get an offline answer, marked as not cloud-refined.

---

## 4. Security & Privacy

### Safe Preview (sibling skills dispatched by default)
- **Dispatched by default:** For `data_intel` asks (competitive landscape / safety signals / literature / sample size), the advisor **dispatches directly to the relevant sibling skill** (ct-registry / ct-safety / ct-literature / ct-samplesize) by default to complete the analysis and return live results — no need to say "please fetch the data now". If you only want the plan and not the data yet, say "just show the plan".
- **Traceable, not fabricated:** Every factual / normative claim carries a source citation or an `⚠️ needs official verification` marker; it never fills factual gaps with fluent prose.
- Outputs are for reference only; validate against official sources before regulatory submissions.

### Outbound & Privacy (non-vague → Coze; vague clarified locally first; data skills run locally via need_tool)
- **The outbound path = cloud analysis (Coze), for every non-vague question (vague ones clarified locally first, then forwarded):** because clinical trials demand high answer quality, the advisor forwards your question to **`https://ct-advisor.coze.site/run`** for analysis against the full database (one call; `scripts/refine_answer.py --ship`（数据智能类问题用 `scripts/orchestrate.py`）POSTs `query_meta` (incl. `query_origin` machine id and `locale` OS-language) + `original_question` + `draft_answer` (your local draft is sent so the cloud can refine it); outbound payloads pass through `sanitize()` first). The public credential is embedded (obfuscated, XOR+base64) in `adapters/coze_token_embedded.py` (published by the author) — keep it as-is and do not replace it with your own token. On Coze timeout/error it falls back to the local `knowledge/` answer, but **only as a fault fallback**. **Do not paste confidential trial / patient / sponsor data** into any prompt.
- **Sibling data skills run locally:** when the question needs registry / safety / literature / sample-size data, Coze returns a `need_tool` card; the skill then executes **locally** (its own public-source retrieval / computation) and the result is stitched into the Coze draft — only card parameters and the draft cross the boundary, so confidential data never leaves the machine.
- **Machine id is hashed, non-PII:** `query_origin` (nested inside `query_meta`) is `sha256(hostname)` — a stable per-machine identifier used only for per-machine audit/attribution and Coze-side rate limiting. It contains **no plaintext hostname, IP, or any other PII**.
- **Locale is your OS language, non-PII:** `locale` (nested inside `query_meta`) is your OS display-language string (e.g. `zh-CN`, `en-US`) — used only to match the answer language to your system. It contains **no plaintext hostname, IP, or any other PII**.
- **Bug-report client (optional, sanitized):** when a skill defect is detected or you explicitly ask to report a bug, `adapters/bug_report.py` sends an 11-key sanitized report (no raw input data — only skill name/version/error type plus a user-approved `description`) to the author's public endpoint `https://ct-bugreport.coze.site/run`, always after your two-stage confirmation. The public credential is embedded (obfuscated, XOR+base64) in `adapters/bug_report.py`.
- **Nothing written to disk by default:** `qa_store` defaults to `noop` — no Q&A record is kept. Only `qa_store.mode: local` appends full Q&A to `data/qa_log.jsonl` on your machine (unencrypted, treat as sensitive, add to `.gitignore`).
- **About memory (self-improving agent):** ct-advisor follows the WorkBuddy self-improving system. Recurring patterns (same issue ≥ 3 times across ≥ 2 tasks) are **automatically** promoted to long-term memory: behavior/communication rules → `~/.workbuddy/SOUL.md`; workflow/tool rules → project `AGENTS.md`; cross-project user preferences → `~/.workbuddy/MEMORY.md`; project-level notes → `.workbuddy/memory/MEMORY.md`. These files live on your machine. To review what's stored, say "show me your MEMORY.md"; to delete, say "forget all my preferences" or manually `rm ~/.workbuddy/MEMORY.md` (global) / `rm -rf .workbuddy/memory/` (project-level). The promotion is silent to avoid interrupting your workflow.

---

## 5. Advanced Reference (for developers)

CLI helpers, runtime requirements, the architecture tree, and scanner false-positive notes have moved here so everyday users don't need them. See [`SKILL.md`](SKILL.md) and [`CHANGELOG.md`](CHANGELOG.md) for the agent-facing spec and version history.

### Runtime & requirements
| Item | Requirement |
|---|---|
| Runtime | The agent reads `knowledge/` directly — **no mandatory dependency**. |
| Optional CLI helpers | `python3` (stdlib only). `scripts/*.py` load `scripts/*.json` via `json` — **no PyYAML**. |
| Sibling skills | `ct-registry`, `ct-safety`, `ct-literature`, `ct-samplesize` (only for data routing / grounding; the competitive-intel brief is stitched in-house from the three; missing ones degrade gracefully). They install from GitHub — `ct-registry`→`https://github.com/medstatstar/ct-registry`, `ct-safety`→`https://github.com/medstatstar/ct-safety`, `ct-literature`→`https://github.com/medstatstar/ct-literature`, `ct-samplesize`→`https://github.com/medstatstar/ct-samplesize` (clone into `~/.workbuddy/skills/<slug>`). When one is missing, the advisor prints its GitHub address directly. |
| Cloud analysis (Coze) | Every **non-vague** question is sent to the Coze endpoint once for analysis (vague ones clarified locally first, then forwarded) — needs `requests` (auto-installed if missing). Local `knowledge/` is the fault fallback only. |

### Architecture
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

### CLI examples (developers)
```bash
python3 scripts/check_deps.py     # local capability probe (no install, no network)
python3 scripts/menu.py --all     # dump the clarification menu as JSON
python3 scripts/menu.py --tier data_skill --human --lang zh   # preview one tier
```

### Security scanner false positives 
Some automated scanners flag `adapters/` because it contains strings that look network- or credential-related. Distinguish two paths: (1) the **advisor backend** `CozeBackend.advise()` / `_post()` are inert stubs that raise `NotImplementedError` and are never executed unless you explicitly implement and enable Coze routing in `config.json` — no token read, no HTTP request on that path. (2) **Answer analysis uses Coze for every non-vague question** (vague ones are clarified locally via the Local Clarify Loop first, then forwarded): `scripts/refine_answer.py --ship`（数据智能类问题用 `scripts/orchestrate.py`）POSTs the payload to the Coze refiner on every answer, so `requests` is imported by the always-active refiner (not just an inactive path). Running the skill **is** outbound for every non-vague question — the question text is sent to `ct-advisor.coze.site/run` (PII sanitized via `sanitize()`; `query_origin` is a non-PII `sha256` machine id). The public credential is embedded (obfuscated, XOR+base64) in `adapters/coze_token_embedded.py` — **no plaintext secrets** in the repo.

---

**Version**: v0.9.71 | **License**: MIT | **Authors**: medstatstar, phoe-zip

For feature requests, bug reports, or other feedback, please contact the author directly at medstatstar@gmail.com (Wintone Zhang).

---

## Confidentiality Notice

> The CT series consists of 20+ specialized domain skills, organized into two tiers — A, B — by "confidential-data-exfiltration risk + whether external retrieval is needed", providing full coverage of the entire new-drug clinical trial (Clinical Trial) lifecycle.
>
> - **Tier A (non-confidential · public)**: takes only ordinary (non-confidential) input; runs fully locally (`network=off`) or performs public retrieval (`network=public-retrieval`, e.g. ct-registry / ct-advisor) — never involves confidential information. Tier A skills are published openly on GitHub.
> - **Tier B (confidential · internal)**: involve strictly confidential clinical-trial data and internal information from pharma sponsors (e.g., ct-analysis, ct-sdtm, ct-eligibility); Tier B is processed locally (`egress=none`, data never leaves the machine) or requires approved egress (`egress=approval-req`, e.g. ct-eligibility). These skills are designated for internal enterprise use only and are not publicly released at present.
>
> If you do have a genuine need for these confidential skills, please contact the author to request custom installation.
>
> 📧 Contact: medstatstar@gmail.com (Wintone Zhang / 张文彤)
