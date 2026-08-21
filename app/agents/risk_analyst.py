"""Transparent risk assessment: model rationale, deterministic score."""

from app.agents.base_agent import BaseAgent
from app.models import Requirement, RequirementAnalysis, RiskItem


class RiskAnalysisAgent(BaseAgent[RiskItem]):
    name = "RiskAnalysis"
    prompt_slug = "risk-analyst"
    response_model = RiskItem

    async def analyse(
        self, workflow_id: str, requirement: Requirement, analysis: RequirementAnalysis
    ) -> list[RiskItem]:
        risk = await self.propose(
            workflow_id, requirement.model_dump_json() + "\n" + analysis.model_dump_json()
        )
        if requirement.id not in risk.requirement_references:
            risk.requirement_references.append(requirement.id)
        return [risk]
