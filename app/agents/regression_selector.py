"""Advisory regression selection grounded only in deterministic diff output."""

from app.agents.base_agent import BaseAgent
from app.models import RegressionRecommendation, TestCase
from app.tools.git_diff_tool import GitDiff


class RegressionSelectorAgent(BaseAgent[RegressionRecommendation]):
    name = "RegressionSelector"
    prompt_slug = "regression-selector"
    response_model = RegressionRecommendation

    async def select(
        self, workflow_id: str, diff: GitDiff, tests: list[TestCase]
    ) -> list[RegressionRecommendation]:
        if not tests:
            return []
        recommendation = await self.propose(
            workflow_id,
            diff.model_dump_json() + "\n" + "\n".join(test.model_dump_json() for test in tests),
        )
        recommendation.test_id = tests[0].id
        recommendation.evidence = (
            [f"git-diff:{path}" for path in diff.changed_files]
            if diff.changed_files
            else ["git-diff:no-changes"]
        )
        return [recommendation]
