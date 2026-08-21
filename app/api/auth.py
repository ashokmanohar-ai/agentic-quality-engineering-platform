"""Local authentication route for the runnable demo."""

import secrets

from fastapi import APIRouter, HTTPException

from app.api.schemas import TokenRequest
from app.config import get_settings
from app.governance.auth import Principal, create_token
from app.models import Role

router = APIRouter(prefix="/auth", tags=["authentication"])
DEMO_ROLES = {
    "viewer": Role.VIEWER,
    "qe": Role.QUALITY_ENGINEER,
    "approver": Role.APPROVER,
    "admin": Role.ADMIN,
}


@router.post("/token")
def token(request: TokenRequest) -> dict[str, str]:
    if not secrets.compare_digest(request.password, get_settings().demo_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    assigned_role = DEMO_ROLES.get(request.username)
    if assigned_role is None or request.role != assigned_role:
        raise HTTPException(status_code=403, detail="Demo user role is fixed by username")
    principal = Principal(
        username=request.username,
        tenant_id=request.tenant_id,
        role=assigned_role,
    )
    return {"access_token": create_token(principal), "token_type": "bearer"}
