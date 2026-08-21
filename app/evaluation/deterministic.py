"""Deterministic evaluation, grounding, and hallucination checks."""

import json
from pathlib import Path
from typing import Any

from app.models import EvaluationSummary


def safe_rate(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100, 2) if denominator else 100.0


def detect_unsupported_references(claimed: list[str], known: set[str]) -> list[str]:
    return sorted(set(claimed) - known)


def evaluate_dataset(path: Path = Path("datasets/agent-evaluation/cases.jsonl")) -> dict[str, Any]:
    if not path.exists():
        return EvaluationSummary(
            schema_validity=0,
            traceability=0,
            tool_correctness=0,
            hallucination_rate=100,
            overall_score=0,
            gate_passed=False,
        ).model_dump()
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    required = {"id", "category", "input", "expected"}
    valid = sum(required.issubset(case) for case in cases)
    traceable = sum(bool(case.get("expected", {}).get("source_ids")) for case in cases)
    tool_correct = sum(case.get("expected", {}).get("tool") != "arbitrary_shell" for case in cases)
    hallucinations = sum(bool(case.get("expected", {}).get("unsupported_claims")) for case in cases)
    schema_rate = safe_rate(valid, len(cases))
    traceability = safe_rate(traceable, len(cases))
    tool_rate = safe_rate(tool_correct, len(cases))
    hallucination_rate = safe_rate(hallucinations, len(cases))
    overall = round((schema_rate + traceability + tool_rate + (100 - hallucination_rate)) / 4, 2)
    summary = EvaluationSummary(
        schema_validity=schema_rate,
        traceability=traceability,
        tool_correctness=tool_rate,
        hallucination_rate=hallucination_rate,
        overall_score=overall,
        gate_passed=schema_rate >= 99
        and traceability == 100
        and tool_rate >= 98
        and hallucination_rate <= 2,
    )
    return {"case_count": len(cases), **summary.model_dump()}
