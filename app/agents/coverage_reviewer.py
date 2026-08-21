"""Deterministic traceability coverage and configurable quality gate."""

from dataclasses import dataclass

from app.models import (
    CoverageFinding,
    CoverageReport,
    CoverageStatus,
    Requirement,
    RiskItem,
    TestCase,
)


@dataclass(frozen=True)
class CoveragePolicy:
    critical_requirements: float = 100
    critical_risks: float = 100
    overall: float = 90


def _percentage(covered: int, total: int) -> float:
    return round((covered / total) * 100, 2) if total else 100.0


class CoverageReviewerAgent:
    name = "CoverageReviewer"

    def __init__(self, policy: CoveragePolicy | None = None) -> None:
        self.policy = policy or CoveragePolicy()

    def review(
        self, requirements: list[Requirement], risks: list[RiskItem], tests: list[TestCase]
    ) -> CoverageReport:
        findings: list[CoverageFinding] = []
        requirement_hits = 0
        critical_requirement_hits = 0
        critical_requirements = [req for req in requirements if req.critical]
        for requirement in requirements:
            linked = [test.id for test in tests if requirement.id in test.requirement_reference]
            covered_criteria = {
                reference
                for test in tests
                if requirement.id in test.requirement_reference
                for reference in test.acceptance_criteria_reference
            }
            expected = {f"AC-{i:02d}" for i in range(1, len(requirement.acceptance_criteria) + 1)}
            is_covered = bool(linked) and expected.issubset(covered_criteria)
            requirement_hits += int(is_covered)
            critical_requirement_hits += int(requirement.critical and is_covered)
            findings.append(
                CoverageFinding(
                    source_id=requirement.id,
                    coverage_status=(
                        CoverageStatus.COVERED
                        if is_covered
                        else CoverageStatus.PARTIALLY_COVERED
                        if linked
                        else CoverageStatus.NOT_COVERED
                    ),
                    related_test_ids=linked,
                    gaps=sorted(expected - covered_criteria),
                    recommendation=("No gap" if is_covered else "Add tests for uncovered criteria"),
                )
            )
        critical_risks = [risk for risk in risks if risk.level.value == "CRITICAL"]
        covered_critical_risks = sum(
            any(risk.id in test.risk_reference for test in tests) for risk in critical_risks
        )
        overall = _percentage(requirement_hits, len(requirements))
        critical_req = _percentage(critical_requirement_hits, len(critical_requirements))
        critical_risk = _percentage(covered_critical_risks, len(critical_risks))
        return CoverageReport(
            findings=findings,
            requirement_coverage=overall,
            critical_requirement_coverage=critical_req,
            critical_risk_coverage=critical_risk,
            gate_passed=(
                overall >= self.policy.overall
                and critical_req >= self.policy.critical_requirements
                and critical_risk >= self.policy.critical_risks
            ),
        )
