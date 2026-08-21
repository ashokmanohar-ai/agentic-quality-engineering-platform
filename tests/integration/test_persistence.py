from pathlib import Path

from app.models import AuditEvent
from app.persistence.database import Database
from app.persistence.repositories import EvidenceRepository, ProjectRepository, WorkflowRepository


def test_project_queries_are_tenant_scoped(tmp_path: Path) -> None:
    db = Database(f"sqlite:///{tmp_path / 'db.sqlite'}")
    db.initialize()
    projects = ProjectRepository(db)
    projects.create("A", "A", "tenant-a")
    projects.create("B", "B", "tenant-b")
    assert [item["id"] for item in projects.list("tenant-a")] == ["A"]


def test_checkpoint_and_audit_are_persisted(tmp_path: Path) -> None:
    db = Database(f"sqlite:///{tmp_path / 'db.sqlite'}")
    db.initialize()
    workflows = WorkflowRepository(db)
    evidence = EvidenceRepository(db)
    workflows.save("WF1", "P1", "T1", "R1", "RUNNING", "RISK", {"value": 1})
    evidence.audit(
        AuditEvent(
            workflow_id="WF1",
            actor="ashok",
            action="CHECK",
            entity_type="WORKFLOW",
            entity_id="WF1",
        )
    )
    assert workflows.get("WF1", "P1", "T1") is not None
    assert len(evidence.audit_trail("WF1")) == 1
