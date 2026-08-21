"""Seed the two interview demonstration requirements."""

import json
import sqlite3
from pathlib import Path

from app.config import get_settings
from app.models import Requirement
from app.persistence.database import Database
from app.persistence.repositories import ProjectRepository, RequirementRepository


def main() -> None:
    settings = get_settings()
    db = Database(settings.database_url)
    db.initialize()
    projects = ProjectRepository(db)
    requirements = RequirementRepository(db)
    try:
        projects.create("demo", "Agentic QE Demonstration", "default")
    except sqlite3.IntegrityError:
        print("Demo project already present")
    for path in sorted(Path("datasets/requirements").glob("*.json")):
        requirement = Requirement.model_validate(json.loads(path.read_text(encoding="utf-8")))
        try:
            requirements.create(requirement)
            print(f"Seeded {requirement.id}")
        except sqlite3.IntegrityError:
            print(f"Already present: {requirement.id}")
    print("Demo data ready. Open http://localhost:8080/docs")


if __name__ == "__main__":
    main()
