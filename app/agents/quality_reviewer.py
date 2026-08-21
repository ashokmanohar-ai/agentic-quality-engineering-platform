"""Narrative quality review constrained by deterministic release gates."""

from dataclasses import dataclass

from app.models import (
    CoverageReport,
    ExecutionResult,
    FailureAnalysis,
    ReleaseDecision,
    ReleaseRecommendation,
    RiskItem,
)


@dataclass(frozen=True)
class ReleasePolicy:
    critical_pass_rate: float = 100
    overall_pass_rate: float = 98


class QualityReviewerAgent:
    name = "QualityReviewer"

    def __init__(self, policy: ReleasePolicy | None = None) -> None:
        self.policy = policy or ReleasePolicy()

    def review(
        self,
        coverage: CoverageReport,
        risks: list[RiskItem],
        executions: list[ExecutionResult],
        triage: list[FailureAnalysis],
    ) -> ReleaseRecommendation:
        failures: list[str] = []
        warnings: list[str] = []
        if not coverage.gate_passed:
            failures.append("Coverage quality gate failed")
        critical_test_failures = [r for r in executions if r.status == "FAILED"]
        if critical_test_failures:
            failures.append("One or more executed critical tests failed")
        unresolved_product = [t for t in triage if t.classification == "PRODUCT_DEFECT"]
        if unresolved_product:
            failures.append("Unresolved product defects exist")
        uncertain = [t for t in triage if t.requires_human_review]
        if uncertain:
            warnings.append("Failure triage requires human review")
        not_run = [r for r in executions if r.status == "NOT_RUN"]
        if not_run or not executions:
            warnings.append("Automation execution is incomplete")
        decision = (
            ReleaseDecision.FAIL
            if failures
            else ReleaseDecision.CONDITIONAL_PASS
            if warnings
            else ReleaseDecision.PASS
        )
        return ReleaseRecommendation(
            deterministic_decision=decision,
            final_recommendation=decision,
            mandatory_gate_failures=failures,
            warnings=warnings,
            quality_summary=(
                f"Requirement coverage {coverage.requirement_coverage:.1f}%; "
                f"critical-risk coverage {coverage.critical_risk_coverage:.1f}%."
            ),
            outstanding_risks=[
                risk.description for risk in risks if risk.level.value in {"HIGH", "CRITICAL"}
            ],
            evidence=[
                f"coverage:{coverage.requirement_coverage}",
                f"executions:{len(executions)}",
                f"triage:{len(triage)}",
            ],
        )
