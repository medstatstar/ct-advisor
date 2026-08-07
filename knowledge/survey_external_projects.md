# External Similar-Project Survey Reference Report (GitHub + ClawHub / OpenClaw)

> Purpose: To survey GitHub and the ClawHub / OpenClaw ecosystem for similar clinical-trial / medical AI agent projects, and extract reusable insights for ct-advisor. Survey date: 2026-08-02. Red-line constraint (in effect throughout): This report is for local reference only, **no git push / no publish**; for regulatory versions and any dynamic items, always retain an "official verification" marker and never embed full regulatory text; any downstream adaptation must first be confirmed with the user.

---

## 1. Project Map (by type)

| # | Project | Type | Core Tech | Relevance to ct-advisor |
|---|---------|------|-----------|--------------------------|
| 1 | A-xin946/clinical-trial-advisor | Upstream origin Skill | Markdown three-reference structure | High (adaptation source) |
| 2 | arnold117/clinical-trial-advisor | Mirror fork | Same as above | Medium (sync verification) |
| 3 | cyanheads/clinicaltrialsgov-mcp-server | ClinicalTrials.gov MCP | FastMCP / STDIO+HTTP | Medium (data_intel reusable) |
| 4 | pascalwhoop/medical-mcps（medical-research-toolkit） | Unified biomedical MCP | 14+ library unified endpoint + ID normalization | Medium (data_intel backend) |
| 5 | CONSORT-RCT-Assistant (pouriamrt) | RAG + hallucination guardrails | LangChain/LangGraph/Chainlit | High (evidence-boundary idea is isomorphic) |
| 6 | clinical-protocol-review (pooja-k-swamy) | Multi-agent protocol review | LangChain + MCP interface + risk scoring | Medium (review paradigm) |
| 7 | Microsoft Prior-Authorization-Multi-Agent | Multi-agent + HITL + audit | 4 Agents + Pydantic structured output | High (architectural philosophy fits) |
| 8 | Clinical-Trial-Success-Predictor | FAISS RAG + metadata manifest | docs_manifest.csv | Medium (knowledge-base metadata control) |
| 9 | NexClinicalMind | Compliance autonomous sentinel | Google ADK + Gemini + CrewAI + MCP | Low (CDISC sentinel, out of scope) |
| 10 | ClinTrialsGPT | A2A-protocol Agentic RAG | Agent-to-Agent | Low (protocol layer, not needed yet) |
| 11 | OpenClaw-Medical-Skills (aradotso/hermes) | Medical Skill collection | 869 modules / FDA·CE·IEC62304·ISO14971 templates | Medium (regulatory template reference) |
| 12 | 云知声五大医疗 Skill | Medical assistant (Chinese) | "living medical-logic engine" backend | Low (commercial backend, not reusable) |
| 13 | Andyxcg/intelligent-triage-symptom-analysis | Symptom triage | 650+ symptoms, 5-tier grading | Low (triage, not trial design) |

---

## 2. Reusable Takeaways by Category

### 2.1 Defining Agent Behavior in Markdown — Strongly Aligned with ct-advisor Architecture (strong validation)
- **Microsoft Prior-Authorization** states a clear principle: *Agent behavior defined in markdown skill files, not Python code*; when CMS policy updates, **clinical/compliance staff edit one text file and redeploy — no engineering PR needed**.
- **ct-advisor current state**: SKILL.md + `knowledge/ref-*.md` + `menu.yaml` + `workflows.yaml` + `system_prompt.md` + `prompts.md` fully define behavior in Markdown/YAML, with dynamic items carrying an "official verification" marker.
- **Conclusion**: A mature external project validates that ct-advisor's "knowledge-as-configuration" design is correct. No changes needed; recommend **preserving and strengthening** this paradigm.

### 2.2 Knowledge-Base Metadata Manifest (docs_manifest idea) — High Fit, Low Cost
- **Clinical-Trial-Success-Predictor** uses `docs_manifest.csv` to control corpus metadata (source / version / validity period).
- **ct-advisor current state**: `ref-regulatory-versions.md` already has a maintenance date (2026-08-01) and an official-verification entry point, but the three main files lack a unified "metadata header".
- **Recommendation**: Add a YAML header block or a separate `_manifest.yaml` to `ref-ops-contract.md` / `ref-reg-contract.md` / `ref-regulatory-versions.md`:
  ```yaml
  file: ref-reg-contract.md
  version: 2026-08-01
  source_urls: [ich.org, nmpa.gov.cn, fda.gov]
  last_verified: 2026-08-01
  next_refresh: 2027-02-01   # every 6–12 months
  ```
  This directly supports the "official verification" audit chain and eases future priority-indexed compression/splitting of the knowledge base.

### 2.3 RAG + Hallucination Guardrails (Grounding Score / Hallucination Guard) — Isomorphic to Evidence Boundaries
- **CONSORT-RCT-Assistant**: 916-paper RAG + Self-Query Retriever; every answer passes through an **LLM JSON scoring step for Grounding / Hallucination checks**, with low grounding blocked outright.
- **ct-advisor current state**: "Evidence boundary + dynamic-item official verification" is equivalent in spirit — answers must be traceable, and dynamic items must be flagged for verification.
- **Recommendation (enhance existing, do not introduce RAG)**: Add a hard rule to `prompts.md` — *any factual assertion must cite its source section (e.g. §3.6); any claim with no citable source must be marked "official verification" and prompt the user to double-check*. This lands CONSORT's "guardrail" idea in pure-methodology fashion, without violating the "pure methodology, no network" red line.

### 2.4 MCP Server Access to Registries / Biomedical Libraries — Related to data_intel Layer, but Overlaps with ct-registry
- **cyanheads/clinicaltrialsgov-mcp-server** v1.5.0 (2025-10-15, 92.46% coverage, 190+ tests): STDIO/HTTP dual transport; `find_eligible_studies` (patient matching), `compare_studies`, `time-series`; auth supports none/jwt/oauth; Apache-2.0.
- **pascalwhoop/medical-mcps** (medical-research-toolkit): unified endpoint `https://mcp.cloud.curiloo.com/tools/unified/mcp`, **100+ tools covering 14+ libraries** (ChEMBL/OpenTargets/ClinicalTrials.gov/PubMed/OpenFDA/OMIM/nodenorm, etc.); nodenorm for ID normalization; most libraries key-free (OMIM/NCI require a key); MIT.
- **ct-advisor current state**: The pure-methodology layer **does not connect to the network and does not call sibling skills**; but the data_intel layer is already allowed to call the **ct-registry skill** present in this workspace (already covering ClinicalTrials.gov/WHO ICTRP/CDE/PubChem).
- **Recommendation**: If data_intel needs real-time data, **reuse the ct-registry skill first**, avoiding the dual-maintenance cost of adding cyanheads/pascalwhoop MCPs. Only when ct-registry does not cover a given library (e.g. OpenFDA pharmacovigilance, ChEMBL targets) should the pascalwhoop unified endpoint be considered. Priority: Low–Medium.

### 2.5 Multi-Agent Protocol Review + Risk Scoring — Future Enhancement
- **clinical-protocol-review**: PI / Site Physician / Health Authority three-role Agents; MCP interface exposes the protocol by section; `risk_assessor` assigns Low/Medium/High severity; `scoring_engine` gives a numeric total score; Streamlit UI.
- **Microsoft Prior-Auth**: 4 Agents (Compliance/Clinical Reviewer/Coverage/Synthesis) in parallel+sequential pipeline; **structured Pydantic output (no JSON parsing)**; **HITL defaults to LENIENT (no auto-rejection; requires clinician Accept/Override with reason recorded)**; 8-section audit PDF.
- **ct-advisor current state**: Single-agent methodology advisor, Workflow A–K.
- **Recommendation (future, not current)**: Add a "multi-perspective review checklist" to protocol-design Workflows (B-layer methodology) — three columns for scientific rigor (PI) / feasibility (Site) / regulatory compliance (HA) + severity grading + total score. The structured-output and HITL-audit ideas can be folded directly into `prompts.md`'s output template. This is a large architectural change; do it only after user confirmation.

### 2.6 ClawHub / OpenClaw Publishing Model — Optional, Bound by Red Line
- pascalwhoop publishes medical-mcps + medical-research-toolkit as an OpenClaw Skill; OpenClaw-Medical-Skills contains 869 modules; 云知声 emphasizes a continuously-updated "living medical-logic engine" backend.
- **ct-advisor current state**: A local skill; the user has explicitly stated "stay local, do not commit / do not publish".
- **Recommendation**: Record only as a **future optional action** — if publishing to ClawHub later, reference pascalwhoop's SKILL.md + OPENCLAW-USAGE.md structure. Current red line: **no publishing, wait for user confirmation**.

---

## 3. Fit Matrix Against ct-advisor's Current Architecture

| External Pattern | ct-advisor Corresponding Layer | Fit | Implementation Cost | Notes |
|------------------|-------------------------------|-----|---------------------|-------|
| Markdown-defined behavior | SKILL.md + ref-*.md | ★★★★★ | None (already present) | External validation confirms design is correct |
| Knowledge-base metadata manifest | ref-*.md header block | ★★★★★ | Low | Directly supports official verification |
| Hallucination guard / Grounding | Evidence boundary + prompts.md | ★★★★☆ | Low | Add traceability hard rule |
| Structured output + HITL audit | prompts.md output template | ★★★★☆ | Medium | Enhances review-type Workflows |
| Multi-agent protocol review | B-layer methodology Workflow | ★★★☆☆ | High | Architectural extension, pending confirmation |
| Registry MCP (cyanheads) | data_intel layer | ★★☆☆☆ | Medium | Overlaps with ct-registry |
| Unified biomedical MCP | data_intel layer | ★★☆☆☆ | Medium | Only fills ct-registry blind spots |
| ClawHub publishing | Release process | ★☆☆☆☆ | Low | Red line: wait for confirmation |
| A2A / CDISC sentinel | — | ☆☆☆☆☆ | — | Out of scope, not adopted |

---

## 4. Actionable Recommendations (by priority, with red-line markers)

1. **[High · Low cost] Add knowledge-base metadata headers**: Add a YAML header (version/source_urls/last_verified/next_refresh) to the three ref-*.md files. Local change, no push.
2. **[High · Low cost] Add "traceability hard rule" to prompts.md**: Factual assertions must cite § section; claims with no source marked "official verification". Strengthens evidence boundary, no network.
3. **[Medium · Medium cost] Add structured output + HITL audit section to the output template**: Review/design answers carry severity grading and a "requires human verification" prompt.
4. **[Low · Medium cost] data_intel real-time data should reuse ct-registry first**: Avoid redundantly mounting external MCPs.
5. **[Optional · Red line] ClawHub publishing**: Only after the user explicitly confirms.

---

## 5. Not Recommended / Proceed with Caution

- **NexClinicalMind (CDISC compliance sentinel), ClinTrialsGPT (A2A)**: Beyond ct-advisor's "methodology advisor" scope, and introduce persistent-networked autonomy, conflicting with the "pure methodology, no network / evidence boundary" red line.
- **云知声 "living medical-logic engine"**: Relies on a commercial backend with automatic updates, contradicting the local-controllable strategy of "dynamic items officially verified + manually refreshed every 6–12 months"; its auto-update philosophy is not adopted.
- **Redundantly introducing external MCPs**: ct-registry already covers the main registries; mounting cyanheads/pascalwhoop again would create dual maintenance and version-drift risk.

---

*This report is a local reference document; all downstream adaptations must first be confirmed with the user; the red lines (no push / no publish / dynamic items officially verified) remain in effect throughout.*
