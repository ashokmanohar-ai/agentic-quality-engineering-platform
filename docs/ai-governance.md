# AI Governance

- **Traceability:** tests and decisions cite requirement, criterion, risk, diff, execution, or knowledge source IDs.
- **Auditability:** prompt/model/tool/validation/approval/release metadata is persisted.
- **Prompt versioning:** prompts live in `prompts/<agent>/vN.md`; every run records version.
- **Human oversight:** automation and release overrides require authorised, attributable action.
- **Model configuration:** vendor access is adapter-based; deterministic mock mode remains available.
- **Evaluation:** versioned datasets and gates detect regressions and unsupported claims.
- **Security:** untrusted-content boundaries, least-privilege tools, path/command allow-lists, secret masking.
- **Data handling:** project scope, minimal telemetry, environment secrets, and explicit retention design.
- **Failure escalation:** model/tool failure, low confidence, repeated routing, and policy violations stop safely.

These controls are engineering practices, not a claim of legal, regulatory, or standards certification.

