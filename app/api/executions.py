"""Approved workflow execution endpoint."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import ExecuteRequest
from app.dependencies import Container, get_container
from app.governance.auth import Principal, current_principal
from app.governance.permissions import authorize
from app.orchestration.graph import serialise_state
from app.orchestration.state import restore_state

router = APIRouter(prefix="/workflows", tags=["executions"])


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    request: ExecuteRequest,
    principal: Annotated[Principal, Depends(current_principal)],
    container: Annotated[Container, Depends(get_container)],
) -> dict[str, Any]:
    authorize(principal.role, "execute")
    workflow = container.workflows.get(workflow_id, request.project_id, principal.tenant_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    state = restore_state(workflow["state"])
    approval = container.evidence.latest_approval(workflow_id, "AUTOMATION")
    if approval is None or approval.decision.value != "APPROVED":
        raise HTTPException(status_code=403, detail="Approved automation is required")
    state["approval"] = approval
    try:
        completed = await container.engine.resume(state)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {
        "workflow_id": workflow_id,
        "status": completed["status"],
        "execution": serialise_state(completed).get("execution", []),
        "release": serialise_state(completed).get("release"),
    }
