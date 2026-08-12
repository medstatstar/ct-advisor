# Clinical Trial Chief Advisor (ct-advisor)

[🇨🇳 中文](./README_zh-CN.md) | [🇺🇸 English (Current)](#)

<div align="center">
<img src="assets/icon.svg" width="240" height="240" alt="ct-advisor logo"/>
</div>

> **The single front door for the whole `ct-*` clinical-trial skill family — a methodology & regulatory-evidence advisor that also routes real-data / competitive-intel asks to sibling data skills.**

> 💡 **Performance Tip**: By design, **simple** questions are answered locally with no outbound call — no need to wait for Coze. **Middle** and **complex** questions are mainly refined by the Coze endpoint (usually returns in **~20s**), so the skill's dependence on the local model's performance is low. That said, reasoning models (e.g. Hunyuan-3, DeepSeek-R1) have been observed to spend a lot of time on meaningless deep thinking when running this skill locally. **If a single reply routinely takes longer than 3 minutes, we recommend switching to a simple standard / flash model to speed things up.**

> No commands or manual needed. Just describe your trial question **in plain language inside a chat** — the advisor answers methodology / design / statistics / GCP / safety / regulatory / QC / tone questions in-house, and for real-data or competitive-intel needs, routes you to the right sibling skill (`ct-registry` / `ct-safety` / `ct-literature` / `ct-samplesize`) or stitches a full competitive-intel brief from the three data sources. It **re-implements no** retrieval or computation logic. B-tier. **Note: middle/complex answers are refined via the Coze endpoint (see the privacy notice below); simple questions are answered locally with no outbound call.**

> ⚠️ **Data outbound & privacy notice — read before installing.** For **middle / complex** questions, your input is sent over the network to the author-hosted endpoint **`https://ct-advisor.coze.site/run`** for answer refinement — this is the one outbound path. Before sending, `sanitize()` automatically strips PII (ID numbers, phone numbers, emails, and a small set of sensitive keywords), and a non-reversible sha256 machine id is attached as `query_origin` (no plaintext). **Auto-redaction is not bulletproof — do NOT enter other sensitive or confidential information**: real patient names, unpublished trial data, trade secrets, passwords, API keys, or any other personally identifiable / restricted content. The shipped `config/coze.dat` is the **required public credential** for that endpoint (published by the author) — keep it as-is; do not replace it with your own token. See §5 for details.

---

## Who This Is For

The `ct-*` clinical-trial skill family is built to address needs across the entire clinical-trial lifecycle, mainly for three groups:

- **Clinical-trial practitioners at pharmaceutical companies** — sponsors, CROs, and medical / statistical / regulatory roles;
- **Clinicians and nurses who design, manage clinical-trial projects, or take part in hands-on trial conduct in medical institutions**;
- **Medical students who want to learn clinical-trial methodology in a structured way**.

## 1. How to Use It in a Chat (the Core)

ct-advisor is a **conversational skill**: you simply tell the assistant what you're working on — no commands, no parameter names to remember. Once installed as a WorkBuddy skill, you invoke it in a chat via the Skill tool; there is no extra setup, but it activates only when you call it — not automatically in the background.

Below are 6 real conversational examples ordered from simple to advanced. Each shows **"You say"** and a sketch of **"The assistant replies"**, plus how to get the actual data / computation.

### Example 1 · A simple methodology question (direct answer, no menu) 
**You say:** 
Superiority design, two parallel groups — how should I set the primary estimand?

**Assistant replies (sketch):** 
Per the ICH E9(R1) estimand framework, a two-arm superiority trial defines: ① **treatment effect** (difference in the chosen endpoint), ② **population** (default "unless an intercurrent event is clinically critical, use the 'while on treatment' strategy"), ③ **variable** (e.g. change from baseline), ④ **summary** (difference + 95% CI). Give me the endpoint and I can draft the full estimand statement.

**📌 No data needed** — this is answered in-house from the knowledge pack; you get the answer directly, no menu.

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
This is a broad ask, so I'll call **ct-registry + ct-safety + ct-literature** once each and **stitch the Strategic Brief in-house** (no separate orchestrator). Plan: (1) registry landscape, (2) FAERS safety signals, (3) published evidence — then a merged brief with a "Data source: ct-xxx on <date>" label on every claim.

**📌 Get the real brief:** By default the advisor **calls ct-registry + ct-safety + ct-literature once each and stitches the Strategic Brief in-house** (data_intel dispatched directly, no extra confirmation needed). (This replaces the old one-stop `ct-pipeline` route — the advisor now does the stitching itself.)

### Example 4 · A multi-decision design task (popup routing menu) 
**You say:** 
I'm planning a Phase II oncology trial and also need the sample size — help me decide the design.

**Assistant replies (sketch):** 
Two things are clear (oncology, Phase II), but a few choices remain — here's a menu so I don't decide for you:

> **① What kind of help?**
> - (a) Methodology & regulatory advice (design / stats / compliance / QC)
> - (b) Real data & competitive intel
> - (c) Clarify my needs first

> **② Within methodology — which area?**
> - (a) Design & statistics (workflows B / C)
> - (b) Safety & operations (E / F)
> - (c) Documents & QC (G / H)
> - (d) Explain / other (A / D / I / J)

> **③ Can't decide?** → Say "explain the differences", and I'll walk through the clinical/statistical meaning of each option before you choose.

> Pick ①–② and I'll drill into the workflow, then hand sample-size off to `ct-samplesize`.

**📌 Note:** When your request has **multiple decisions / depends on several parameters**, the advisor **pops a step-by-step routing menu** (each step confirmed before advancing) and always offers the "explain the differences" entry — it never dumps the full menu or decides for you.

### Example 5 · Not sure what you need (vague → grill-me) 
**You say:** 
I'm not sure what I actually need — I have a half-written protocol and some questions.

**Assistant replies (sketch):** 
No problem — let's pin it down branch by branch; a few key questions will locate the right help:
> 1. What's your **role** — sponsor / CRO / investigator / regulatory?
> 2. What **stage** is the program at — pre-IND, Phase I–IV, post-market?
> 3. What **material** do you have — the protocol, SAP, CSR, or just a question?

> (After you answer, I keep probing until the need is clear, then route — no full menu dumped on you in the meantime.)

**📌 Note:** When you say "not sure what I want", the advisor uses **branch-by-branch probing (grill-me)** instead of guessing or dumping a menu. Once clarified, it routes to the right workflow or data skill.

### Example 6 · Switch the output language
**You say:** 
switch to English.  /  > Always reply in English.

**Assistant replies (sketch):** 
Sure, I'll answer in English from now on. (Output language auto-follows your OS by default — Chinese OS → Chinese, otherwise English — but you can switch with one sentence.)

**📌 Note:** Language is one-sentence switchable:
- **This conversation only** — say "switch to English" / "用中文回复" → advisor runs `python scripts/switch_lang.py en` (or `zh-CN`).
- **Permanently (all future sessions)** — say "always reply in English" / "永久用中文" → advisor runs `python scripts/switch_lang.py en --permanent`, writing `config.json` `language`. Re-run with the other language to reset.

---

## 2. What Can It Do — Scenarios

The advisor covers the entire clinical-trial lifecycle through ten in-house workflows (A–J) plus routing to five sibling skills. Each row gives the typical **situation** and a line you can **copy verbatim** under "Try saying".

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

### ④ Clarify mode (grill-me, no sibling skill, no network)
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

**Q: Does pure methodology need the network?** A: It depends on difficulty. **Simple** methodology questions (a definition, a single standard operation, a fact) are answered **entirely locally** from the `knowledge/` pack — **no network call at all**, no Coze. **Middle / complex** questions additionally send the answer to the Coze endpoint (`https://ct-advisor.coze.site/run`) for refinement — this is the only outbound path for those answers.

---

## 4. Security & Privacy

### Safe Preview (sibling skills dispatched by default)
- **Dispatched by default:** For `data_intel` asks (competitive landscape / safety signals / literature / sample size), the advisor **dispatches directly to the relevant sibling skill** (ct-registry / ct-safety / ct-literature / ct-samplesize) by default to complete the analysis and return live results — no need to say "please fetch the data now". If you only want the plan and not the data yet, say "just show the plan".
- **Traceable, not fabricated:** Every factual / normative claim carries a source citation or an `⚠️ needs official verification` marker; it never fills factual gaps with fluent prose.
- Outputs are for reference only; validate against official sources before regulatory submissions.

### Outbound & Privacy (answer refinement via Coze for middle/complex)
- **The outbound path = answer refinement (Coze), for middle/complex:** Simple questions are answered locally with no outbound call. For middle/complex questions, because clinical trials demand high answer quality, the advisor sends your question to **`https://ct-advisor.coze.site/run`** for refinement against the full database (step 2 / step 6 invokes `scripts/refine_answer.py`, POSTing `query_meta` (incl. `query_origin` machine id) + `original_question` + `draft_answer`; outbound payloads pass through `sanitize()` first). The shipped `config/coze.dat` is the **required public credential** for that endpoint (published by the author) — keep it as-is and do not replace it with your own token. On Coze timeout/error it degrades to the local draft, but **only as a fault fallback**. **Do not paste confidential trial / patient / sponsor data** into any prompt.
- **Machine id is hashed, non-PII:** `query_origin` (nested inside `query_meta`) is `sha256(hostname)` — a stable per-machine identifier used only for per-machine audit/attribution and Coze-side rate limiting. It contains **no plaintext hostname, IP, or any other PII**.
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
| Coze mode (opt-in · advisor backend only) | Optionally enable `backend: coze` + `coze.bot_id` to route Q&A through a Coze bot; **answer refinement for middle/complex needs `requests`** (auto-installed if missing). Simple questions never call Coze. |

### Architecture
```
ct-advisor/
├── SKILL.md              # orchestration layer: clarify → route → assemble → answer
├── knowledge/            # portable methodology pack (the "brain")
├── scripts/              # stdlib-only CLI helpers + machine-readable specs
│   ├── menu.json         # clarification-menu tree
│   ├── workflows.json    # A–J routing & integration contract
│   ├── i18n.py           # bilingual single source of truth
│   ├── menu.py           # menu builder (Coze twin / local preview)
│   ├── check_deps.py     # local-only capability probe
│   └── search_refs.py    # topic-reference locator
├── adapters/             # reasoning-exit / data-grounding / Q&A seams (swappable)
└── config.json           # runtime backend selector (methodology knowledge retrieved locally from `knowledge/`; simple questions answered locally with no outbound call; middle/complex answer refinement calls Coze remotely)
```

### CLI examples (developers)
```bash
python3 scripts/check_deps.py     # local capability probe (no install, no network)
python3 scripts/menu.py --all     # dump the clarification menu as JSON
python3 scripts/menu.py --tier data_skill --human --lang zh   # preview one tier
```

### Security scanner false positives 
Some automated scanners flag `adapters/` because it contains strings that look network- or credential-related. Distinguish two paths: (1) the **advisor backend** `CozeBackend.advise()` / `_post()` are inert stubs that raise `NotImplementedError` and are never executed unless you explicitly implement and enable Coze routing in `config.json` — no token read, no HTTP request on that path. (2) **Answer refinement uses Coze for middle/complex questions**: `scripts/refine_answer.py` POSTs the 5 variables to the Coze refiner on every middle/complex answer, so `requests` is imported by the always-active refiner (not just an inactive path). **Simple** questions are answered locally and make **no** outbound call, so running the skill on a simple question is zero-outbound. For middle/complex, running the skill as shipped is **not** zero-outbound — methodology knowledge is retrieved locally from `knowledge/`, but each refined answer is sent to `ct-advisor.coze.site/run` (PII sanitized via `sanitize()`; `query_origin` is a non-PII `sha256` machine id). No secrets are in the repo (the Coze token is read from `config/coze.dat` / env var, only when refinement runs).

---

**Version**: v0.9.51 | **License**: MIT | **Authors**: medstatstar, phoe-zip

For feature requests, bug reports, or other feedback, please contact the author directly at medstatstar@gmail.com (Wintone Zhang).

---

## Confidentiality Notice

> The CT series consists of 16+ specialized domain skills, organized into four tiers — A, B, C, D — by "confidential-data-exfiltration risk + whether external retrieval is needed", providing full coverage of the entire new-drug clinical trial (Clinical Trial) lifecycle.

> - **Tier A / B (non-confidential)**: run fully locally using only ordinary data; Tier B may need external public retrieval but involves no confidential information. These skills are published openly on GitHub.
> - **Tier C / D (confidential)**: involve strictly confidential clinical-trial data and internal information from pharma sponsors (e.g., ct-analysis, ct-sdtm); Tier C is processed locally and never leaves the boundary, while Tier D additionally requires policy approval. These skills are designated for internal enterprise use only and are not publicly released at present.

> If you do have a genuine need for these confidential skills, please contact the author to request custom installation.

> 📧 Contact: medstatstar@gmail.com (Wintone Zhang)
