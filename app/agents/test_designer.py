"""Risk-based structured test design with mandatory traceability."""

from copy import deepcopy

from app.agents.base_agent import BaseAgent
from app.models import Requirement, RequirementAnalysis, RiskItem, TestCase


class TestDesignAgent(BaseAgent[TestCase]):
    name = "TestDesigner"
    prompt_slug = "test-designer"
    response_model = TestCase

    async def design(
        self,
        workflow_id: str,
        requirement: Requirement,
        analysis: RequirementAnalysis,
        risks: list[RiskItem],
    ) -> list[TestCase]:
        proposed = await self.propose(
            workflow_id,
            requirement.model_dump_json()
            + "\n"
            + analysis.model_dump_json()
            + "\n"
            + "\n".join(r.model_dump_json() for r in risks),
        )
        proposed.requirement_reference = [requirement.id]
        proposed.acceptance_criteria_reference = ["AC-01"]
        proposed.risk_reference = [risk.id for risk in risks]
        cases = [proposed]
        for index, criterion in enumerate(requirement.acceptance_criteria[1:], start=2):
            case = deepcopy(proposed)
            case.id = f"TC-{requirement.id}-{index:03d}"
            case.title = f"Verify acceptance criterion {index}: {criterion[:60]}"
            case.objective = criterion
            case.acceptance_criteria_reference = [f"AC-{index:02d}"]
            case.type = "FUNCTIONAL" if index % 2 else "NEGATIVE"
            case.critical = requirement.critical
            cases.append(case)
        return cases
