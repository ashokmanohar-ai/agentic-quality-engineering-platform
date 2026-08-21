from pathlib import Path

import pytest

from app.config import Settings
from app.governance.approval import automation_approval
from app.llm.mock_provider import MockProvider
from app.models import Requirement
from app.orchestration.graph import WorkflowEngine
from app.orchestration.state import QEWorkflowState
from app.persistence.database import Database
from app.persistence.repositories import EvidenceRepository, WorkflowRepository

TEST_SIGNING_KEY = "k" * 32
TEST_DEMO_PASSWORD = "p" * 12


def initial_state() -> QEWorkflowState:
    requirement = Requirement(
        id="REQ-001",
        project_id="demo",
        title="Password reset",
        user_story="As a registered customer I can safely reset my forgotten password",
        acceptance_criteria=["Token expires", "Password changes", "New login succeeds"],
        critical=True,
    )
    return QEWorkflowState(
        workflow_id="WF-1",
        project_id="demo",
        tenant_id="default",
        actor="qe",
        requirement=requirement,
        risks=[],
        tests=[],
        regression=[],
        automation=[],
        execution=[],
        triage=[],
        status="CREATED",
        current_stage="CREATED",
        coverage_retry_count=0,
        agent_timeline=[],
    )


@pytest.mark.asyncio
async def test_workflow_pauses_at_human_approval(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'db.sqlite'}",
        automation_workspace=tmp_path / "generated",
        jwt_secret=TEST_SIGNING_KEY,
        demo_password=TEST_DEMO_PASSWORD,
    )
    db = Database(settings.database_url)
    db.initialize()
    engine = WorkflowEngine(
        settings, MockProvider(), WorkflowRepository(db), EvidenceRepository(db)
    )
    completed = await engine.start(initial_state())
    assert completed["status"] == "AWAITING_APPROVAL"
    assert completed["current_stage"] == "AUTOMATION_REVIEW"
    assert completed["automation"][0].validation_status == "VALID"
    assert (tmp_path / "generated" / completed["automation"][0].relative_path).exists()


@pytest.mark.asyncio
async def test_resume_without_approval_is_blocked(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'db.sqlite'}",
        automation_workspace=tmp_path / "generated",
        jwt_secret=TEST_SIGNING_KEY,
        demo_password=TEST_DEMO_PASSWORD,
    )
    db = Database(settings.database_url)
    db.initialize()
    engine = WorkflowEngine(
        settings, MockProvider(), WorkflowRepository(db), EvidenceRepository(db)
    )
    completed = await engine.start(initial_state())
    with pytest.raises(PermissionError, match="approval"):
        await engine.resume(completed)


def test_approval_is_bound_to_artifact_hash() -> None:
    record = automation_approval("WF-1", "approver", "abc123", True, "Reviewed the generated code")
    assert record.artifact_hash == "abc123"
    assert record.decision.value == "APPROVED"
