"""Agent evaluation and audit evidence endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.dependencies import Container, get_container
from app.evaluation.deterministic import evaluate_dataset
from app.governance.auth import Principal, current_principal
from app.governance.permissions import authorize

router = APIRouter(tags=["evaluations"])


@router.get("/evaluations")
def evaluations(
    principal: Annotated[Principal, Depends(current_principal)],
) -> dict[str, Any]:
    authorize(principal.role, "read")
    return evaluate_dataset()


@router.get("/workflows/{workflow_id}/audit")
def audit_trail(
    workflow_id: str,
    principal: Annotated[Principal, Depends(current_principal)],
    container: Annotated[Container, Depends(get_container)],
) -> list[dict[str, Any]]:
    authorize(principal.role, "audit")
    return container.evidence.audit_trail(workflow_id)
