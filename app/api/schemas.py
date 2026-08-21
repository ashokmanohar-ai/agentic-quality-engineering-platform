"""HTTP request contracts."""

from pydantic import BaseModel, ConfigDict, Field

from app.models import ReleaseDecision, Role


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TokenRequest(APIModel):
    username: str
    password: str
    role: Role = Role.QUALITY_ENGINEER
    tenant_id: str = "default"


class ProjectCreate(APIModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=100)


class WorkflowCreate(APIModel):
    project_id: str
    requirement_id: str


class ApprovalCreate(APIModel):
    project_id: str
    approved: bool
    comment: str = Field(min_length=3, max_length=500)


class ExecuteRequest(APIModel):
    project_id: str


class OverrideRequest(APIModel):
    project_id: str
    override_decision: ReleaseDecision
    reason: str = Field(min_length=10, max_length=1000)
