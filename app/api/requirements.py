"""Requirement ingestion endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import Container, get_container
from app.governance.auth import Principal, current_principal
from app.governance.permissions import authorize
from app.models import Requirement

router = APIRouter(prefix="/requirements", tags=["requirements"])


@router.post("")
def create_requirement(
    requirement: Requirement,
    principal: Annotated[Principal, Depends(current_principal)],
    container: Annotated[Container, Depends(get_container)],
) -> Requirement:
    authorize(principal.role, "create_workflow")
    if requirement.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    return container.requirements.create(requirement)
