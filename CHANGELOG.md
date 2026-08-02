# Changelog

## 0.8.0 (2026-08-02) — init version

- Initial public release of **ct-advisor**, the unified conversation entry point for the `ct-*` clinical-trial skill family.
- Methodology / design / compliance / QC / tone questions answered in-house through workflows A–J (zero outbound by default).
- Data & competitive-intel routing to `ct-registry` / `ct-safety` / `ct-literature`; sample-size handoff to `ct-samplesize`. Missing sibling skills degrade gracefully (never fabricate).
- User-friendly clarification menu (Capability / Data & intel / Clarify) with step-by-step confirmation and plain-language differences.
- Bilingual READMEs with **适用人群 / Who This Is For** and **后续发布计划 / Future Release Plans** sections.
- Every answer is cross-checked by a dual-model review to ensure correctness and reliability.
