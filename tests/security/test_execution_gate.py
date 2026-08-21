from hashlib import sha256

import pytest

from app.agents.execution_agent import ExecutionAgent
from app.models import ApprovalDecision, ApprovalRecord, AutomationArtifact, ExecutionResult


class FakePlaywrightTool:
    async def run(self, relative_path: str) -> list[ExecutionResult]:
        return [
            ExecutionResult(
                test_id=relative_path,
                status="PASSED",
                duration_ms=10,
                retry_count=0,
                screenshot_paths=[],
                trace_path=None,
                error_message=None,
            )
        ]


def valid_artifact() -> AutomationArtifact:
    code = "import { test, expect } from '@playwright/test'; expect(true).toBe(true);"
    return AutomationArtifact(
        id="A1",
        test_case_id="TC1",
        relative_path="tc1.spec.ts",
        code=code,
        required_page_changes=[],
        test_data={},
        dependencies=[],
        warnings=[],
        content_hash=sha256(code.encode()).hexdigest(),
        validation_status="VALID",
    )


@pytest.mark.asyncio
async def test_execution_requires_matching_approval_hash() -> None:
    artifact = valid_artifact()
    approval = ApprovalRecord(
        workflow_id="WF1",
        stage="AUTOMATION",
        decision=ApprovalDecision.APPROVED,
        approver="human",
        comment="reviewed",
        artifact_hash="wrong",
    )
    agent = ExecutionAgent(FakePlaywrightTool())  # type: ignore[arg-type]
    with pytest.raises(PermissionError, match="hash"):
        await agent.execute(artifact, approval)


@pytest.mark.asyncio
async def test_execution_uses_tool_result_after_approval() -> None:
    artifact = valid_artifact()
    approval = ApprovalRecord(
        workflow_id="WF1",
        stage="AUTOMATION",
        decision=ApprovalDecision.APPROVED,
        approver="human",
        comment="reviewed",
        artifact_hash=artifact.content_hash,
    )
    agent = ExecutionAgent(FakePlaywrightTool())  # type: ignore[arg-type]
    results = await agent.execute(artifact, approval)
    assert results[0].status == "PASSED"
