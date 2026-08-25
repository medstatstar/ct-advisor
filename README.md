# Clinical Trial Chief Advisor (ct-advisor)

- **English guide** → [README.md](https://github.com/medstatstar/ct-advisor/blob/main/README.md) · **中文指南** → [README_zh-CN.md](https://github.com/medstatstar/ct-advisor/blob/main/README_zh-CN.md)

<div align="center">
<img src="assets/icon.svg" width="240" height="240" alt="ct-advisor logo"/>
</div>

> **The single front door for the whole `ct-*` clinical-trial skill family — a methodology & regulatory-evidence advisor. Every **non-vague** question is first passed through a deterministic, LLM-free local orchestrator (`scripts/orchestrate.py`): it may prefetch the needed sibling data skill (ct-registry / ct-safety / ct-literature / ct-samplesize) **in parallel** with the Coze cloud workflow, then merge and stitch the result **in code** — the agent only relays the final answer verbatim. A `vague` question is first clarified locally via the Local Clarify Loop (`scripts/clarify_loop.py`), then re-routed. When Coze (or the prefetch) needs a sibling data skill, the call runs **locally** and the result is stitched in by code; local `knowledge/` serves only as the Coze-failure fallback.**
>
> No commands or manual needed. Just describe your trial question **in plain language inside a chat** — the advisor passes it to the local orchestrator, which forwards to the Coze cloud workflow for methodology / design / statistics / GCP / safety / regulatory / QC / tone answers, and for real-data or competitive-intel needs runs the right sibling skill (`ct-registry` / `ct-safety` / `ct-literature` / `ct-samplesize`) **locally** and stitches the result in **code**. It **re-implements no** retrieval or computation logic. A-tier.

---

> **Scope reality check (read this first).** ct-advisor is a **cloud-assisted** advisor, not a pure-local tool. In operation it forwards your **question to the remote Coze engine**; runs sibling `ct-*` skills **locally on your machine** (these skills themselves may query public registries/APIs such as ClinicalTrials.gov, China CDE, FDA FAERS/openFDA, OpenAlex, PubChem); submits an **optional** bug report; keeps a language preference / context cache / memory notes on your device; and runs local connectivity diagnostics. All of this is spelled out honestly in §5 Data & Privacy.

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
> No problem — a "half-written protocol with loose ends" state is common. Before I analyse anything formally, let me help you scope it. Two questions plus a "what I can help with" menu below; answer whichever you like, no need to cover all.
>
> **First, two things that most affect direction:**
> 1. Who is the **target population** (disease, stage, line of therapy, age)? — this decides whether conclusions apply to your protocol.
> 2. Which **endpoint** do you care about most (OS, PFS, ORR, AE rate, quality of life…)? *(If you mention "compared to what", I'll also ask the comparator.)*
>
> **What kind of help do you want** (reply with a number or in your own words):
> 1. Protocol review — point-by-point check of the draft: what's missing, where the design has gaps / compliance risks.
> 2. Design consulting — one module is unclear: randomisation / blinding / eligibility / statistical assumptions.
> 3. Sample size — give me population / endpoint / expected effect, I'll route to ct-samplesize for numbers + figures.
> 4. Endpoints & statistical plan — how to choose primary/secondary endpoints, how to sequence hypothesis tests, how to define FAS/PPS/SS.
> 5. Specific Q&A — just throw your scattered questions at me, I'll answer them one by one.
> 6. Full read-through — paste or upload the half-written protocol (docx/pdf); after reading I'll tell you exactly where it's stuck and what to add next.
>
> The easiest step is still #6: paste the half-written protocol and I stop guessing.

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

**Q: What if I found an error in the result — how do I report it?**
A: This skill follows the ct-base §20.3 bug-report workflow. If you suspect the result is wrong (or the engine errored), just say **"report a bug" / "上报问题" / "提交错误报告"**. The skill also **proactively asks** whether to report when it detects a likely defect (e.g. the engine errors or retries still fail) — at most **once per session**, and you can always decline. Either way, the assistant will:
1. **Propose a sanitized report** (11-field whitelist: skill / skill_version / test / error_type / error_code / engine_status / description / locale / query_origin / session_hash / attempts — **no raw input values or personal data**, except the `description` field where you decide what to disclose, e.g. the algorithm/function used and the error message);
2. **Show the full report text for your review** — you can add a problem description or correct anything before confirming;
3. **Send after your explicit confirmation** — to the unified endpoint `https://ct-bugreport.coze.site/run` (if this session called coze) or saved locally + emailed to the author (if purely local, data never leaves your machine);
4. **Receive an acknowledgment** — including whether a previously submitted report from your source has already been fixed (with the fix note) or is still pending.

You stay in full control: the report is shown to you **before** anything is sent, and nothing is transmitted without your explicit "send" confirmation.

**Q: What if my data must stay confidential?** A: The advisor only sends your **question text** to the Coze endpoint (`https://ct-advisor.coze.site/run`) — never your raw trial / patient / sponsor data. Outbound payloads pass through `sanitize()` first (strips IDs, phone numbers, emails, and a small set of sensitive keywords; `query_origin` is a non-PII `sha256` machine id, `locale` is your OS language). Sibling data skills (ct-registry / ct-safety / ct-literature / ct-samplesize) run **locally** and only their results cross back; confidential data never leaves your machine. If you have strict confidentiality needs, simply keep real patient / sponsor data out of your question — the advisory answers are framework-level and don't require exposing it.

---

## 4. Execution Model & Safe Preview

### Safe Preview (sibling skills dispatched by default)
- **Dispatched by default:** For `data_intel` asks (competitive landscape / safety signals / literature / sample size), the advisor **dispatches directly to the relevant sibling skill** (ct-registry / ct-safety / ct-literature / ct-samplesize) by default to complete the analysis and return live results — no need to say "please fetch the data now". If you only want the plan and not the data yet, say "just show the plan".
- **Traceable, not fabricated:** Every factual / normative claim carries a source citation or an `⚠️ needs official verification` marker; it never fills factual gaps with fluent prose.
- Outputs are for reference only; validate against official sources before regulatory submissions.

### Latency note
Every **non-vague** question is handled by the local orchestrator (`scripts/orchestrate.py`), which forwards to the Coze endpoint in a **single call** (usually returns in **~20s**; data-intel questions also run the needed sibling skill locally in parallel). A `vague` question is clarified locally first (a few seconds via the Local Clarify Loop), then re-routed. Because the orchestrator, prefetch, merge, and stitching are all **code** (not the LLM), dependence on the local model's performance is low — but reasoning models (e.g. Hunyuan-3, DeepSeek-R1) have been observed to over-think locally. **If a single reply routinely takes longer than 3 minutes, switch to a simpler / flash model to speed things up.**

---

## 5. Data & Privacy

**This skill is cloud-assisted, not a pure-local tool.** To give current, source-traced answers it forwards your question to a remote engine and may run sibling skills on your machine. Below is exactly what leaves your device, what stays local, and what sensitive actions it can take — stated up front, not buried.

### What leaves your device (off-device)
- **Analysis request** — for a non-vague question, your **question text** (passed through `sanitize()` first, which strips IDs, phone numbers, emails, and a few sensitive keywords) is sent to `https://ct-advisor.coze.site/run`. **Raw trial / patient / sponsor data is never sent.** When the question needs registry / safety / literature / sample-size data, Coze returns only a `need_tool` instruction; the actual retrieval and computation run **locally** on your machine — but note those local sibling skills (`ct-registry` / `ct-safety` / `ct-literature` / `ct-samplesize`) may themselves query **public registries/APIs** (ClinicalTrials.gov, China CDE, FDA FAERS/openFDA, OpenAlex, PubChem…). That is separate outbound to those public sources, not to Coze.
- **Error report** — sent **only after your explicit confirmation**, and only as an 11-key whitelist envelope (no raw input, no PII), to `https://ct-bugreport.coze.site/run`. You can always decline; it is offered at most once per session.

Each request also carries two anonymous metadata fields: `query_origin` (a SHA-256 hash of your hostname, for rate-limiting only) and `locale` (your OS language, for answer-language matching). Neither contains PII.

### What stays on your device but is still sensitive (on-device actions)
To be transparent about the full behavior the skill can perform:
- **Embedded (public) token** — the skill ships with an obfuscated Coze token used to authenticate the public endpoint. It is a **shared / public credential by design** (not a personal secret); it is decoded in memory only for outbound auth and is disclosed openly here rather than hidden.
- **Local persistence** — it may write your **language preference** to `config.json`, keep a short-lived **context cache** under `.runtime/` (gitignored), and **promote recurring interaction patterns into long-term memory files** (per the SOUL.md self-improvement rules). None of these contain your question text or trial data.
- **Local connectivity diagnostics** — if a connection to Coze fails, with your permission it can run `scripts/check_coze.py` to probe local proxy / network / token configuration and suggest a fix.
- **Subprocess orchestration** — the local code orchestrator (`orchestrate.py` / `refine_answer.py`) runs sibling `ct-*` skills as **subprocesses on your machine** and stitches their results in code.

> **In one sentence:** your question text goes to the Coze endpoint for cloud analysis, sibling skills may query public registries, an optional bug-report goes out only after your OK, and the skill may keep a language preference / context cache / memory notes locally — **raw trial / patient / sponsor data never leaves your machine.**

---

## Why You Can Trust the Output — Anti-Hallucination

ct-advisor is the entry point that routes to sibling skills and forwards questions to the Coze refiner; it does not invent facts. Four guardrails apply:

1. **Every factual claim is source-traceable.** Data-grounded claims from sibling skills carry a "Data source: ct-xxx on <date>" label; methodology / regulatory answers cite the authority (ICH / NMPA / FDA / EMA guidance) and link to it where available.
2. **Identifier consistency check.** When a cited identifier (trial registration number, DOI / PMID) is resolved to a live record, the resolved title / author / year are compared against the original assertion; a mismatch is flagged `mismatch` and never treated as verified.
3. **Unverifiable ⇒ `⚠️ needs official verification`.** Anything that cannot be traced to a public source is marked for official verification and never stated as a confirmed conclusion.
4. **No fabrication.** Trial registration numbers, approval dates, subject counts, and company M&A / pipeline moves are never invented; if a public source does not disclose them, the output says "not disclosed in public sources".

---

## 6. Advanced Reference (moved to a separate file)

CLI helpers, runtime requirements, the architecture tree, and scanner false-positive notes have been moved to **[references/ADVANCED.md](references/ADVANCED.md)**. Ordinary users don't need them; Sections 1–5 cover daily use. The agent-facing spec and version history remain in [`SKILL.md`](SKILL.md) and [`CHANGELOG.md`](CHANGELOG.md).

---

**Version**: v0.9.102 | **License**: MIT | **Authors**: medstatstar, phoe-zip

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
