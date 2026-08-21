"""Human approval and governed release-override endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import ApprovalCreate, OverrideRequest
from app.dependencies import Container, get_container
from app.governance.approval import automation_approval, release_override
from app.governance.auth import Principal, current_principal
from app.governance.permissions import authorize
from app.models import AuditEvent
from app.orchestration.graph import serialise_state
from app.orchestration.state import restore_state

router = APIRouter(prefix="/workflows", tags=["approvals"])


@router.post("/{workflow_id}/approve")
def approve_automation(
    workflow_id: str,
    request: ApprovalCreate,
    principal: Annotated[Principal, Depends(current_principal)],
    container: Annotated[Container, Depends(get_container)],
) -> dict[str, Any]:
    authorize(principal.role, "approve")
    workflow = container.workflows.get(workflow_id, request.project_id, principal.tenant_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    state = restore_state(workflow["state"])
    artifacts = state.get("automation", [])
    if not artifacts:
        raise HTTPException(status_code=409, detail="No automation artifact exists")
    approval = automation_approval(
        workflow_id,
        principal.username,
        artifacts[0].content_hash,
        request.approved,
        request.comment,
    )
    state["approval"] = approval
    state["status"] = "APPROVED" if request.approved else "REJECTED"
    state["current_stage"] = "AUTOMATION_APPROVAL"
    container.evidence.add_approval(approval)
    container.evidence.audit(
        AuditEvent(
            workflow_id=workflow_id,
            actor=principal.username,
            action="AUTOMATION_APPROVAL",
            entity_type="AUTOMATION",
            entity_id=artifacts[0].id,
            details={"decision": approval.decision.value, "artifact_hash": approval.artifact_hash},
        )
    )
    container.workflows.save(
        workflow_id,
        request.project_id,
        principal.tenant_id,
        state["requirement"].id,
        state["status"],
        state["current_stage"],
        serialise_state(state),
    )
    return approval.model_dump(mode="json")


@router.post("/{workflow_id}/override")
def override_release(
    workflow_id: str,
    request: OverrideRequest,
    principal: Annotated[Principal, Depends(current_principal)],
    container: Annotated[Container, Depends(get_container)],
) -> dict[str, Any]:
    authorize(principal.role, "approve")
    workflow = container.workflows.get(workflow_id, request.project_id, principal.tenant_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    state = restore_state(workflow["state"])
    release = state.get("release")
    if release is None:
        raise HTTPException(status_code=409, detail="No release recommendation exists")
    record = release_override(
        workflow_id,
        principal.username,
        release.final_recommendation,
        request.override_decision,
        request.reason,
    )
    release.final_recommendation = request.override_decision
    state["release"] = release
    container.evidence.add_approval(record)
    container.evidence.audit(
        AuditEvent(
            workflow_id=workflow_id,
            actor=principal.username,
            action="RELEASE_OVERRIDE",
            entity_type="RELEASE_RECOMMENDATION",
            entity_id=workflow_id,
            details={
                "original": record.original_decision,
                "override": record.override_decision,
                "reason": record.comment,
            },
        )
    )
    container.workflows.save(
        workflow_id,
        request.project_id,
        principal.tenant_id,
        state["requirement"].id,
        state["status"],
        "RELEASE_OVERRIDE",
        serialise_state(state),
    )
    return record.model_dump(mode="json")
