# Atomic Task Units — ct-advisor (per ct-base §7)

> Each capability of ct-advisor is decomposed into atomic units. Schema: Input / Output / Dependency / AI autonomy (⬛ fully automatic / 🟨 semi-automatic / ⬜ assisted) / Combination interface (→ downstream unit ID). Units are owned by `scripts/workflows.json` (the runtime registry) and referenced from `knowledge/system_prompt.md` + `SKILL.md`.

---

## Entry & Triage

### UNIT-0 · Clarification Gate (gate 0)
- **Input**: user's first message (raw natural language). Optional: role / stage / materials.
- **Output**: triage classification (`simple` / `complex` / `vague`) + clarification menu (if complex) or grill-me probing (if vague) + confirmed problem profile.
- **Dependency**: none (entry unit).
- **AI autonomy**: 🟨 semi-automatic — menu/grill-me rendering is automatic, but conclusion-changing questions require user confirmation.
- **Combination interface**: → UNIT-A…J (route by triage).

---

## Methodology Workflows (A–J)

### UNIT-A · Explain & locate evidence
- **Input**: concept / term / "why" question + jurisdiction (optional). Reads `ref-ops-contract.md` + `ref-reg-contract.md` + `ref-regulatory-versions.md`.
- **Output**: conclusion / boundary / example / common-mistake / regulatory citation card; `⚠️ verify-official` flag on dynamic items.
- **Dependency**: UNIT-0.
- **AI autonomy**: ⬛ fully automatic (local knowledge retrieval).
- **Combination interface**: → UNIT-H (A's output can be QC-reviewed).

### UNIT-B · Trial design
- **Input**: design goal + population / endpoint / control / blinding choices + therapeutic area. Reads `ref-reg-contract.md` + `ref-ops-contract.md`.
- **Output**: design chain (goal → clinical question → estimand → population → intervention → endpoint → randomization/blinding → data collection → analysis → feasibility → conclusion) + option trade-off + risks.
- **Dependency**: UNIT-0.
- **AI autonomy**: 🟨 semi-automatic (design choices confirmed with user).
- **Combination interface**: → UNIT-C (estimand feeds stats) / → UNIT-H.

### UNIT-C · Statistics & estimands
- **Input**: estimand strategy + sample-size parameters (effect size, α, power, dropout) + analysis-set / missing / multiplicity. Reads `ref-reg-contract.md`.
- **Output**: method framework + parameter gap analysis; when parameters complete → handoff payload to `ct-samplesize`.
- **Dependency**: UNIT-B (design context).
- **AI autonomy**: 🟨 semi-automatic (parameter confirmation) → ⬛ fully automatic (handoff).
- **Combination interface**: → `ct-samplesize` (external skill) / → UNIT-H.

### UNIT-D · GCP & quality
- **Input**: GCP / ethics / deviation / CAPA / monitoring / data-quality scenario. Reads `ref-ops-contract.md`.
- **Output**: impact judgment + responsibility + escalation + CAPA recommendation.
- **Dependency**: UNIT-0.
- **AI autonomy**: ⬛ fully automatic.
- **Combination interface**: → UNIT-H.

### UNIT-E · Clinical operations
- **Input**: site / supplier / RBM / recruitment / IP / data / randomization / lock / close scenario. Reads `ref-ops-contract.md`.
- **Output**: dependencies + RACI + risk triggers + closed-loop actions.
- **Dependency**: UNIT-0.
- **AI autonomy**: ⬛ fully automatic.
- **Combination interface**: → UNIT-H.

### UNIT-F · Safety & DSUR
- **Input**: AE/SAE/SUSAR / signal / RSI / benefit-risk / DSUR scenario. Reads `ref-reg-contract.md` + `ref-ops-contract.md`.
- **Output**: case classification + RSI versioning + reporting path + aggregate analysis + action + regulatory basis.
- **Dependency**: UNIT-0.
- **AI autonomy**: ⬛ fully automatic.
- **Combination interface**: → UNIT-H / → ct-safety (data grounding).

### UNIT-G · Documents & reports
- **Input**: CSR planning / writing inputs / consistency review. Reads `ref-reg-contract.md` + `ref-ops-contract.md`.
- **Output**: document dependency + consistency chain + issue priority + fix recommendation.
- **Dependency**: UNIT-B/C/D/E/F (consumes their outputs).
- **AI autonomy**: 🟨 semi-automatic.
- **Combination interface**: → UNIT-H.

### UNIT-H · Methodology QC
- **Input**: protocol / statistical strategy / document pack / workflow under review + the `reads[]` of the workflow being reviewed. Reads `ref-reg-contract.md` + `ref-ops-contract.md`.
- **Output**: overall judgment (acceptable / conditionally acceptable / unacceptable) + issue list (evidence/impact/priority) + fix plan + document gap + next quality gate.
- **Dependency**: UNIT-A…G (any workflow output can be the QC target).
- **AI autonomy**: 🟨 semi-automatic (judgment + fix plan confirmed with user).
- **Combination interface**: → UNIT-J (memory of QC decisions, if user asks to save).

### UNIT-I · User tone writing
- **Input**: user's own article/email/sample + "reply in this tone" or "draft new". Reads `ref-interaction-style.md`.
- **Output**: style portrait + tone-matched reply or new draft + fact-boundary note.
- **Dependency**: UNIT-0.
- **AI autonomy**: 🟨 semi-automatic (style portrait confirmed; clinical/regulatory facts still verified per §6.1).
- **Combination interface**: → UNIT-H (I's output can be QC-reviewed).

### UNIT-J · User local memory
- **Input**: explicit user request to remember a preference / decision. Reads `ref-interaction-style.md`.
- **Output**: minimal, reviewable, deletable local memory entry written to WorkBuddy memory mechanism.
- **Dependency**: UNIT-0 + explicit user authorization.
- **AI autonomy**: ⬜ assisted (writes only after explicit confirmation; never self-initiates).
- **Combination interface**: none (terminal unit).

---

## Routing & Data-Grounding Units

### UNIT-R1 · Route to ct-registry
- **Input**: "registered trials" / "competitor landscape" drug/indication query.
- **Output**: search plan → live registry landscape from ct-registry (with "Data source: ct-registry on <date>" labels).
- **Dependency**: UNIT-0 triage = data_intel.
- **AI autonomy**: 🟨 semi-automatic (search plan confirmed before fetch).
- **Combination interface**: → UNIT-R4 (stitch).

### UNIT-R2 · Route to ct-safety
- **Input**: "safety signals" / "FAERS" / "PRR/ROR" drug-event query.
- **Output**: search plan → live FAERS signals from ct-safety.
- **Dependency**: UNIT-0.
- **AI autonomy**: 🟨 semi-automatic.
- **Combination interface**: → UNIT-R4.

### UNIT-R3 · Route to ct-literature
- **Input**: "published evidence" / "systematic reviews" query.
- **Output**: search plan → normalized literature from ct-literature.
- **Dependency**: UNIT-0.
- **AI autonomy**: 🟨 semi-automatic.
- **Combination interface**: → UNIT-R4.

### UNIT-R4 · Stitch competitive-intel brief (in-house)
- **Input**: outputs from UNIT-R1 + UNIT-R2 + UNIT-R3 (one call each).
- **Output**: consolidated Strategic Brief with per-claim "Data source: ct-xxx on <date>" labels.
- **Dependency**: UNIT-R1 + UNIT-R2 + UNIT-R3.
- **AI autonomy**: ⬛ fully automatic (stitching is in-house synthesis).
- **Combination interface**: → UNIT-H (brief can be QC-reviewed) / → UNIT-J.

### UNIT-R5 · Handoff to ct-samplesize
- **Input**: complete sample-size parameters (from UNIT-C).
- **Output**: computed n / power from ct-samplesize.
- **Dependency**: UNIT-C (parameters complete).
- **AI autonomy**: 🟨 semi-automatic (parameter confirmation) → ⬛ fully automatic (external compute).
- **Combination interface**: → UNIT-C (result feeds back) / → UNIT-G (n feeds CSR planning).

---

## Composite Routes (orchestrate units)

| Composite route | Unit sequence |
|---|---|
| Confirmatory trial design | 0 → B → C → D → E |
| Full lifecycle / training / QC | A → B → C → D → E → F → G → H |
| Regulatory strategy & China filing | A → B (+ ref-regulatory-*) |
| Safety aggregate (DSUR) | F (+ ct-safety data grounding) |
| Methodology QC consuming sibling output | H (+ reads_sibling=true) |
| Full competitive-intel brief | R1 + R2 + R3 → R4 (stitched in-house) |
