"""Deterministic, zero-cost provider used by CI and offline demonstrations."""

from hashlib import sha256
from typing import cast

from pydantic import BaseModel

from app.llm.provider import Message, ResponseT, Usage
from app.models import (
    AutomationArtifact,
    CoverageFinding,
    CoverageReport,
    CoverageStatus,
    FailureAnalysis,
    RegressionRecommendation,
    RequirementAnalysis,
    RiskItem,
    TestCase,
    TestStep,
)


class MockProvider:
    name = "mock"
    model_name = "deterministic-mock-v1"

    def __init__(self, malformed: bool = False, unavailable: bool = False) -> None:
        self.malformed = malformed
        self.unavailable = unavailable
        self.last_usage = Usage()

    async def generate(self, messages: list[Message], response_model: type[ResponseT]) -> ResponseT:
        if self.unavailable:
            from app.llm.provider import ModelUnavailableError

            raise ModelUnavailableError("mock provider configured as unavailable")
        if self.malformed:
            return response_model.model_validate({"malformed": True})
        text = "\n".join(m.content for m in messages)
        output = self._fixture(response_model.__name__, text)
        return cast(ResponseT, output)

    def _fixture(self, model_name: str, text: str) -> BaseModel:
        evidence = ["REQ-001", "AC-01"]
        if model_name == "RequirementAnalysis":
            return RequirementAnalysis(
                actors=["registered customer"],
                functional_requirements=[
                    "Allow a registered customer to complete the requested flow"
                ],
                business_rules=["Only valid, current tokens may be accepted"],
                acceptance_criteria=["AC-01", "AC-02"],
                assumptions=[],
                ambiguities=["Rate limits are not specified"],
                missing_information=["Expected service-level objective is not specified"],
                dependencies=["identity service", "notification service"],
                testability_concerns=[],
                evidence=evidence,
                confidence=0.92,
            )
        if model_name == "RiskItem":
            payment = "payment" in text.lower()
            return RiskItem(
                id="RISK-001",
                category="Data Risk" if payment else "Security Risk",
                description=(
                    "A retry could create a duplicate charge"
                    if payment
                    else "A reset token could be replayed or accepted after expiry"
                ),
                probability=4,
                impact=5,
                rationale="The flow changes protected account or financial state",
                recommended_tests=["negative token test", "idempotency or replay test"],
                requirement_references=["REQ-001"],
                evidence=evidence,
                confidence=0.90,
            )
        if model_name == "TestCase":
            return TestCase(
                id="TC-REQ-001-001",
                title="Reject an expired or replayed operation token",
                objective="Verify safe handling of an invalid state-changing request",
                type="SECURITY_FUNCTIONAL",
                priority="CRITICAL",
                risk_reference=["RISK-001"],
                requirement_reference=["REQ-001"],
                acceptance_criteria_reference=["AC-01"],
                preconditions=["A registered user and expired token exist"],
                steps=[
                    TestStep(action="Open the operation link", expected="The request is validated"),
                    TestStep(
                        action="Submit the expired token", expected="The operation is rejected"
                    ),
                ],
                expected_result="No protected state changes and a safe error is shown",
                test_data={"token_state": "expired"},
                automation_candidate=True,
                tags=["security", "regression"],
                critical=True,
            )
        if model_name == "CoverageReport":
            return CoverageReport(
                findings=[
                    CoverageFinding(
                        source_id="REQ-001",
                        coverage_status=CoverageStatus.COVERED,
                        related_test_ids=["TC-REQ-001-001"],
                        gaps=[],
                        recommendation="Maintain traceability during implementation",
                    )
                ],
                requirement_coverage=100,
                critical_requirement_coverage=100,
                critical_risk_coverage=100,
                gate_passed=True,
            )
        if model_name == "RegressionRecommendation":
            return RegressionRecommendation(
                test_id="TC-REQ-001-001",
                classification="MUST_RUN",
                confidence=0.94,
                impacted_components=["authentication"],
                rationale="The test is directly linked to the changed flow",
                evidence=["git-diff:app/auth.py", "REQ-001"],
            )
        if model_name == "AutomationArtifact":
            code = (
                "import { test, expect } from '@playwright/test';\n\n"
                "test('expired operation token is rejected', async ({ page }) => {\n"
                '  await page.goto("data:text/html,'
                "<div role='alert'>This link has expired</div>\");\n"
                "  await expect(page.getByRole('alert')).toContainText('expired');\n"
                "});\n"
            )
            return AutomationArtifact(
                id="AUTO-001",
                test_case_id="TC-REQ-001-001",
                relative_path="tc-req-001-001.spec.ts",
                code=code,
                required_page_changes=[],
                test_data={"token_state": "expired"},
                dependencies=[],
                warnings=["Review baseURL and fixture assumptions"],
                content_hash=sha256(code.encode()).hexdigest(),
            )
        if model_name == "FailureAnalysis":
            lowered = text.lower()
            is_network = "econn" in lowered or '"error_message":"network' in lowered
            return FailureAnalysis(
                test_id="TC-REQ-001-001",
                classification="NETWORK" if is_network else "UNKNOWN",
                confidence=0.88 if is_network else 0.50,
                probable_root_cause=(
                    "Connection failure" if is_network else "Insufficient evidence"
                ),
                supporting_evidence=(["ECONNRESET in runner output"] if is_network else []),
                hypotheses=[] if is_network else ["A product or environment issue may exist"],
                recommended_action="Review trace and environment logs",
                requires_human_review=not is_network,
            )
        raise ValueError(f"No deterministic fixture for {model_name}")
