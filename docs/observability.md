# Observability

Trace boundaries are workflow, agent, model, tool, retrieval, and evaluation. Useful attributes include workflow/project IDs, agent, provider/model, prompt version, duration, status, tokens, configured pricing-based cost, tool name, and error classification.

Telemetry is disabled by default. Do not export requirement bodies, credentials, tokens, full prompts, or test data without explicit data classification and redaction policy. Use hashes and source IDs when raw content is unnecessary.

The optional Phoenix Compose profile offers a local trace target. A production exporter should use authenticated OTLP, sampling, retention, tenant isolation, and alerting for model/tool errors, loop guard events, low evaluation scores, and approval anomalies.

