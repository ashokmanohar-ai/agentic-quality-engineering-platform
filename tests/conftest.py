from collections.abc import Iterator
from pathlib import Path

import pytest

from app.config import Settings
from app.persistence.database import Database
from app.persistence.repositories import EvidenceRepository, WorkflowRepository

TEST_SIGNING_KEY = "k" * 32
TEST_DEMO_PASSWORD = "p" * 12


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        automation_workspace=tmp_path / "generated",
        jwt_secret=TEST_SIGNING_KEY,
        demo_password=TEST_DEMO_PASSWORD,
    )


@pytest.fixture
def repositories(settings: Settings) -> Iterator[tuple[WorkflowRepository, EvidenceRepository]]:
    db = Database(settings.database_url)
    db.initialize()
    yield WorkflowRepository(db), EvidenceRepository(db)
