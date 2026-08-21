"""Workflow start, checkpoint inspection, timeline, and report endpoints."""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import WorkflowCreate
from app.dependencies import Container, get_container
from app.governance.auth import Principal, current_principal
from app.governance.permissions import authorize
from app.models import AuditEvent
from app.orchestration.graph import serialise_state
from app.orchestration.state import QEWorkflowState

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("")
async def start_workflow(
    request: WorkflowCreate,
    principal: Annotated[Principal, Depends(current_principal)],
    container: Annotated[Container, Depends(get_container)],
) -> dict[str, Any]:
    authorize(principal.role, "create_workflow")
    requirement = container.requirements.get(
        request.requirement_id, request.project_id, principal.tenant_id
    )
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found in this project")
    workflow_id = "WF-" + datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    state = QEWorkflowState(
        workflow_id=workflow_id,
        project_id=request.project_id,
        tenant_id=principal.tenant_id,
        actor=principal.username,
        requirement=requirement,
        analysis=None,
        risks=[],
        tests=[],
        regression=[],
        automation=[],
        execution=[],
        triage=[],
        approval=None,
        release=None,
        status="CREATED",
        current_stage="CREATED",
        coverage_retry_count=0,
        agent_timeline=[],
    )
    try:
        completed = await container.engine.start(state)
    except Exception as exc:
        container.evidence.audit(
            AuditEvent(
                workflow_id=workflow_id,
                actor=principal.username,
                action="WORKFLOW_FAILED",
                entity_type="WORKFLOW",
                entity_id=workflow_id,
                details={"error_type": type(exc).__name__},
            )
        )
        raise HTTPException(
            status_code=422, detail=f"Workflow stopped safely: {type(exc).__name__}"
        ) from exc
    return workflow_summary(serialise_state(completed))


@router.get("/{workflow_id}")
def get_workflow(
    workflow_id: str,
    project_id: str,
    principal: Annotated[Principal, Depends(current_principal)],
    container: Annotated[Container, Depends(get_container)],
) -> dict[str, Any]:
    authorize(principal.role, "read")
    workflow = container.workflows.get(workflow_id, project_id, principal.tenant_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.get("/{workflow_id}/report")
def get_report(
    workflow_id: str,
    project_id: str,
    principal: Annotated[Principal, Depends(current_principal)],
    container: Annotated[Container, Depends(get_container)],
) -> dict[str, Any]:
    workflow = get_workflow(workflow_id, project_id, principal, container)
    state = workflow["state"]
    return {
        "workflow_id": workflow_id,
        "status": workflow["status"],
        "quality_summary": state.get("release") or state.get("coverage"),
        "agent_timeline": state.get("agent_timeline", []),
        "evidence": {
            "tests": state.get("tests", []),
            "automation": state.get("automation", []),
            "execution": state.get("execution", []),
            "triage": state.get("triage", []),
        },
    }


def workflow_summary(state: dict[str, Any]) -> dict[str, Any]:
    coverage = state.get("coverage") or {}
    requirement = state["requirement"]
    return {
        "workflow_id": state["workflow_id"],
        "status": state["status"],
        "current_stage": state["current_stage"],
        "requirement_id": requirement["id"],
        "quality_summary": {
            "coverage": coverage.get("requirement_coverage", 0),
            "critical_risk_coverage": coverage.get("critical_risk_coverage", 0),
        },
        "agent_timeline": state.get("agent_timeline", []),
    }
