"""Evidence-aware failure triage with confidence controls."""

from app.agents.base_agent import BaseAgent
from app.models import ExecutionResult, FailureAnalysis


class FailureTriageAgent(BaseAgent[FailureAnalysis]):
    name = "FailureTriage"
    prompt_slug = "failure-triage"
    response_model = FailureAnalysis

    def __init__(self, *args: object, unknown_threshold: float = 0.60, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.unknown_threshold = unknown_threshold

    async def triage(self, workflow_id: str, result: ExecutionResult) -> FailureAnalysis:
        analysis = await self.propose(workflow_id, result.model_dump_json())
        analysis.test_id = result.test_id
        if analysis.confidence < self.unknown_threshold:
            analysis.classification = "UNKNOWN"
            analysis.requires_human_review = True
        return analysis
