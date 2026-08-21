"""Safe generated-artifact writer and static policy validator."""

import re
from pathlib import Path

from app.models import AutomationArtifact
from app.tools.security import ToolCategory

FORBIDDEN_PATTERNS: dict[str, str] = {
    "arbitrary sleep": r"waitForTimeout\s*\(",
    "brittle XPath": r"locator\s*\(\s*['\"]//",
    "hard-coded password": r"password\s*[:=]\s*['\"][^$<{]",
    "focused test": r"test\.only\s*\(",
    "skipped test": r"test\.skip\s*\(",
    "shell execution": r"child_process|execSync|spawnSync",
}


class AutomationWorkspace:
    category = ToolCategory.WRITE

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative_path: str) -> Path:
        if not relative_path.endswith(".spec.ts"):
            raise ValueError("generated automation must use .spec.ts")
        destination = (self.root / relative_path).resolve()
        if not destination.is_relative_to(self.root):
            raise PermissionError("path traversal blocked")
        return destination

    def static_validate(self, artifact: AutomationArtifact) -> list[str]:
        errors = [
            name
            for name, pattern in FORBIDDEN_PATTERNS.items()
            if re.search(pattern, artifact.code)
        ]
        if "@playwright/test" not in artifact.code:
            errors.append("missing Playwright import")
        if "expect(" not in artifact.code:
            errors.append("missing assertion")
        self.resolve(artifact.relative_path)
        return errors

    def write_validated(self, artifact: AutomationArtifact) -> Path:
        errors = self.static_validate(artifact)
        if errors:
            artifact.validation_status = "INVALID"
            artifact.validation_errors = errors
            raise ValueError("; ".join(errors))
        destination = self.resolve(artifact.relative_path)
        destination.write_text(artifact.code, encoding="utf-8")
        artifact.validation_status = "VALID"
        artifact.validation_errors = []
        return destination
