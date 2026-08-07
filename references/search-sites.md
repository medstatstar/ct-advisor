---
file: search-sites.md
version: 2026-08-06
purpose: External search-site routing table — when knowledge/ and Coze both fail to provide sufficient basis, guide the user by workflow to authoritative sites to consult on their own
---

# External Search Sites by Workflow

> **Trigger**: when the agent finds no hit in `knowledge/` and still lacks sufficient basis after Coze refinement, output the corresponding category's site list so the user can consult it themselves.
> **Usage**: output only the site name + URL, never retrieve on the user's behalf. Format: `suggested reading: [site name](URL)`.

---

## Workflow A — Explain & Locate Evidence

**category tags**: `explain` / `methodology`

| Site | URL | When to use |
|---|---|---|
| ICH | https://ich.org | ICH guideline index (E6/E8/E9/E10/E11/E17 etc.): https://ich.org/page/search-index-ich-guidelines |
| NMPA (国家药监局, National Medical Products Administration) | https://www.nmpa.gov.cn | China regulations, norms, announcements, drug labels |
| CDE (药品审评中心, Center for Drug Evaluation) | https://www.cde.org.cn | technical guidance principles, clinical-trial implicit许可 (silent approval), review info |
| FDA | https://www.fda.gov | FDA Guidance Documents, Drugs@FDA, CBER/CDER guidance |
| EMA | https://www.ema.europa.eu | EU scientific guidelines, EPARs, CHMP opinions |
| WHO | https://www.who.int | WHO guidelines, technical reports, essential medicines list |
| PubMed | https://pubmed.ncbi.nlm.nih.gov | biomedical literature search |
| Europe PMC | https://europepmc.org | European biomedical literature, with full-text links |

---

## Workflow B — Trial Design

**category tag**: `design`

| Site | URL | When to use |
|---|---|---|
| ICH | https://ich.org | E8(R1) general considerations for clinical trials, E10 control selection |
| NMPA | https://www.nmpa.gov.cn | clinical development guidance principled on clinical value |
| CDE | https://www.cde.org.cn | single-arm, adaptive, basket design guidance |
| FDA | https://www.fda.gov | adaptive design, enrichment design, master protocol guidance |
| EMA | https://www.ema.europa.eu | methodological guidance, populations, endpoints, statistical considerations |
| ClinicalTrials.gov | https://clinicaltrials.gov | search registered-trial design info (control, endpoint, inclusion/exclusion) |
| 中国临床试验注册中心 (ChiCTR) | https://www.chictr.org.cn | trials registered by Chinese investigators |
| 药物临床试验登记 (China Drug Trials) | https://www.chinadrugtrials.org.cn | China IND/BLA trial registration & disclosure |
| WHO ICTRP | https://www.who.int/clinical-trials-registry-platform | global trial registry aggregate search |

---

## Workflow C — Statistics & Estimands

**category tag**: `statistics`

| Site | URL | When to use |
|---|---|---|
| ICH | https://ich.org | E9(R1) estimands, E10 control selection |
| NMPA | https://www.nmpa.gov.cn | drug clinical-trial statistical guidance principle |
| CDE | https://www.cde.org.cn | non-inferiority/equivalence/superiority design, interim analysis, multiplicity, missing data guidance |
| FDA | https://www.fda.gov | non-inferiority trials, adaptive design, multiplicity, missing-data guidance |
| EMA | https://www.ema.europa.eu | statistical methodology, sensitivity analysis, missing-data handling |
| PubMed | https://pubmed.ncbi.nlm.nih.gov | statistical-methodology literature (e.g. estimand framework, Bayesian design) |
| Semantic Scholar | https://www.semanticscholar.org | AI academic search, with citation counts and methodology papers |
| Cochrane Library | https://www.cochranelibrary.com | systematic-review and meta-analysis methodology reference |

---

## Workflow D — GCP & Quality

**category tags**: `regulatory` / `compliance`

| Site | URL | When to use |
|---|---|---|
| NMPA | https://www.nmpa.gov.cn | GCP (2020 edition), drug clinical-trial institution management, drug registration management |
| CDE | https://www.cde.org.cn | safety info reporting during trials, communication meetings |
| FDA | https://www.fda.gov | GCP guidance, Inspection Guides, BIMO |
| EMA | https://www.ema.europa.eu | GCP inspection, clinical-trial management, EudraVigilance |
| ICH | https://ich.org | E6(R2)/E6(R3) full GCP text, E2E Pharmacovigilance |
| WHO | https://www.who.int | WHO GCP guidance, good pharmacy practice |
| CIOMS | https://cioms.ch | CIOMS reports (ethics, safety reporting, signal detection) |

---

## Workflow E — Clinical Operations

**category tag**: `operations`

| Site | URL | When to use |
|---|---|---|
| NMPA | https://www.nmpa.gov.cn | clinical-trial institution filing, drug clinical-trial registration & disclosure |
| CDE | https://www.cde.org.cn | clinical-trial info management, implicit许可, supplementary materials |
| FDA | https://www.fda.gov | IND/IDE management, clinical-trial practice |
| EMA | https://www.ema.europa.eu | CTIS (Clinical Trials Information System), EudraVigilance |
| WHO ICTRP | https://www.who.int/clinical-trials-registry-platform | WHO primary-registry data sources |

---

## Workflow F — Safety & DSUR

**category tag**: `safety`

| Site | URL | When to use |
|---|---|---|
| NMPA | https://www.nmpa.gov.cn | adverse-reaction bulletins, pharmacovigilance, risk control |
| CDE | https://www.cde.org.cn | rapid safety-data reporting during trials, SUSAR/RSI/DSUR requirements |
| FDA FAERS | https://www.fda.gov/drugs/questions-and-answers-fdas-adverse-event-reporting-system-faers | public adverse-event database |
| FDA Sentinel | https://www.fda.gov/safety/fdas-sentinel-initiative | post-market active surveillance |
| EMA EudraVigilance | https://www.adrreports.eu | EU adverse-event database |
| WHO-UMC VigiBase | https://www.who-umc.org | global individual case safety report database |
| VigiAccess | https://www.vigaccess.org | WHO-UMC public safety-data search |
| LareB (BfArM, Germany) | https://www.lareb.nl | Netherlands pharmacovigilance center (supplementary signal data) |
| 国家药品不良反应监测 (National ADR Monitoring) | https://www.adr.org.cn | China adverse-reaction monitoring & bulletins |

---

## Workflow G — Documents & Reports

**category tag**: `regulatory`

| Site | URL | When to use |
|---|---|---|
| ICH | https://ich.org | E3 clinical study report structure |
| NMPA | https://www.nmpa.gov.cn | CTD format requirements, clinical-trial report norms |
| CDE | https://www.cde.org.cn | clinical-trial summary report writing requirements |
| FDA | https://www.fda.gov | eCTD, Medical Review, Statistical Review templates |
| EMA | https://www.ema.europa.eu | CSR writing norms, modular report requirements |

---

## Workflow H — Methodology QC

**category tag**: `qc`

> The search sites match the workflow under review (e.g. QC target is a safety document → use Workflow F's site list).

---

## Cross-Category Resources

**Drug Information**

| Site | URL | Notes |
|---|---|---|
| PubChem | https://pubchem.ncbi.nlm.nih.gov | compound structure, activity, safety data |
| ChEMBL | https://www.ebi.ac.uk/chembl | drug targets, ADME, bioactivity data |
| DrugBank | https://go.drugbank.com | approved / investigational drug info |
| Micromedex | https://www.micromedexsolutions.com | evidence-based drug info (institutional subscription) |
| DailyMed | https://dailymed.nlm.nih.gov | FDA-approved drug labels |
| 中国药品注册 (China drug registration) | https://www.nmpa.gov.cn/datasearch | domestic / imported drug database |
| 中国药典 (Chinese Pharmacopoeia) | https://www.chp.org.cn | national drug standards (2025 edition) |

**Trial Registries**

| Site | URL | Notes |
|---|---|---|
| ClinicalTrials.gov | https://clinicaltrials.gov | US-led global trial registry |
| 药物临床试验登记 (China Drug Trials) | https://www.chinadrugtrials.org.cn | China IND/BLA mandatory registration |
| 中国临床试验注册中心 (ChiCTR) | https://www.chictr.org.cn | WHO primary registry |
| EU Clinical Trials Register | https://www.clinicaltrialsregister.eu | EU CTR, EU-region trials |
| WHO ICTRP | https://www.who.int/clinical-trials-registry-platform | global trial-registry aggregate entry |
| ISRCTN | https://www.isrctn.com | international registry operated by Springer Nature |
| DRKS | https://www.drks.de | German clinical-trial registry |
| jRCT | https://jrct.mhlw.go.jp | Japan clinical-trial registry |

**Literature**

| Site | URL | Notes |
|---|---|---|
| PubMed | https://pubmed.ncbi.nlm.nih.gov | US NLM biomedical literature |
| Europe PMC | https://europepmc.org | EMBL-EBI biomedical literature |
| Cochrane Library | https://www.cochranelibrary.com | systematic-review methodology |
| Semantic Scholar | https://www.semanticscholar.org | AI academic search engine |
| 中国知网 (CNKI) | https://www.cnki.net | Chinese academic literature |

---

## Output template

When `knowledge/` and Coze both fail to provide sufficient basis, output in this format:

```
> ⚠️ Local knowledge base and Coze refinement both found no sufficient basis; suggested authoritative sources:
> - [site name](URL) — brief note on what to look up
```

**Forbidden**:
- ❌ retrieving sites on the user's behalf (not the agent's data-pull responsibility)
- ❌ fabricating specific content from the sites
- ❌ outputting sites unrelated to the question
