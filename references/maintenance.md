# Maintenance Notes

> 从 SKILL.md 移出（2026-11-15）：回归测试 / Bug 上报 / 带日期变更说明等维护类内容，不应留在 SKILL.md，归档于此。

**2026-10-26 · ct-base §22.24 dual-track governance framework**: as the ct-series single entry point routing to ct-samplesize/ct-registry/ct-safety/ct-literature/ct-protocol, any classification judgement involving AI-as-intervention (prospective evaluation + SPIRIT-AI/CONSORT-AI) vs AI-for-trial-operations (workflow accuracy + TRIPOD-AI/ICH E6(R3)) follows the §22.24 dual-track governance framework (EClinicalMedicine 2026-10).


## permissions (original verbose block, archived 2026-11-15)

permissions:
  scope: "user-space-only"
  network: "controlled-coze-opt-in"
  network_note: "All questions are forwarded to Coze (single call, internal `scripts/orchestrate.py`). Local side performs NO knowledge base lookup, NO local network retrieval, NO web search. Attachments under 5 MB are uploaded as original bytes to Coze `/upload_file` and shipped as the top-level `doc_context` field (Coze decodes natively); attachments over 5 MB are converted to Markdown locally via `scripts/office_to_md.py` (stdlib-only) and the resulting .md is uploaded through the SAME doc_context channel. The Coze-side knowledge base is the single source of truth."
  filesystem: "Read-only to own files; no confidential data leaves locally — Coze payloads sanitized, query_origin is a stable per-machine sha256 hash (non-PII)."
