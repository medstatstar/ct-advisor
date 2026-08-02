# Clinical Trial Advisor (ct-advisor)

[🇨🇳 Chinese](./README_zh-CN.md) | [🇺🇸 English (Current)](#)

<div align="center">
<img src="assets/icon.svg" width="240" height="240" alt="ct-advisor logo"/>
</div>

> **The single front door for the whole `ct-*` clinical-trial skill family — a methodology & regulatory-evidence advisor that also routes real-data / competitive-intel asks to the sibling ct data skills.**

> You don't need commands or a manual. Just describe your trial question **in plain language inside a chat**; the advisor answers methodology / design / statistics / GCP / safety / regulatory / QC / tone questions in-house, and — for real-data or competitive-intel needs — routes you to the right sibling skill (`ct-registry` / `ct-safety` / `ct-literature` / `ct-samplesize`) or stitches a full competitive-intel brief from the three data sources. It **re-implements no** retrieval or computation logic. B-tier; pure methodology runs fully offline.

---

## Who This Is For

ct-advisor is built for three groups:

- **Clinical-trial practitioners at pharmaceutical companies** — sponsors, CROs, and medical / statistical / regulatory roles;
- **Clinicians and nurses who take part in the hands-on conduct of trials**;
- **Medical students who want to learn clinical-trial methodology in a structured way**.

## 1. How to Use It in a Chat (the Core)

ct-advisor is a **conversational skill**: you simply tell the assistant what you're working on — no commands, no parameter names to remember. As a WorkBuddy skill it **auto-loads with no extra installation**.

Below are 6 real conversational examples ordered from simple to advanced. Each shows **"You say"** and a sketch of **"The assistant replies"**, plus how to get the actual data / computation.

### Example 1 · A simple methodology question (direct answer, no menu) **You say:** > For a superiority trial with two parallel groups, how should I set the primary estimand?

**Assistant replies (sketch):** > Here's the ICH E9(R1) estimand framing for a two-arm superiority trial: define the **treatment effect** (difference in the chosen endpoint), the **population** (use the "while on treatment" strategy unless a intercurrent event is clinically critical), the **variable** (e.g. change from baseline), and the **summary** (difference + 95% CI). I can draft the full estimand statement if you give me the endpoint.

**📌 No data needed** — this is answered in-house from the knowledge pack; you get the answer directly, no menu.

### Example 2 · A narrow data ask (one data skill) **You say:** > Pull the registered trials for semaglutide in type-2 diabetes, 2021–2026.

**Assistant replies (sketch):** > Routing you to **ct-registry** (CT.gov + WHO ICTRP + CDE + EU-CTR + ChiCTR + ISRCTN + DRKS). Here is the normalized landscape — N trials, phase mix, region mix, top sponsors — with each row labeled "Data source: ct-registry on <date>".

**📌 Get the real data:** By default the advisor shows the **search plan** (which sources, which keywords) and asks you to confirm. Say **"please fetch the data now"** and it actually calls the sibling skill and returns the live landscape.

### Example 3 · A broad competitive-intel ask (three sources stitched in-house ⭐) **You say:** > Give me the full competitive-intel picture for GLP-1 RA in obesity — trials, safety signals, and literature.

**Assistant replies (sketch):** > This is a broad ask, so I'll call **ct-registry + ct-safety + ct-literature** once each and **stitch the Strategic Brief in-house** (no separate orchestrator). Plan: (1) registry landscape, (2) FAERS safety signals, (3) published evidence — then a merged brief with a "Data source: ct-xxx on <date>" label on every claim.

**📌 Get the real brief:** Say **"please fetch the data now"** and it runs the three sibling skills and assembles the consolidated brief. (This replaces the old one-stop `ct-pipeline` route — the advisor now does the stitching itself.)

### Example 4 · A multi-decision design task (popup routing menu) **You say:** > I'm planning a Phase II oncology trial and also need the sample size — help me decide the design.

**Assistant replies (sketch):** > Two things are clear (oncology, Phase II), but a few choices remain — here's a menu so I don't decide for you:

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

### Example 5 · Not sure what you need (vague → grill-me) **You say:** > I'm not sure what I actually need — I have a half-written protocol and some questions.

**Assistant replies (sketch):** > No problem — let's pin it down branch by branch; a few key questions will locate the right help:
> 1. What's your **role** — sponsor / CRO / investigator / regulatory?
> 2. What **stage** is the program at — pre-IND, Phase I–IV, post-market?
> 3. What **material** do you have — the protocol, SAP, CSR, or just a question?

> (After you answer, I keep probing until the need is clear, then route — no full menu dumped on you in the meantime.)

**📌 Note:** When you say "not sure what I want", the advisor uses **branch-by-branch probing (grill-me)** instead of guessing or dumping a menu. Once clarified, it routes to the right workflow or data skill.

### Example 6 · Switch the output language **You say:** > Reply in English.

**Assistant replies (sketch):** > Sure, I'll answer in English from now on. (Output language follows your OS by default — Chinese OS → Chinese, otherwise English — and you can force-switch anytime with one sentence.)

**📌 Note:** Output language follows your OS setting by default; force-switch anytime with one sentence.

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

### ④ Clarify mode (grill-me, no sibling skill, no network)
| Situation | Try saying in chat |
|:---|:---|
| Not sure what you need | "I'm not sure what I need — help me figure it out" |

> The underlying sibling skills are described in their own READMEs; ordinary users only need to say what they want in plain language — the advisor routes and stitches.

---

## 3. First-Time FAQ

**Q: I only gave a partial description — will it still help?** A: Yes. For methodology it answers from the knowledge pack with whatever you provide, and flags anything it can't verify as `⚠️ needs official verification`. For data asks it confirms the search scope with you before fetching.

**Q: How are data sources labeled in the answer?** A: Every data-grounded claim carries a "Data source: ct-xxx on <date>" label, so you can trace each number back to the sibling skill that produced it.

**Q: It only shows a plan, not the live data. How do I get the actual results?** A: By default the advisor shows the **routing / search plan** first (which skill, which sources, which keywords) and asks you to confirm. Say **"please fetch the data now"** and it actually calls the sibling skill and returns the live results. This is the safe default — see the plan, then run once you're confident.

**Q: On a Chinese system, is the output in Chinese?** A: Yes. Output language follows your OS setting by default (Chinese on a Chinese-OS, English otherwise), and you can force-switch anytime with one sentence (e.g. "switch to English").

**Q: How is the full competitive-intel brief generated now?** A: The advisor calls **ct-registry + ct-safety + ct-literature** once each and **stitches the Strategic Brief itself** — no separate `ct-pipeline` orchestrator. This keeps the same three-source coverage while removing the extra dependency.

**Q: Does pure methodology need the network?** A: No. Methodology (workflows A–J) runs **fully offline** — no network, no third-party Python packages. Only data/intel routing touches the sibling skills (which may do public retrieval).

---

## 4. Safety & Preview

- **What is Safe Preview:** By default the advisor only **shows the plan** (which workflow / which sibling skill / which sources) and answers methodology from its knowledge pack — it does **not** auto-fire the sibling-data retrieval. Say **"please fetch the data now"** to trigger the real call; say **"just show the plan"** to keep previewing.
- **No secrets, local-first:** The advisor never exposes personal info, subject data, unpublished project data, private paths, or credentials. Methodology runs with zero outbound traffic.
- **Traceable, not fabricated:** Every factual / normative claim carries a source citation or an `⚠️ needs official verification` marker; it never fills factual gaps with fluent prose.
- Outputs are for reference only; validate against official sources before regulatory submissions.

---

## Future Release Plans

ct-advisor currently runs locally and is already usable for methodology, regulatory, and data routing. We are planning further enhancements and welcome your continued attention:

1. **Cross-model validation**: We will soon introduce remote-database-verified cross-model validation, running key methodology conclusions through a dual-model cross-check to further improve accuracy and reliability.
2. **Sibling skills to be released**: Related sibling skills will be released progressively as they are completed, gradually filling more capabilities across the full clinical-trial lifecycle.

---

## 6. Advanced Reference (for developers)

CLI helpers, runtime requirements, the architecture tree, and scanner false-positive notes have moved here so everyday users don't need them. See [`SKILL.md`](SKILL.md) and [`CHANGELOG.md`](CHANGELOG.md) for the agent-facing spec and version history.

### Runtime & requirements
| Item | Requirement |
|---|---|
| Runtime | The agent reads `knowledge/` directly — **no mandatory dependency**. |
| Optional CLI helpers | `python3` (stdlib only). `scripts/*.py` load `scripts/*.json` via `json` — **no PyYAML**. |
| Sibling skills | `ct-registry`, `ct-safety`, `ct-literature`, `ct-samplesize` (only for data routing / grounding; the competitive-intel brief is stitched in-house from the three; missing ones degrade gracefully). |
| Coze mode (opt-in) | `config.json` `backend: coze` + `coze.bot_id`; `requests` used only when Coze is enabled. |

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
└── config.json           # runtime backend selector (default: local, zero outbound)
```

### CLI examples (developers)
```bash
python3 scripts/check_deps.py     # local capability probe (no install, no network)
python3 scripts/menu.py --all     # dump the clarification menu as JSON
python3 scripts/menu.py --tier data_skill --human --lang zh   # preview one tier
```

### Security scanner false positives Some automated scanners flag `adapters/` because it contains strings that look network- or credential-related. **These are inert stubs and are never executed in the default (local) mode** — `CozeBackend._post()` is only reached when `config.json` sets `backend: coze` and `coze.bot_id` is configured; `import requests` is lazy; no secrets are in the repo (the Coze token is read from the `COZE_TOKEN` env var at call time). Run the skill as shipped and it stays zero-outbound.

---

**Version**: v0.8.0 | **License**: MIT | **Authors**: medstatstar, phoe-zip

For feature requests, bug reports, or other feedback, please contact the author directly at medstatstar@gmail.com (Wintone Zhang).

---

## Confidentiality Notice

> The CT series consists of 16+ specialized domain skills, organized into four tiers — A, B, C, D — by "confidential-data-exfiltration risk + whether external retrieval is needed", providing full coverage of the entire new-drug clinical trial (Clinical Trial) lifecycle.

> - **Tier A / B (non-confidential)**: run fully locally using only ordinary data; Tier B may need external public retrieval but involves no confidential information. These skills are published openly on GitHub.
> - **Tier C / D (confidential)**: involve strictly confidential clinical-trial data and internal information from pharma sponsors (e.g., ct-analysis, ct-sdtm); Tier C is processed locally and never leaves the boundary, while Tier D additionally requires policy approval. These skills are designated for internal enterprise use only and are not publicly released at present.

> If you do have a genuine need for these confidential skills, please contact the author to request custom installation.

> 📧 Contact: medstatstar@gmail.com (Wintone Zhang)
