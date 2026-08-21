"""Validated domain contracts shared by agents, APIs, and persistence."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


def now_utc() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Role(StrEnum):
    VIEWER = "VIEWER"
    QUALITY_ENGINEER = "QUALITY_ENGINEER"
    APPROVER = "APPROVER"
    ADMIN = "ADMIN"


class Requirement(StrictModel):
    id: str
    project_id: str
    tenant_id: str = "default"
    title: str
    user_story: str
    acceptance_criteria: list[str]
    critical: bool = False
    source_ids: list[str] = Field(default_factory=list)


class RequirementQuality(StrictModel):
    valid: bool
    findings: list[str]


class RequirementAnalysis(StrictModel):
    actors: list[str]
    functional_requirements: list[str]
    business_rules: list[str]
    acceptance_criteria: list[str]
    assumptions: list[str]
    ambiguities: list[str]
    missing_information: list[str]
    dependencies: list[str]
    testability_concerns: list[str]
    evidence: list[str]
    confidence: float = Field(ge=0, le=1)


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskItem(StrictModel):
    id: str
    category: str
    description: str
    probability: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    rationale: str
    recommended_tests: list[str]
    requirement_references: list[str]
    evidence: list[str]
    confidence: float = Field(ge=0, le=1)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def score(self) -> int:
        return self.probability * self.impact

    @computed_field  # type: ignore[prop-decorator]
    @property
    def level(self) -> RiskLevel:
        if self.score <= 4:
            return RiskLevel.LOW
        if self.score <= 9:
            return RiskLevel.MEDIUM
        if self.score <= 16:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL


class TestStep(StrictModel):
    action: str
    expected: str


class TestCase(StrictModel):
    id: str
    title: str
    objective: str
    type: str
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    risk_reference: list[str]
    requirement_reference: list[str]
    acceptance_criteria_reference: list[str]
    preconditions: list[str]
    steps: list[TestStep]
    expected_result: str
    test_data: dict[str, Any]
    automation_candidate: bool
    tags: list[str]
    critical: bool = False

    @field_validator("requirement_reference", "acceptance_criteria_reference")
    @classmethod
    def traceability_required(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("test cases cannot be orphaned")
        return value


class CoverageStatus(StrEnum):
    COVERED = "COVERED"
    PARTIALLY_COVERED = "PARTIALLY_COVERED"
    NOT_COVERED = "NOT_COVERED"
    DUPLICATE = "DUPLICATE"
    WEAK_COVERAGE = "WEAK_COVERAGE"


class CoverageFinding(StrictModel):
    source_id: str
    coverage_status: CoverageStatus
    related_test_ids: list[str]
    gaps: list[str]
    recommendation: str


class CoverageReport(StrictModel):
    findings: list[CoverageFinding]
    requirement_coverage: float = Field(ge=0, le=100)
    critical_requirement_coverage: float = Field(ge=0, le=100)
    critical_risk_coverage: float = Field(ge=0, le=100)
    gate_passed: bool


class RegressionRecommendation(StrictModel):
    test_id: str
    classification: Literal["MUST_RUN", "SHOULD_RUN", "OPTIONAL", "NOT_IMPACTED"]
    confidence: float = Field(ge=0, le=1)
    impacted_components: list[str]
    rationale: str
    evidence: list[str]


class AutomationArtifact(StrictModel):
    id: str
    test_case_id: str
    relative_path: str
    code: str
    required_page_changes: list[str]
    test_data: dict[str, Any]
    dependencies: list[str]
    warnings: list[str]
    content_hash: str
    validation_status: Literal["PENDING", "VALID", "INVALID"] = "PENDING"
    validation_errors: list[str] = Field(default_factory=list)


class ApprovalDecision(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalRecord(StrictModel):
    workflow_id: str
    stage: Literal["AUTOMATION", "RELEASE_OVERRIDE"]
    decision: ApprovalDecision
    approver: str
    comment: str
    artifact_hash: str
    timestamp: datetime = Field(default_factory=now_utc)
    original_decision: str | None = None
    override_decision: str | None = None


class ExecutionResult(StrictModel):
    test_id: str
    status: Literal["PASSED", "FAILED", "SKIPPED", "NOT_RUN"]
    duration_ms: int = Field(ge=0)
    retry_count: int = Field(ge=0)
    screenshot_paths: list[str]
    trace_path: str | None
    error_message: str | None
    browser: str = "chromium"
    console_errors: list[str] = Field(default_factory=list)
    network_errors: list[str] = Field(default_factory=list)


class FailureAnalysis(StrictModel):
    test_id: str
    classification: Literal[
        "PRODUCT_DEFECT",
        "AUTOMATION_DEFECT",
        "TEST_DATA",
        "ENVIRONMENT",
        "NETWORK",
        "DEPENDENCY",
        "FLAKY",
        "UNKNOWN",
    ]
    confidence: float = Field(ge=0, le=1)
    probable_root_cause: str
    supporting_evidence: list[str]
    hypotheses: list[str]
    recommended_action: str
    requires_human_review: bool


class EvaluationSummary(StrictModel):
    schema_validity: float
    traceability: float
    tool_correctness: float
    hallucination_rate: float
    overall_score: float
    gate_passed: bool


class ReleaseDecision(StrEnum):
    PASS = "PASS"  # noqa: S105
    CONDITIONAL_PASS = "CONDITIONAL_PASS"  # noqa: S105
    FAIL = "FAIL"


class ReleaseRecommendation(StrictModel):
    deterministic_decision: ReleaseDecision
    final_recommendation: ReleaseDecision
    mandatory_gate_failures: list[str]
    warnings: list[str]
    quality_summary: str
    outstanding_risks: list[str]
    evidence: list[str]
    created_at: datetime = Field(default_factory=now_utc)


class AgentRun(StrictModel):
    workflow_id: str
    agent: str
    prompt_name: str
    prompt_version: str
    provider: str
    model: str
    input_hash: str
    output_json: dict[str, Any]
    validation_status: str
    latency_ms: int
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    created_at: datetime = Field(default_factory=now_utc)


class AuditEvent(StrictModel):
    workflow_id: str
    actor: str
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=now_utc)


class WorkflowStatus(StrEnum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    LOOP_GUARD_TRIGGERED = "LOOP_GUARD_TRIGGERED"
    FAILED = "FAILED"
