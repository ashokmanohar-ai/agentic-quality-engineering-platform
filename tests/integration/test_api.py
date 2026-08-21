from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.config import get_settings
from app.dependencies import get_container
from app.main import app

TEST_SIGNING_KEY = "k" * 32
TEST_DEMO_PASSWORD = "p" * 12


def test_health_and_protected_api(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("JWT_SECRET", TEST_SIGNING_KEY)
    monkeypatch.setenv("DEMO_PASSWORD", TEST_DEMO_PASSWORD)
    monkeypatch.setenv("AUTOMATION_WORKSPACE", str(tmp_path / "generated"))
    get_settings.cache_clear()
    get_container.cache_clear()
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "healthy"
        assert client.get("/api/v1/projects").status_code == 401
        token_response = client.post(
            "/api/v1/auth/token",
            json={
                "username": "qe",
                "password": TEST_DEMO_PASSWORD,
                "role": "QUALITY_ENGINEER",
                "tenant_id": "default",
            },
        )
        assert token_response.status_code == 200
        escalated = client.post(
            "/api/v1/auth/token",
            json={
                "username": "qe",
                "password": TEST_DEMO_PASSWORD,
                "role": "ADMIN",
                "tenant_id": "default",
            },
        )
        assert escalated.status_code == 403
        headers = {"Authorization": f"Bearer {token_response.json()['access_token']}"}
        created = client.post(
            "/api/v1/projects", json={"id": "demo", "name": "Demo"}, headers=headers
        )
        assert created.status_code == 200
        assert client.get("/api/v1/projects", headers=headers).json()[0]["id"] == "demo"
        requirement = {
            "id": "REQ-001",
            "project_id": "demo",
            "tenant_id": "default",
            "title": "Password Reset",
            "user_story": "As a registered user I can safely reset my forgotten password",
            "acceptance_criteria": ["Token expires", "New login succeeds"],
            "critical": True,
            "source_ids": ["REQ-001"],
        }
        assert (
            client.post("/api/v1/requirements", json=requirement, headers=headers).status_code
            == 200
        )
        started = client.post(
            "/api/v1/workflows",
            json={"project_id": "demo", "requirement_id": "REQ-001"},
            headers=headers,
        )
        assert started.status_code == 200
        assert started.json()["status"] == "AWAITING_APPROVAL"
        workflow_id = started.json()["workflow_id"]
        denied = client.post(
            f"/api/v1/workflows/{workflow_id}/approve",
            json={"project_id": "demo", "approved": True, "comment": "reviewed"},
            headers=headers,
        )
        assert denied.status_code == 403
    get_settings.cache_clear()
    get_container.cache_clear()
