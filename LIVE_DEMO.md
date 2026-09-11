# Live AgentOps Studio

**Live demo:** https://agentops-studio-ten.vercel.app  
**Portfolio case study:** https://ashok-kumar-manohar-portfolio.vercel.app/case-studies/agentops-studio

## What the live demo proves

The public demo executes a deterministic multi-agent state machine and generates a fresh trace on every run:

```text
Goal → Planner → specialist agents → MCP policy → tools → reviewer → evaluation → release
```

Recruiters can inspect the MCP registry, permission classes, approval/block policy, generated execution trace and evidence-based release decision.

## What this repository adds

This repository is the deeper implementation proof: explicit LangGraph state, nine specialised QE agents, Pydantic contracts, persisted checkpoints, RBAC/tenant scope, deterministic quality gates, hash-bound human approval, governed Playwright execution, audit events, observability and CI.

## 3-minute recruiter route

1. Open the live demo and inspect **MCP Registry**.
2. Run **Agent Workflow** and inspect the newly generated trace.
3. Return here and inspect `app/`, `automation/playwright/`, `config/`, `tests/` and `.github/workflows/`.
4. Review the architecture, human-in-the-loop and security documentation.

## Integrity statement

The Vercel workflow is a keyless deterministic state-machine demonstration. It demonstrates orchestration and governance concepts; it is not production agent telemetry. The repository provides the stronger engineering evidence for state, roles, approvals, execution boundaries and auditability.
