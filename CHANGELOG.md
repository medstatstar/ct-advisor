# Changelog

## 0.8.2 (2026-08-02) — security-audit remediation

- Removed the unimplemented "dual-model cross-check" claim: SKILL.md summary/description no longer state it as current behavior; it is now correctly placed on the roadmap (see README §Future Release Plans).
- Q&A logging is now OFF by default: `build_qa_store()` returns `NoOpStore` unless `config.json` sets `qa_store.mode: local` (writes `data/qa_log.jsonl`) or `remote`. No local record of questions/answers is kept by default.
- `CozeBackend._post()` now raises `NotImplementedError` (was real HTTP code behind a stub comment); `advise()` already did. The Coze path reads no token and makes no request unless explicitly implemented and enabled.
- Docs: added "§5 Data Retention & Privacy" to both READMEs; clarified the auto-load wording and the zero-outbound / zero-local-residue statement; updated the scanner-false-positive note.
- No methodology / workflow logic changes.

## 0.8.1 (2026-08-02) — README anglicization

- Anglicized the English README (`README.md`): removed all residual Chinese text (example trigger phrases, the Chinese dialogue in the language-switch demo, the `⚠️ 官方核实` marker, and the bilingual author byline) so the English page is English-only. The Chinese README (`README_zh-CN.md`) remains the Chinese counterpart.
- Aligned the README version badge to `0.8.0`.
- No logic / workflow changes.

## 0.8.0 (2026-08-02) — init version

- Initial public release of **ct-advisor**, the unified conversation entry point for the `ct-*` clinical-trial skill family.
- Methodology / design / compliance / QC / tone questions answered in-house through workflows A–J (zero outbound by default).
- Data & competitive-intel routing to `ct-registry` / `ct-safety` / `ct-literature`; sample-size handoff to `ct-samplesize`. Missing sibling skills degrade gracefully (never fabricate).
- User-friendly clarification menu (Capability / Data & intel / Clarify) with step-by-step confirmation and plain-language differences.
- Bilingual READMEs with **适用人群 / Who This Is For** and **后续发布计划 / Future Release Plans** sections.
- Every answer is cross-checked by a dual-model review to ensure correctness and reliability.
