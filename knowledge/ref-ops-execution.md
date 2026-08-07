---
file: ref-ops-execution.md
version: 2026-08-05
topics: QTL, GCP training, contract & insurance, re-consent, SIV, recruitment & retention, site closeout, IRB/IEC composition, drug return, medical devices, compliance, recruitment advertising, discontinuation/withdrawal; cross-file dependency checklist, pre-delivery quality gate, methodology QC output, minimal answer template
serves_workflows: [B, D, E, G, H]
---

<!-- === merged: ref-ops-execution.md === -->
# Trial Execution Details (workflow E/D · 3.14-3.27)


### 3.14 Trial risk plan and quality tolerance limit (QTL) (workflow E / D) — CtQ→KRI→QTL→CAPA closed loop
- **Context / Role**: Project manager (PM) / QM — develop the trial risk plan based on E6(R3) quality risk management, setting CtQ and quality tolerance limits (QTL).
- **Correct handling path**: ① Identify **critical-to-quality factors (CtQ)** (elements affecting subject safety / result reliability, see §3.6); ② set a **quality tolerance limit (QTL)** for each CtQ — an acceptable deviation threshold, exceeding which triggers action; ③ the risk plan contains: risk description, likelihood/severity, control measures, monitoring indicators (KRI), QTL, escalation path; ④ QTL links with KRI: centralized monitoring (§3.6) monitors in real time, and exceeding the limit triggers root-cause and CAPA; ⑤ the risk plan is updated as the trial progresses and integrated with the monitoring plan and SAP.
- **Key points**: QTL turns "risk-based" from principle into a quantifiable threshold; CtQ→KRI→QTL→CAPA forms a closed loop.
- ⚠️ QTL-setting conventions and E6(R3) quality-risk-management requirements are dynamic items — follow current FDA/EMA/NMPA GCP and risk-management guidance (officially verify).

### 3.15 GCP training system and pre-delegation training (workflow E / D) — training is verifiable qualification evidence
- **Context / Role**: Clinical operations manager / QM — investigators/CRC must complete GCP and protocol training before delegation; how to build the training system, records, and traceability.
- **Correct handling path**: ① **Pre-delegation training**: anyone must complete GCP, protocol, SOP, safety, and system training and pass assessment before being entered in the delegation log (§3.1.2 / §2.4); ② **ongoing training**: protocol amendments, safety-information updates, and audit findings must trigger re-training; ③ **records**: training topic, date, instructor, participants, and assessment results are archived in the ISF/eTMF as verifiable qualification evidence; ④ outsourced/third-party personnel (e.g. home-health nurse, §4.1.2) require the same training + qualification; ⑤ missing or fraudulent training must be treated as a quality risk (CAPA, §6).
- **Key points**: Training is not a "one-time sign-in" — pre-delegation + ongoing + traceability form the qualification loop.
- ⚠️ GCP training content and qualification requirements are dynamic items — follow IRB SOP and current GCP (officially verify).

### 3.16 Trial contract and subject-injury insurance (workflow E / D) — contracting parties, insurance, and indemnification
- **Context / Role**: Institution office / sponsor — the trial contract must define each party's responsibilities, insurance coverage, and the subject-injury compensation process.
- **Correct handling path**: ① **Contracting parties**: signed by sponsor and institution (PI), defining research responsibility, data ownership, costs, IP, and insurance; ② **subject-injury insurance**: per local regulations and GCP, purchase insurance or establish a compensation fund covering trial-related injury (distinct from §3.10 participation compensation — insurance covers harm); ③ **compensation process**: injury determination, claim, and payment path are written into the contract and ICF, with subjects informed; ④ insurance must cover the full trial and a reasonable follow-up period; on institution change (§3.12) the insurance party is updated synchronously; ⑤ multinational multicenter trials must meet each region's statutory insurance/compensation requirements.
- **Key points**: Contract and insurance are the contractual bottom line of subject protection — the injury-compensation path must be transparent in the ICF and contract.
- ⚠️ Insurance mandate, compensation standard, and time limits are dynamic items — follow local regulations, GCP, and the contract (officially verify).

### 3.17 Re-consent timing for substantial amendments (workflow D) — version switch and subject notification
- **Context / Role**: IRB secretary / investigator — after a substantial protocol change (e.g. endpoint change) is approved by the ethics committee, the timing and linkage for re-signing the ICF by already-enrolled subjects.
- **Correct handling path**: ① After the substantial amendment (§3.5) is IRB-approved and the version switched, assess the impact on enrolled subjects' willingness to continue (§2.2 continuing consent); ② **re-consent timing**: per IRB SOP and protocol (commonly re-signing treated subjects within a set window after approval / new ICF effective) — specifics are dynamic; ③ subjects refusing re-sign: must not be forced to continue; handle per protocol (may withdraw or safety-follow only), and record the refusal; ④ version-switch synchronization: delegation, training, ICF/CRF/EDC/IRT/SAP/supplies (§3.5 / §8.1); ⑤ re-sign completion must be tracked to closure; the status and reason of uncompleted subjects are logged.
- **Key points**: Amendment approval ≠ automatic effect — re-signing treated subjects is the closed-loop step of version control and must be tracked by timeline.
- ⚠️ Re-consent timing and version-switch requirements are dynamic items — follow IRB SOP and current GCP (officially verify).

### 3.18 Site Initiation Visit (SIV) and start-up quality (workflow E) — the last gate before the kickoff meeting
- **Context / Role**: CRA / clinical operations manager — a Site Initiation Visit (SIV) must be completed before site screening/enrollment, clarifying start-up conditions and post-start-up responsibilities.
- **Correct handling path**: ① **Pre-start-up**: must first meet the §3.1 start-up quality gate (feasibility, contract, ethics, registration, delegation training, systems/supplies/drug); ② **SIV content**: brief the site team on protocol/GCP/SOP/safety/data systems/drug management/monitoring plan, confirming roles and processes; ③ **start-up confirmation**: all key roles (investigator, sub-I, CRC, pharmacist, lab) are trained and sign off, systems verified usable; ④ **start-up minutes**: record start date, attendees, action items and closure deadlines as evidence of initiation; ⑤ **first-enrollment linkage**: screening/enrollment should not begin until action items are closed — SIV completion ≠ site ready (see §3.1).
- **Key points**: SIV is a node of "knowledge transfer + responsibility confirmation", not a formality; start-up minutes + a complete start-up gate together prove the site is ready.
- ⚠️ SIV content requirements, start-up confirmation checklist, and first-enrollment pre-conditions are dynamic items — follow sponsor SOP and current GCP (officially verify).

### 3.20 Subject recruitment and retention / dropout prevention (workflow E) — recruitment funnel and retention plan
- **Context / Role**: Clinical operations manager / CRA — slow site enrollment and high dropout require recruitment and retention strategy with monitoring.
- **Correct handling path**: ① **Recruitment**: based on §3.2 feasibility, set a recruitment funnel (base/conversion/ramp/seasonal), calibrated against clinic flow, competing trials, and screen-failure rate; multi-channel (investigator referral, registries, community); ② **retention**: reduce visit burden (home visits / DCT §4.1.2), transport/time stipends (§3.10 compliant), clear communication and relationship maintenance, recall subjects for follow-up when needed; ③ **dropout monitoring**: use KRI (§3.6) to monitor dropout rate, window breaches, and withdrawals, warning by dropout mechanism (random/non-random); ④ **dropout impact**: high dropout affects ITT/FAS and power (§4.2.2, §3.2), requiring sensitivity analysis and sponsor escalation; ⑤ **site variation**: low-enrollment / high-dropout sites go through §3.13 performance review.
- **Key points**: Recruitment and retention are the two ends of the feasibility loop — funnel management + burden control + dropout warning together safeguard power.
- ⚠️ Recruitment compliance boundaries, acceptable dropout thresholds, and retention measures are dynamic items — follow IRB SOP and current GCP (officially verify).

### 3.21 Site closeout and data / supplies handover (workflow E) — a verifiable closure loop
- **Context / Role**: CRA / clinical operations manager — when a site completes enrollment/follow-up or terminates early, it must be closed out properly and data/supplies handed over.
- **Correct handling path**: ① **Pre-closeout confirmation**: safety follow-up complete, data queries closed, drug account reconciled/returned, sample status, fund settlement, reports and archiving (see §3.3); ② **data and documents**: ISF/eTMF handover/archiving (§4.1.1), source-data accessibility retained; ③ **supplies**: remaining investigational product returned/destroyed (§4.2.6), equipment returned; ④ **subjects**: complete follow-up or outcome handover, post-withdrawal safety follow-up (§4.1.4); ⑤ **documents**: the closeout report records action-item owner/deadline/tracking.
- **Key points**: Site closeout is a "verifiable wrap-up", not simply stopping visits — safety follow-up, data/account/supplies loop, and archiving are all required.
- ⚠️ Site-closeout conditions, data/supplies handover and retention requirements are dynamic items — follow sponsor SOP and current GCP (officially verify).

### 3.22 Institutional Review Board (IRB / IEC) composition and independent operation (workflow D) — qualifications and firewall of the reviewing body
- **Context / Role**: Institution office / IRB — the IRB/IEC's composition, independence, operating frequency, and conflict-of-interest management ensure review quality.
- **Correct handling path**: ① **Composition**: multi-disciplinary + non-scientific/community members, with review competence and diversity; ② **Independence**: members have no improper financial ties to the sponsor/investigator, and review is free from administrative/economic interference; ③ **Operation**: convened/expedited review procedures and records, continuing-review frequency (§3.7), document archiving; ④ **COI**: members must declare and recuse conflicts of interest (see §2.6); ⑤ **linkage**: connects with §3.5 amendment tiered review and §3.7 continuing review.
- **Key points**: IRB effectiveness lies in "diverse composition + independence + standardized operation" — the independence firewall is the first threshold of subject protection.
- ⚠️ IRB composition, independence requirements, and operating standards are dynamic items — follow IRB SOP and current GCP / ethics-review regulations (officially verify).

### 3.23 Investigational product return, destruction, and count discrepancy (workflow E) — the final link in the accountability loop
- **Context / Role**: Investigational pharmacist / CRC — at trial end / subject withdrawal / recall, remaining-drug return, destruction, and account counts must form a traceable loop.
- **Correct handling path**: ① **Return**: per protocol/contract, return unused drug, empty packaging, and remaining liquid formulations, recording batch/quantity; ② **Destruction**: destroy under authorized supervision (or return to sponsor for centralized destruction), keeping destruction records and witness; ③ **Count discrepancy**: the dispensed − returned − destroyed difference must be investigated for cause (missing record/loss/non-compliance), recorded, and reported (§6.3); ④ **Ledger**: consistent throughout with the accountability ledger (§4.2.4); ⑤ **cold chain**: temperature-deviated drug (§4.2.3) destruction must be recorded separately.
- **Key points**: Drug return and destruction are "the final link in the accountability loop" — return has records, destruction has witnesses, discrepancy has a cause.
- ⚠️ Drug return/destruction procedures and record requirements are dynamic items — follow current GCP and sponsor SOP (officially verify).

### 3.24 Special considerations for medical-device clinical trials (workflow E / B) — cannot copy the drug-RCT template
- **Context / Role**: Clinical operations / regulatory — medical-device trials (including IVD, implant, software SaMD) differ from drug trials in design, comparator, endpoints, and follow-up.
- **Correct handling path**: ① **Design**: usually controlled by "gold standard / marketed device", superiority or non-inferiority, accounting for the learning curve; ② **Endpoints**: device performance/usability/imaging/complications, often needing long-term follow-up (e.g. implant/pacemaker); ③ **blinding limits**: devices are often hard to blind (surgery/procedure), requiring bias assessment and independent endpoint adjudication (BICR/CEC); ④ **sample**: consider operator variability, site effect, and cluster randomization; ⑤ **regulation**: follow device GCP / registration pathway (linking to §8.3 filing), IVD by analytical + clinical validity verification; ⑥ **software/SaMD**: algorithm changes require version control and re-validation (§4.6 CSV).
- **Key points**: Device trials are "comparator + learning curve + long-term follow-up + bias control" — cannot copy the drug-RCT template.
- ⚠️ Medical-device trial design, comparator, and follow-up requirements are dynamic items — follow current NMPA/FDA/EMA device GCP and registration provisions (officially verify).

### 3.25 Subject medication compliance and dosing monitoring (workflow E) — prerequisite for credible efficacy data
- **Context / Role**: CRC / investigator — subject medication compliance affects the reliability of efficacy and exposure data (§1.10) and must be monitored and recorded.
- **Correct handling path**: ① **Monitoring**: count remaining tablets/packaging, electronic compliance (MEMS bottle), plasma drug concentration as corroboration; ② **Recording**: actual dosing time/missed dose/make-up dose entered into source data (§4.1); ③ **Intervention**: remind/educate low-compliance subjects, handle severe cases per protocol; ④ **endpoint link**: compliance affects PP/per-protocol set and efficacy interpretation (§5.23); ⑤ **blinding**: compliance monitoring must not unblind.
- **Key points**: Medication compliance is the "prerequisite for credible efficacy data" — objective monitoring + source record + no unblinding.
- ⚠️ Compliance-monitoring methods and record requirements are dynamic items — follow current GCP and protocol/SOP (officially verify).

### 3.26 Subject recruitment advertising and public-recruitment ethics compliance (workflow D / E) — advertising draws, not persuades
- **Context / Role**: Investigator / CRC — public recruitment ads and social-media recruitment must meet ethics review and avoid inducement/misleading.
- **Correct handling path**: ① **Review**: recruitment materials must be pre-reviewed and approved by the IRB (§3.22); ② **Content**: objective, no overstated benefit, no hidden risk, no inducement (avoid excessive compensation §3.10); ③ **Channel**: social media/platforms must be compliant, privacy-protective (§2.10), and traceable; ④ **Fairness**: ensure equitable access for vulnerable populations (§5 vulnerable); ⑤ **vs informed consent**: ads must not replace the ICF (§2.1).
- **Key points**: Recruitment ads are "ethics review + objective + non-inducing" — ads draw, not persuade; the ICF is the consent.
- ⚠️ Recruitment-ad review and public-recruitment requirements are dynamic items — follow IRB SOP and current GCP/recruitment regulations (officially verify).

### 3.27 Subject discontinuation / withdrawal and post-withdrawal follow-up (workflow E / F) — withdrawal is not loss of contact
- **Context / Role**: Investigator / medical — a subject's voluntary withdrawal, withdrawal due to AE/pregnancy (§2.12)/loss to follow-up, or sponsor discontinuation of dosing requires standardized discontinuation and follow-up arrangement (see §3.20 retention).
- **Correct handling path**: ① **Discontinuation reason**: record the withdrawal/discontinuation reason (AE, withdrawn consent, loss to follow-up, protocol violation); ② **Washout**: set the washout/follow-up period by half-life (§1.5); ③ **subject follow-up**: post-withdrawal safety follow-up (especially AE/pregnancy/lactation §5.8) must be performed per protocol and completed as far as possible; ④ **data**: already-collected data remain analyzable (§4.1); for withdrawn consent, delete data per §2.2; ⑤ **endpoint link**: affects analysis sets (§5.23) and dropout rate (§3.20).
- **Key points**: Discontinuation/withdrawal is a "reason record + washout + safety follow-up + data attribution" loop — withdrawal is not loss of contact.
- ⚠️ Discontinuation/withdrawal follow-up and data-retention requirements are dynamic items — follow current GCP and protocol/SOP (officially verify).

<!-- === merged: ref-ops-methodology-qc.md === -->
# Cross-file Dependencies, Methodology QC & Answer Template (workflow H)


## 8. Cross-file dependencies & methodology QC (workflow H)

### 8.1 Cross-file dependency checklist
| Upstream change | Must-check downstream |
|---|---|
| Study objective / endpoint | protocol, SoA, CRF, SAP, sample size, TFL, CSR |
| Inclusion / exclusion | recruitment, screening, CRF, monitoring, medical monitoring, feasibility |
| Dose / administration | IB, ICF, supply, IRT, accountability, safety monitoring, SAP |
| Safety risk | IB / RSI, protocol, ICF, safety plan, training, monitoring, DSUR / CSR |
| Visit / procedure | SoA, ICF, CRF, budget, supply, lab manual, systems |
| Randomization / blinding | IRT, drug coding, permissions, emergency unblinding, data review, SAP |
| External vendor / data source | contract, quality agreement, interface, transfer spec, verification, archiving |
| Protocol amendment | change rationale & approval, enrolled / future subjects, ethics & regulatory, version switch, training, ICF, CRF / EDC / IRT, SAP, supply |
| Data-handling rule | DMP, SAP, dataset, TFL, CSR, traceable record |

### 8.2 Pre-delivery quality gate (for H judgment)
- [ ] The decision the user must make and the delivery use are explicit;
- [ ] Jurisdiction / date / product / phase / role confirmed or flagged as assumption;
- [ ] Confirmed facts, professional inference, unknowns, dynamic requirements are separated;
- [ ] Both subject-protection and result-reliability impacts are assessed;
- [ ] Conclusion does not exceed the strength the source can support;
- [ ] Key numbers / deadlines / thresholds / versions verified against current official or project source;
- [ ] Upstream–downstream consistency protocol—SoA—CRF—SAP—TFL—CSR checked;
- [ ] Advice includes owner, trigger, record, escalation, closure evidence;
- [ ] When data is missing, false precision stopped; list what is missing / who provides / impact;
- [ ] For formal / submission-level conclusions, document, data version, approval status are locked.

### 8.3 Methodology QC output shape (workflow H deliverable) Overall judgment (acceptable / acceptable with conditions / unacceptable) → issue list (evidence / impact / priority) → remediation plan → information gap → next quality gate. May consume sibling-skill real outputs for the cross-file consistency chain (e.g. cross-check the in-house competitor-landscape brief from `ct-registry` + `ct-safety` + `ct-literature` against protocol design claims).

## 9. Minimal answer template (across B / D / E / G / H)
1. **Conclusion**: one sentence on whether a judgment is possible now; 2. **Applicable boundary**: product / phase / jurisdiction / date / assumption; 3. **Methodology judgment**: objective / risk — evidence — control — decision rule; 4. **Upstream–downstream impact**: subjects / protocol / data / safety / operations / report; 5. **Immediate action**: concrete steps by priority; 6. **Information gap**: what is missing / who provides / impact; 7. **Official verification**: official site / search terms / fields to check for dynamic requirements; 8. **Next quality gate**: what must be met to proceed.

This file's core is to keep the agent always working the closed loop "clinical question — evidence — design — execution — data — interpretation — action", without memorizing every detail.
