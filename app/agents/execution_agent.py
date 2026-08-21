"""Execution adapter that consumes real Playwright JSON and never fabricates results."""

from app.models import ApprovalDecision, ApprovalRecord, AutomationArtifact, ExecutionResult
from app.tools.playwright_tool import PlaywrightTool


class ExecutionAgent:
    name = "ExecutionAgent"

    def __init__(self, tool: PlaywrightTool) -> None:
        self.tool = tool

    async def execute(
        self, artifact: AutomationArtifact, approval: ApprovalRecord | None
    ) -> list[ExecutionResult]:
        if artifact.validation_status != "VALID":
            raise PermissionError("automation must be validated before execution")
        if approval is None or approval.decision != ApprovalDecision.APPROVED:
            raise PermissionError("automation requires an explicit approval")
        if approval.artifact_hash != artifact.content_hash:
            raise PermissionError("approval does not match the artifact hash")
        return await self.tool.run(artifact.relative_path)
