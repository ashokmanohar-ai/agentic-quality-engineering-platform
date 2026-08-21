"""Playwright artifact proposal; generated files are validated before approval/execution."""

from hashlib import sha256

from app.agents.base_agent import BaseAgent
from app.models import AutomationArtifact, TestCase


class AutomationGeneratorAgent(BaseAgent[AutomationArtifact]):
    name = "AutomationGenerator"
    prompt_slug = "automation-generator"
    response_model = AutomationArtifact

    async def generate(self, workflow_id: str, test_case: TestCase) -> AutomationArtifact:
        artifact = await self.propose(workflow_id, test_case.model_dump_json())
        artifact.test_case_id = test_case.id
        artifact.relative_path = f"{test_case.id.lower()}.spec.ts"
        artifact.content_hash = sha256(artifact.code.encode()).hexdigest()
        return artifact
