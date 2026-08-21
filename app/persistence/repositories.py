"""Persistence repositories; every business query is tenant/project scoped."""

import json
from datetime import UTC, datetime
from typing import Any

from app.models import AgentRun, ApprovalRecord, AuditEvent, Requirement
from app.persistence.database import Database


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ProjectRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(self, project_id: str, name: str, tenant_id: str) -> dict[str, str]:
        created_at = _now()
        self.db.execute(
            "INSERT INTO projects(id, tenant_id, name, created_at) VALUES (?, ?, ?, ?)",
            (project_id, tenant_id, name, created_at),
        )
        return {"id": project_id, "tenant_id": tenant_id, "name": name, "created_at": created_at}

    def list(self, tenant_id: str) -> list[dict[str, Any]]:
        return self.db.all(
            "SELECT * FROM projects WHERE tenant_id=? ORDER BY created_at", (tenant_id,)
        )


class RequirementRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(self, requirement: Requirement) -> Requirement:
        self.db.execute(
            """INSERT INTO requirements
            (id, project_id, tenant_id, payload, created_at) VALUES (?, ?, ?, ?, ?)""",
            (
                requirement.id,
                requirement.project_id,
                requirement.tenant_id,
                requirement.model_dump_json(),
                _now(),
            ),
        )
        return requirement

    def get(self, requirement_id: str, project_id: str, tenant_id: str) -> Requirement | None:
        row = self.db.one(
            "SELECT payload FROM requirements WHERE id=? AND project_id=? AND tenant_id=?",
            (requirement_id, project_id, tenant_id),
        )
        return Requirement.model_validate_json(row["payload"]) if row else None


class WorkflowRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save(
        self,
        workflow_id: str,
        project_id: str,
        tenant_id: str,
        requirement_id: str,
        status: str,
        current_stage: str,
        state: dict[str, Any],
    ) -> None:
        existing = self.db.one(
            "SELECT step_count, transition_history FROM workflows WHERE id=?", (workflow_id,)
        )
        history = json.loads(existing["transition_history"]) if existing else []
        if history and history[-1] == current_stage:
            repeated = 1
            for stage in reversed(history[:-1]):
                if stage == current_stage:
                    repeated += 1
                else:
                    break
            if repeated >= 3:
                status = "LOOP_GUARD_TRIGGERED"
        history.append(current_stage)
        step_count = (existing["step_count"] if existing else 0) + 1
        if step_count > 25:
            status = "LOOP_GUARD_TRIGGERED"
        values = (
            workflow_id,
            project_id,
            tenant_id,
            requirement_id,
            status,
            current_stage,
            step_count,
            self.db.dumps(history),
            self.db.dumps(state),
            _now(),
        )
        self.db.execute(
            """INSERT INTO workflows
            (id, project_id, tenant_id, requirement_id, status, current_stage, step_count,
             transition_history, state_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET status=excluded.status,
              current_stage=excluded.current_stage, step_count=excluded.step_count,
              transition_history=excluded.transition_history, state_json=excluded.state_json,
              updated_at=excluded.updated_at""",
            values,
        )

    def get(self, workflow_id: str, project_id: str, tenant_id: str) -> dict[str, Any] | None:
        row = self.db.one(
            "SELECT * FROM workflows WHERE id=? AND project_id=? AND tenant_id=?",
            (workflow_id, project_id, tenant_id),
        )
        if row:
            row["state"] = json.loads(row.pop("state_json"))
            row["transition_history"] = json.loads(row["transition_history"])
        return row

    def list(self, project_id: str, tenant_id: str) -> list[dict[str, Any]]:
        rows = self.db.all(
            "SELECT * FROM workflows WHERE project_id=? AND tenant_id=? ORDER BY updated_at DESC",
            (project_id, tenant_id),
        )
        for row in rows:
            row.pop("state_json", None)
            row["transition_history"] = json.loads(row["transition_history"])
        return rows


class EvidenceRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add_agent_run(self, run: AgentRun) -> None:
        data = run.model_dump(mode="json")
        self.db.execute(
            """INSERT INTO agent_runs(workflow_id,agent,prompt_name,prompt_version,provider,model,
            input_hash,output_json,validation_status,latency_ms,input_tokens,output_tokens,
            estimated_cost,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data["workflow_id"],
                data["agent"],
                data["prompt_name"],
                data["prompt_version"],
                data["provider"],
                data["model"],
                data["input_hash"],
                self.db.dumps(data["output_json"]),
                data["validation_status"],
                data["latency_ms"],
                data["input_tokens"],
                data["output_tokens"],
                data["estimated_cost"],
                str(data["created_at"]),
            ),
        )

    def add_approval(self, approval: ApprovalRecord) -> None:
        data = approval.model_dump(mode="json")
        self.db.execute(
            """INSERT INTO approvals(workflow_id,stage,decision,approver,comment,artifact_hash,
            original_decision,override_decision,timestamp) VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                data["workflow_id"],
                data["stage"],
                data["decision"],
                data["approver"],
                data["comment"],
                data["artifact_hash"],
                data["original_decision"],
                data["override_decision"],
                str(data["timestamp"]),
            ),
        )

    def latest_approval(self, workflow_id: str, stage: str) -> ApprovalRecord | None:
        row = self.db.one(
            "SELECT * FROM approvals WHERE workflow_id=? AND stage=? ORDER BY id DESC LIMIT 1",
            (workflow_id, stage),
        )
        if not row:
            return None
        row.pop("id")
        return ApprovalRecord.model_validate(row)

    def audit(self, event: AuditEvent) -> None:
        data = event.model_dump(mode="json")
        self.db.execute(
            """INSERT INTO audit_events
            (workflow_id,actor,action,entity_type,entity_id,details,timestamp)
            VALUES (?,?,?,?,?,?,?)""",
            (
                data["workflow_id"],
                data["actor"],
                data["action"],
                data["entity_type"],
                data["entity_id"],
                self.db.dumps(data["details"]),
                str(data["timestamp"]),
            ),
        )

    def audit_trail(self, workflow_id: str) -> list[dict[str, Any]]:
        rows = self.db.all(
            "SELECT * FROM audit_events WHERE workflow_id=? ORDER BY timestamp", (workflow_id,)
        )
        for row in rows:
            row["details"] = json.loads(row["details"])
        return rows
