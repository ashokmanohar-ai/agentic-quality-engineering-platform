# Interview Walkthrough

## Two-minute explanation

This platform demonstrates how Agentic AI can be safely introduced into Quality Engineering using specialised agents, deterministic gates, tool controls, structured outputs, human approvals, Playwright automation, observability, and continuous AI evaluation. I use LangGraph to make state and decisions explicit. The mock provider lets every control run in CI with no paid API. Agents propose analysis and context; code calculates risk, coverage, and release gates. Generated TypeScript is constrained, validated, hash-approved, then executed, and failure evidence is triaged before an auditable recommendation.

## Five-minute walkthrough

1. Submit the password-reset or payment-retry requirement.
2. Show deterministic requirement checks and structured agent analysis.
3. Show probability/impact inputs and code-calculated risk level.
4. Open traceable test cases and deterministic coverage findings.
5. Explain git-diff-grounded regression selection.
6. Inspect generated Playwright and policy validation.
7. Show the durable `AWAITING_APPROVAL` checkpoint and artifact hash.
8. Approve, execute the real Playwright test, and inspect screenshot/trace/error evidence.
9. Show confidence-controlled triage and deterministic release gate.
10. Finish with prompt version, token/latency, audit timeline, and the 36-case evaluation gate.

## Architect questions

**Why multiple agents?** Narrow contracts make responsibility, tool privilege, evaluation, and failure containment explicit. Agent count is not the goal.

**Why LangGraph?** It exposes state, conditional routing, bounded retries, checkpoints, and human interruption instead of hiding orchestration in conversation.

**Agent versus workflow?** Agents propose within a narrow semantic task; the workflow owns policy and transitions.

**Why structured outputs?** They allow schema validation, traceability checks, persistence, stable APIs, and safe failure.

**How are hallucinations controlled?** Tool output is authoritative, source IDs are required, unknown identifiers are evaluated, deterministic checks validate references, and unsupported output fails gates.

**How do you test nondeterminism?** Pin prompts/config/data, use low temperature and repeated real-model benchmarks, separate deterministic from qualitative metrics, and monitor distributions rather than one sample.

**How is generated code safe?** Dedicated directory, path resolution, static restrictions, formatting/lint/typecheck/discovery, human hash approval, and a fixed execution command.

**How do release decisions work?** Mandatory code gates decide PASS/CONDITIONAL_PASS/FAIL; the model supplies narrative and cannot override them.

**How would this scale?** Replace SQLite via the repository boundary, run workers and Playwright in isolated jobs, use durable LangGraph persistence/queues, OIDC, managed secrets, OTLP, per-tenant quotas, and measured retrieval.

**How would Jira/Azure DevOps/GitHub integrate?** Add read-only, typed ingestion tools that preserve external IDs and provenance; writes remain separately permissioned and human-approved.

