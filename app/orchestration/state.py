"""Explicit state passed between LangGraph nodes."""

from typing import Any, TypedDict, cast

from app.models import (
    ApprovalRecord,
    AutomationArtifact,
    CoverageReport,
    EvaluationSummary,
    ExecutionResult,
    FailureAnalysis,
    RegressionRecommendation,
    ReleaseRecommendation,
    Requirement,
    RequirementAnalysis,
    RiskItem,
    TestCase,
)


class QEWorkflowState(TypedDict, total=False):
    workflow_id: str
    project_id: str
    tenant_id: str
    actor: str
    requirement: Requirement
    analysis: RequirementAnalysis | None
    risks: list[RiskItem]
    tests: list[TestCase]
    coverage: CoverageReport | None
    regression: list[RegressionRecommendation]
    automation: list[AutomationArtifact]
    execution: list[ExecutionResult]
    triage: list[FailureAnalysis]
    evaluation: EvaluationSummary | None
    approval: ApprovalRecord | None
    release: ReleaseRecommendation | None
    status: str
    current_stage: str
    coverage_retry_count: int
    agent_timeline: list[dict[str, Any]]


def restore_state(data: dict[str, Any]) -> QEWorkflowState:
    """Rebuild Pydantic objects from a persisted JSON checkpoint."""
    restored = dict(data)
    if data.get("requirement"):
        restored["requirement"] = Requirement.model_validate(data["requirement"])
    if data.get("analysis"):
        restored["analysis"] = RequirementAnalysis.model_validate(data["analysis"])
    restored["risks"] = [RiskItem.model_validate(item) for item in data.get("risks", [])]
    restored["tests"] = [TestCase.model_validate(item) for item in data.get("tests", [])]
    if data.get("coverage"):
        restored["coverage"] = CoverageReport.model_validate(data["coverage"])
    restored["regression"] = [
        RegressionRecommendation.model_validate(item) for item in data.get("regression", [])
    ]
    restored["automation"] = [
        AutomationArtifact.model_validate(item) for item in data.get("automation", [])
    ]
    restored["execution"] = [
        ExecutionResult.model_validate(item) for item in data.get("execution", [])
    ]
    restored["triage"] = [FailureAnalysis.model_validate(item) for item in data.get("triage", [])]
    if data.get("evaluation"):
        restored["evaluation"] = EvaluationSummary.model_validate(data["evaluation"])
    if data.get("approval"):
        restored["approval"] = ApprovalRecord.model_validate(data["approval"])
    if data.get("release"):
        restored["release"] = ReleaseRecommendation.model_validate(data["release"])
    return cast(QEWorkflowState, restored)
