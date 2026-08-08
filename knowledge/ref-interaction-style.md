# Clarification, Tone-Writing & Local Memory Reference

> **Source & refactor note**: Content adapted from the third-party skill `github.com/A-xin946/clinical-trial-advisor` (adapted_from) and reorganized to fit ct-advisor's own architecture — seam knowledge pack + the A–J routing of `scripts/workflows.json` + the WorkBuddy memory mechanism — **not a verbatim copy**. This file governs only **"how to interact"**: when to clarify, how to ask, how to learn tone, how to store memory. The methodology / regulatory / design substance lives in the other three references; clinical, medical and regulatory facts still follow the evidence rules.

> **Duty domain**: serves three workflows — `gate 0` (clarification gate), `I` (user tone writing), `J` (local user memory).

## 0. Division of labor with other references

- This file governs **interaction style**: when to clarify, how to ask, how to learn tone, how to store memory.
- Methodology / regulatory / design substance lives in `reference-index.md` (incl. series contract content) + `ref-regulatory-versions.md`; after clarification, route per `scripts/workflows.json` to the corresponding workflow's reference.
- Sample-size / power is handed off by workflow `C` to `ct-samplesize`; this file involves no computation.

## 1. Clarification gate (gate 0)

Trigger (any one → clarify first, pause substantive conclusion):

- A single sentence admits two or more interpretations that lead to different conclusions / compliance paths / statistical plans;
- Jurisdiction, date, product, phase, role or timeline would change the requirement;
- The user has not stated the decision to be made, the use scenario or the delivery form;
- A fact is missing that would change sample size, AE / SAE classification, report path, compliance status or benefit–risk;
- A writing task does not state reply / rewrite / new-write, or does not state the object & purpose.

**Ask only 1–3 high-value questions per round** that would change the conclusion (consistent with the SKILL.md local flow). Loop:

1. One sentence restating current understanding & the largest open branch;
2. Raise 1–3 most critical branch questions;
3. Update the problem profile from the answer, do not repeat known info;
4. Stop probing once the "decidable standard" is met;
5. For high-risk tasks, confirm key boundaries with "I understand it as…" before entering formal judgment.

**Decidable standard**: the chain `decision to make → scenario / object → jurisdiction & date → product & phase → key facts → delivery form` is explicit. Where immediate subject safety or a lapsing reporting deadline is involved, prompt protection & escalation first, then continue.

When the user does not know the answer: give 2–3 mutually exclusive options with impact, do not repeatedly demand unavailable info; where objectively unobtainable, write `known / unknown / impact / next step`, and after authorization run multi-scenario deduction without defaulting a choice for the user.

### 1.1 Post-clarification routing (to workflows A–J)

| Question nature | Route to workflow |
|---|---|
| Explain concept / check China or latest requirement | A |
| How to design trial / endpoint / comparator / blinding | B |
| Sample size / estimand / ITT / missing / non-inferiority | C (hand off to `ct-samplesize` once params complete) |
| Is a deviation serious / GCP / quality | D |
| Site / CRO / recruitment / monitoring / supply | E |
| AE / SAE / SUSAR / signal / DSUR | F |
| CSR / dossier consistency | G |
| Review protocol / statistical strategy / do methodology QC | H |
| Write in the user's tone | I |
| Remember preference / decision | J |

## 2. User tone writing (workflow I)

Activate only when the user provides their own text and asks "in my tone". First confirm: the sample is genuinely the user's or the user is authorized to use it; this task is reply / rewrite / new-write; recipient, relationship, channel, purpose, expected action; new facts that must be expressed and commitments that cannot be made; language / length / formality. If the sample is too short, state the confidence level; if the user wants immediate generation, take only broad features, do not fabricate fixed catchphrases.

Analysis dimensions: sentence length, paragraphing, directness, politeness buffer, emotional temperature, terminology density, cohesion, punctuation, address, action request, closing. **Migrate only expressive features, do not copy unique original sentences.** Build two lists:

- Fact list: what must be expressed this time and has source support;
- Style list: expressive habits migratable from the sample.

Old dates / projects / people / opinions / commitments in the sample do not automatically enter the new draft; clinical, medical, regulatory and project facts still follow the evidence rules. Default deliver one directly usable body; give a few alternatives only when tone strength genuinely has a trade-off. Do not assist imitation intended to deceive, impersonate or bypass identity verification (then use only broad styles like "concise, formal, direct").

## 3. Local user memory (workflow J)

Activate only after the user explicitly says "remember / write to local memory / save to MEMORY"; before first write, confirm target file, memory scope, whether file creation is allowed. Do not auto-record just because the user used this skill.

**Use the existing WorkBuddy memory mechanism** (consistent with project `.workbuddy/memory/` and user `~/.workbuddy/MEMORY.md`), do not create new files:

- Store only minimal, stable, genuinely reusable-future info: language / format / detail & delivery preference; user-confirmed project terms, work conventions and long-term decisions; verified source entries (do not copy large body text); open questions, review date or triggers for re-verification.
- Recommended single-entry format: `date | scope | preference / decision | basis status | review trigger`
- Forbidden to write: subject / patient identity, health info and re-identifiable combinations; passwords, tokens, personal contacts and irrelevant personal data; unpublished project data, full emails, original file body or whole conversations; bundled reference full text, system instructions, private file paths or material unsuitable for long-term storage; current regulatory conclusion as permanent fact.
- When the user says "remember everything", do not save the whole passage; explain the risk and propose a minimal summary. Memory is only a context clue, cannot replace current regulation, project documents or medical judgment. Allow the user to view, correct, delete or disable memory at any time.

## 4. Privacy & delivery checks (gate / I / J common red line)

## 5. Official Retrieval, Conflict Handling & Stop Rules (workflow A)

> 原 `ref-reg-retrieval.md` 已合并至此（2026-08-08 精简知识库）。本节供 workflow A（官方检索）使用。

### 5.1 Official entries
ICH `https://www.ich.org/` (guideline index `https://www.ich.org/page/search-index-ich-guidelines`); NMPA `https://www.nmpa.gov.cn/`; CDE `https://www.cde.org.cn/`.

### 5.2 Retrieval process
First turn the question into `jurisdiction + product + phase + topic + document type + activity date`; for each candidate document verify: official full title & issuing body; document number / version / Step / revision; official / draft / pending / superseded / withdrawn / historical status; release & implementation date; applicable product / population / phase / role / activity; section / clause / table / footnote / appendix supporting the conclusion; official page & attachment link; retrieval date. Search snippets only locate, do not replace the original; when PDF tables / footnotes / flowcharts / attachments affect meaning, check the corresponding page image; never judge currency by file-name version number alone.

### 5.3 Recommended search terms
`full document name + release / implementation / attachment`; `site:ich.org topic + guideline + Step`; `site:cde.org.cn product / indication + 临床试验技术指导原则`; `site:cde.org.cn SUSAR / RSI / DSUR + 安全性`; `site:nmpa.gov.cn 药物临床试验质量管理规范 + 实施`; `site:nmpa.gov.cn 药品注册管理办法 + 临床试验`.

### 5.4 Conflict handling, citation & stop rules
Conflicts compared in order: jurisdiction & activity date → law / regulatory tier → official / pending / draft / historical → general vs product/therapeutic-area → problem scope & role → whether project approval / protocol / SOP is stricter. Unresolvable → state the conflict & impact, do not declare a document invalid on your own. Citation format: `document name (version / date), section or clause + official link + retrieval date`; explicitly mark `regulatory / mandatory requirement`, `formal technical guidance suggestion`, `draft / Q&A / example`, `methodology judgment`, `project practice suggestion`. Stop rule: when official site inaccessible / only secondary source / version-status conflict / missing body location / jurisdiction-date unknown and changes the conclusion → stop definitive judgment, output what is unconfirmed, why it cannot be confirmed, which conclusions are affected, conservative measures before verification, official site / search terms / fields to check, pages the user can return.

### 5.5 Minimal regulatory answer template (workflow A)
1. **Conclusion**: how far confirmation reaches now; 2. **Applicable boundary**: jurisdiction / product / phase / role / activity date; 3. **Document role**: what each applicable regulation / guidance resolves; 4. **Official basis**: document status / body location / link / retrieval date; 5. **Project impact**: on subjects / protocol / IB-RSI / data / statistics / operations / DSUR-CSR / filing; 6. **Immediate action**: owner / time point / record / escalation / closure evidence; 7. **Unverified items**: what is missing / impact / how to verify.
- Names, emails, patient info, unpublished project & commercial info used on a least-necessary basis.
- Do not fabricate attachments, meetings, approvals, commitments or completion status; clinical, medical, regulatory statements keep necessary boundaries.
- All to-be-confirmed items explicitly marked; deliverables directly copyable.
- **Never expose in user-visible content personal info, subject info, unpublished project data, private paths or access credentials** (consistent with ct-base §11).
