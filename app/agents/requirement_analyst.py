"""Requirement analysis with deterministic pre-flight quality checks."""

from app.agents.base_agent import BaseAgent
from app.models import Requirement, RequirementAnalysis, RequirementQuality


def validate_requirement(requirement: Requirement) -> RequirementQuality:
    findings: list[str] = []
    if not requirement.user_story.strip():
        findings.append("User story is empty")
    if len(requirement.user_story.split()) < 6:
        findings.append("User story is very short")
    if not requirement.acceptance_criteria:
        findings.append("Acceptance criteria are absent")
    normalized = [item.casefold().strip() for item in requirement.acceptance_criteria]
    if len(normalized) != len(set(normalized)):
        findings.append("Acceptance criteria contain duplicates")
    return RequirementQuality(valid=not findings, findings=findings)


class RequirementAnalystAgent(BaseAgent[RequirementAnalysis]):
    name = "RequirementAnalyst"
    prompt_slug = "requirement-analyst"
    response_model = RequirementAnalysis

    async def analyse(self, workflow_id: str, requirement: Requirement) -> RequirementAnalysis:
        quality = validate_requirement(requirement)
        content = (
            requirement.model_dump_json()
            + "\nDeterministic findings: "
            + ", ".join(quality.findings)
        )
        analysis = await self.propose(workflow_id, content)
        if quality.findings:
            analysis.testability_concerns.extend(
                finding
                for finding in quality.findings
                if finding not in analysis.testability_concerns
            )
        return analysis
