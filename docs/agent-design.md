# Agent Design

| Agent | Inputs | Structured output | Allowed tools | Disallowed actions | Primary metrics | Failure handling |
|---|---|---|---|---|---|---|
| Requirement Analyst | Story, criteria, knowledge | `RequirementAnalysis` | Knowledge read | Invent facts, execute | Completeness, unsupported claims | Expose ambiguity |
| Risk Analyst | Requirement, analysis | `RiskItem` | Knowledge read | Calculate gate, invent API | Critical-risk recall | Preserve evidence |
| Test Designer | Requirement, risks | `TestCase` | Existing-test read | Orphan cases, run test | Traceability, coverage | Schema rejection |
| Coverage Reviewer | IDs and tests | `CoverageReport` | None | Estimate percentages | Critical coverage | Deterministic fail |
| Regression Selector | Diff, links, history | `RegressionRecommendation` | Git diff read | Invent changed file | Precision, tool correctness | Advisory confidence |
| Automation Generator | Approved candidate and rules | `AutomationArtifact` | Framework read | Write/run/approve | Compile/policy rate | Validate before write |
| Execution Agent | Valid artifact and approval | `ExecutionResult` | Fixed Playwright | Fabricate/alter code | Result fidelity | `NOT_RUN` on no evidence |
| Failure Triage | Actual run evidence | `FailureAnalysis` | Results/trace read | Treat hypothesis as fact | Accuracy, calibration | `UNKNOWN` + review |
| Quality Reviewer | Coverage, runs, triage | `ReleaseRecommendation` | Report read | Override gate | Gate fidelity | Deterministic decision wins |

Narrow responsibilities reduce tool privileges and make evaluation meaningful. An “agent” is the model-backed proposal component; the workflow owns control flow, retries, approvals, and policy.

