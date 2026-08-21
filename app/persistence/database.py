"""SQLite persistence with explicit project scoping and queryable audit history."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, name TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS requirements (
  id TEXT PRIMARY KEY, project_id TEXT NOT NULL, tenant_id TEXT NOT NULL, payload TEXT NOT NULL,
  created_at TEXT NOT NULL, FOREIGN KEY(project_id) REFERENCES projects(id)
);
CREATE TABLE IF NOT EXISTS workflows (
  id TEXT PRIMARY KEY, project_id TEXT NOT NULL, tenant_id TEXT NOT NULL, requirement_id TEXT NOT NULL,
  status TEXT NOT NULL, current_stage TEXT NOT NULL, step_count INTEGER NOT NULL DEFAULT 0,
  transition_history TEXT NOT NULL DEFAULT '[]', state_json TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
  id INTEGER PRIMARY KEY AUTOINCREMENT, workflow_id TEXT NOT NULL, stage TEXT NOT NULL,
  decision TEXT NOT NULL, approver TEXT NOT NULL, comment TEXT NOT NULL, artifact_hash TEXT NOT NULL,
  original_decision TEXT, override_decision TEXT, timestamp TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS agent_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, workflow_id TEXT NOT NULL, agent TEXT NOT NULL,
  prompt_name TEXT NOT NULL, prompt_version TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL,
  input_hash TEXT NOT NULL, output_json TEXT NOT NULL, validation_status TEXT NOT NULL,
  latency_ms INTEGER NOT NULL, input_tokens INTEGER NOT NULL, output_tokens INTEGER NOT NULL,
  estimated_cost REAL NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, workflow_id TEXT NOT NULL, actor TEXT NOT NULL,
  action TEXT NOT NULL, entity_type TEXT NOT NULL, entity_id TEXT NOT NULL,
  details TEXT NOT NULL, timestamp TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_workflows_project ON workflows(project_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_workflow ON audit_events(workflow_id, timestamp);
"""


class Database:
    def __init__(self, url: str) -> None:
        if not url.startswith("sqlite:///"):
            raise ValueError("The built-in repository supports sqlite:/// URLs")
        self.path = Path(url.removeprefix("sqlite:///")).resolve()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> int:
        with self.connect() as connection:
            cursor = connection.execute(sql, parameters)
            return cursor.lastrowid or 0

    def one(self, sql: str, parameters: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(sql, parameters).fetchone()
            return dict(row) if row else None

    def all(self, sql: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(sql, parameters).fetchall()]

    @staticmethod
    def dumps(value: Any) -> str:
        return json.dumps(value, default=str, separators=(",", ":"))
