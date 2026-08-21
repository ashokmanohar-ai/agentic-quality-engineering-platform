"""Project endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.api.schemas import ProjectCreate
from app.dependencies import Container, get_container
from app.governance.auth import Principal, current_principal
from app.governance.permissions import authorize
from app.persistence.repositories import ProjectRepository

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("")
def create_project(
    request: ProjectCreate,
    principal: Annotated[Principal, Depends(current_principal)],
    container: Annotated[Container, Depends(get_container)],
) -> dict[str, str]:
    authorize(principal.role, "create_workflow")
    return ProjectRepository(container.db).create(request.id, request.name, principal.tenant_id)


@router.get("")
def list_projects(
    principal: Annotated[Principal, Depends(current_principal)],
    container: Annotated[Container, Depends(get_container)],
) -> list[dict[str, Any]]:
    authorize(principal.role, "read")
    return ProjectRepository(container.db).list(principal.tenant_id)
