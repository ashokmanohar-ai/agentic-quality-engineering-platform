"""Fixed Playwright runner that parses actual machine-readable execution output."""

import asyncio
import json
from pathlib import Path
from typing import Any

from app.models import ExecutionResult
from app.tools.security import ToolCategory


class PlaywrightTool:
    category = ToolCategory.EXECUTION

    def __init__(self, project_root: Path = Path("automation/playwright")) -> None:
        self.project_root = project_root.resolve()
        self.generated_root = (self.project_root / "generated").resolve()

    async def run(self, relative_path: str) -> list[ExecutionResult]:
        test_path = (self.generated_root / relative_path).resolve()
        if not test_path.is_relative_to(self.generated_root) or not test_path.exists():
            raise PermissionError("only an existing approved generated test may run")
        process = await asyncio.create_subprocess_exec(
            "npx",
            "playwright",
            "test",
            str(Path("generated") / relative_path),
            "--reporter=json",
            cwd=self.project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180)
        except TimeoutError:
            process.kill()
            await process.wait()
            return [
                ExecutionResult(
                    test_id=relative_path,
                    status="NOT_RUN",
                    duration_ms=0,
                    retry_count=0,
                    screenshot_paths=[],
                    trace_path=None,
                    error_message="Playwright execution timed out",
                )
            ]
        try:
            report: dict[str, Any] = json.loads(stdout.decode())
        except json.JSONDecodeError:
            return [
                ExecutionResult(
                    test_id=relative_path,
                    status="NOT_RUN",
                    duration_ms=0,
                    retry_count=0,
                    screenshot_paths=[],
                    trace_path=None,
                    error_message=(stderr.decode() or "Playwright did not emit valid JSON")[:2000],
                )
            ]
        results: list[ExecutionResult] = []
        for suite in report.get("suites", []):
            for spec in suite.get("specs", []):
                for test in spec.get("tests", []):
                    runs = test.get("results", [])
                    last = runs[-1] if runs else {}
                    status_map = {"passed": "PASSED", "failed": "FAILED", "skipped": "SKIPPED"}
                    raw_status = str(last.get("status", ""))
                    attachments = last.get("attachments", [])
                    results.append(
                        ExecutionResult(
                            test_id=spec.get("title", relative_path),
                            status=status_map.get(raw_status, "NOT_RUN"),
                            duration_ms=last.get("duration", 0),
                            retry_count=max(0, len(runs) - 1),
                            screenshot_paths=[
                                a["path"]
                                for a in attachments
                                if a.get("name") == "screenshot" and a.get("path")
                            ],
                            trace_path=next(
                                (a.get("path") for a in attachments if a.get("name") == "trace"),
                                None,
                            ),
                            error_message=(last.get("error") or {}).get("message"),
                        )
                    )
        return results or [
            ExecutionResult(
                test_id=relative_path,
                status="NOT_RUN",
                duration_ms=0,
                retry_count=0,
                screenshot_paths=[],
                trace_path=None,
                error_message="No tests were discovered",
            )
        ]
