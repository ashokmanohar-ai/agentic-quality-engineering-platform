# Orchestration

LangGraph makes transitions and state explicit.

```mermaid
flowchart TD
    S["Start"] --> RA["Requirement analysis"]
    RA --> RK["Risk analysis"]
    RK --> TD["Test design"]
    TD --> CR["Coverage review"]
    CR --> CG{"Coverage gate"}
    CG -->|retry within limit| TD
    CG -->|pass| RS["Regression + automation"]
    CG -->|limit reached| X["Human escalation"]
    RS --> VA["Validate artifact"]
    VA --> HA{"Human approval"}
    HA -->|approved| EX["Execute + triage"]
    HA -->|rejected| X
    EX --> QR["Quality review"]
```

The planning graph stops in `AWAITING_APPROVAL`; this is a durable pause, not a blocking in-memory wait. The resume graph verifies a persisted approval and matching hash before execution. Every stage updates the timeline and audit trail. Maximum graph steps and repeated transitions prevent infinite loops.

Errors are reported as model, tool, validation, policy, execution, or environment failures. Unavailable models and Playwright produce explicit unavailable/not-run outcomes; they never become synthetic success.

