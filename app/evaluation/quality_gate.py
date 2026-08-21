"""Configurable continuous agent quality gate."""

from dataclasses import dataclass

from app.models import EvaluationSummary


@dataclass(frozen=True)
class EvaluationPolicy:
    structured_output_validity: float = 99
    traceability: float = 100
    tool_correctness: float = 98
    maximum_hallucination_rate: float = 2


def passes(summary: EvaluationSummary, policy: EvaluationPolicy | None = None) -> bool:
    policy = policy or EvaluationPolicy()
    return (
        summary.schema_validity >= policy.structured_output_validity
        and summary.traceability >= policy.traceability
        and summary.tool_correctness >= policy.tool_correctness
        and summary.hallucination_rate <= policy.maximum_hallucination_rate
    )
