# Human in the Loop

Human approval is mandatory for generated automation execution. The approval records approver, time, decision, comment, and exact content hash. Editing the artifact invalidates that approval.

A release override is a separate governed action. The record preserves the original deterministic/AI recommendation, override, reason, approver, and timestamp. The platform never silently replaces history.

`APPROVER` or `ADMIN` can approve and view audit evidence. `QUALITY_ENGINEER` can create and execute an already approved workflow. `VIEWER` is read-only. Production should map these roles from an OIDC identity provider and enforce separation-of-duties policy where required.

