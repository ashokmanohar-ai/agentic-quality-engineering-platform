"""Deterministic git diff extraction; no model-provided command is accepted."""

import shutil
import subprocess
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from app.tools.security import ToolCategory


class GitDiff(BaseModel):
    model_config = ConfigDict(extra="forbid")
    changed_files: list[str]
    added_files: list[str]
    deleted_files: list[str]
    changed_modules: list[str]


class GitDiffTool:
    category = ToolCategory.READ_ONLY

    def __init__(self, repository: Path) -> None:
        self.repository = repository.resolve()

    def inspect(self, base: str = "HEAD~1", head: str = "HEAD") -> GitDiff:
        if not base.replace("/", "").replace("-", "").replace("_", "").replace("~", "").isalnum():
            raise ValueError("invalid base ref")
        if not head.replace("/", "").replace("-", "").replace("_", "").isalnum():
            raise ValueError("invalid head ref")
        git = shutil.which("git")
        if git is None:
            raise RuntimeError("git is unavailable")
        process = subprocess.run(  # noqa: S603
            [git, "diff", "--name-status", base, head],
            cwd=self.repository,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if process.returncode != 0:
            return GitDiff(changed_files=[], added_files=[], deleted_files=[], changed_modules=[])
        changed: list[str] = []
        added: list[str] = []
        deleted: list[str] = []
        for line in process.stdout.splitlines():
            status, _, path = line.partition("\t")
            if not path:
                continue
            changed.append(path)
            if status.startswith("A"):
                added.append(path)
            if status.startswith("D"):
                deleted.append(path)
        modules = sorted({Path(path).parts[0] for path in changed if Path(path).parts})
        return GitDiff(
            changed_files=changed,
            added_files=added,
            deleted_files=deleted,
            changed_modules=modules,
        )
