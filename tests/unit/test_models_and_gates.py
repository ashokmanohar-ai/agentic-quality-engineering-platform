import pytest
from pydantic import ValidationError

from app.agents.coverage_reviewer import CoverageReviewerAgent
from app.agents.quality_reviewer import QualityReviewerAgent
from app.models import Requirement, RiskItem
from app.models import TestCase as QECase
from app.models import TestStep as QEStep


def requirement(critical: bool = True) -> Requirement:
    return Requirement(
        id="REQ-001",
        project_id="P1",
        title="Reset",
        user_story="As a user I can safely reset my password",
        acceptance_criteria=["Expired token rejected", "New password accepted"],
        critical=critical,
    )


def risk() -> RiskItem:
    return RiskItem(
        id="RISK-001",
        category="Security Risk",
        description="Token replay",
        probability=4,
        impact=5,
        rationale="Protected state",
        recommended_tests=["replay"],
        requirement_references=["REQ-001"],
        evidence=["REQ-001"],
        confidence=0.9,
    )


def test_risk_score_and_level_are_deterministic() -> None:
    item = risk()
    assert item.score == 20
    assert item.level.value == "CRITICAL"


def test_risk_rejects_out_of_range_probability() -> None:
    with pytest.raises(ValidationError):
        risk().model_copy(update={"probability": 7}).model_validate(
            risk().model_dump() | {"probability": 7}
        )


def test_orphan_test_is_rejected() -> None:
    with pytest.raises(ValidationError, match="orphaned"):
        QECase(
            id="TC-1",
            title="orphan",
            objective="bad",
            type="FUNCTIONAL",
            priority="HIGH",
            risk_reference=[],
            requirement_reference=[],
            acceptance_criteria_reference=["AC-01"],
            preconditions=[],
            steps=[QEStep(action="a", expected="b")],
            expected_result="b",
            test_data={},
            automation_candidate=False,
            tags=[],
        )


def test_coverage_calculations_are_deterministic() -> None:
    case = QECase(
        id="TC-1",
        title="both criteria",
        objective="cover",
        type="FUNCTIONAL",
        priority="CRITICAL",
        risk_reference=["RISK-001"],
        requirement_reference=["REQ-001"],
        acceptance_criteria_reference=["AC-01", "AC-02"],
        preconditions=[],
        steps=[QEStep(action="a", expected="b")],
        expected_result="b",
        test_data={},
        automation_candidate=True,
        tags=[],
        critical=True,
    )
    report = CoverageReviewerAgent().review([requirement()], [risk()], [case])
    assert report.requirement_coverage == 100
    assert report.critical_requirement_coverage == 100
    assert report.critical_risk_coverage == 100
    assert report.gate_passed


def test_coverage_gate_fails_for_missing_criterion() -> None:
    case = QECase(
        id="TC-1",
        title="one criterion",
        objective="cover",
        type="FUNCTIONAL",
        priority="HIGH",
        risk_reference=[],
        requirement_reference=["REQ-001"],
        acceptance_criteria_reference=["AC-01"],
        preconditions=[],
        steps=[QEStep(action="a", expected="b")],
        expected_result="b",
        test_data={},
        automation_candidate=False,
        tags=[],
    )
    assert not CoverageReviewerAgent().review([requirement()], [risk()], [case]).gate_passed


def test_release_gate_cannot_pass_failed_coverage() -> None:
    coverage = CoverageReviewerAgent().review([requirement()], [risk()], [])
    release = QualityReviewerAgent().review(coverage, [risk()], [], [])
    assert release.final_recommendation.value == "FAIL"
    assert release.mandatory_gate_failures
