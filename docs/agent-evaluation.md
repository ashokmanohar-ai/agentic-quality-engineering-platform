# Agent Evaluation

Evaluation is continuous product quality, not a one-time prompt review.

## Deterministic dimensions

- Pydantic schema validity and required fields
- Requirement, acceptance-criterion, risk, and source traceability
- Changed files and tool arguments against actual tool output
- Generated TypeScript compilation and policy rules
- Risk/coverage/release arithmetic
- Unsupported identifiers and project claims
- Correct routing, retries, and approval enforcement

The 36-case JSONL dataset spans requirements, risk, failures, injection, tool/file safety, tenancy, model failure, and governance. CI uses the mock provider.

## Qualitative dimensions

LLM-as-a-Judge may assess requirement understanding, test quality, risk rationale, or explanation clarity. `JudgeScore` requires a bounded score, rationale, and evidence. A judge never calculates coverage, validates IDs, or decides a mandatory gate.

## Thresholds

Default gates are 99% structured validity, 100% traceability, 98% tool correctness, and at most 2% unsupported-reference rate. Real-model benchmarks should pin model, prompt version, dataset revision, temperature, and run metadata.

Retrieval must separately measure context precision/recall, source correctness, and relevant-document retrieval before semantic retrieval is promoted.

