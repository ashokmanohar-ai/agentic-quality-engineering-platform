from pathlib import Path

import pytest

from app.agents.automation_generator import AutomationGeneratorAgent
from app.agents.failure_triage import FailureTriageAgent
from app.agents.requirement_analyst import RequirementAnalystAgent
from app.agents.risk_analyst import RiskAnalysisAgent
from app.agents.test_designer import TestDesignAgent as DesignAgent
from app.llm.mock_provider import MockProvider
from app.models import ExecutionResult, Requirement


def demo_requirement() -> Requirement:
    return Requirement(
        id="REQ-001",
        project_id="demo",
        title="Password reset",
        user_story="As a registered user I can safely reset my forgotten password",
        acceptance_criteria=["Token expires", "New login works"],
        critical=True,
    )


@pytest.mark.asyncio
async def test_agent_chain_uses_valid_structured_outputs() -> None:
    provider = MockProvider()
    requirement = demo_requirement()
    analysis = await RequirementAnalystAgent(provider).analyse("WF-1", requirement)
    risks = await RiskAnalysisAgent(provider).analyse("WF-1", requirement, analysis)
    tests = await DesignAgent(provider).design("WF-1", requirement, analysis, risks)
    artifact = await AutomationGeneratorAgent(provider).generate("WF-1", tests[0])
    assert analysis.confidence > 0.8
    assert risks[0].score == 20
    assert all(test.requirement_reference == [requirement.id] for test in tests)
    assert artifact.relative_path.endswith(".spec.ts")


@pytest.mark.asyncio
async def test_low_confidence_triage_becomes_unknown() -> None:
    result = ExecutionResult(
        test_id="TC1",
        status="FAILED",
        duration_ms=20,
        retry_count=0,
        screenshot_paths=[],
        trace_path=None,
        error_message="mystery",
    )
    triage = await FailureTriageAgent(MockProvider(), unknown_threshold=0.60).triage("WF-1", result)
    assert triage.classification == "UNKNOWN"
    assert triage.requires_human_review


@pytest.mark.asyncio
async def test_provider_unavailable_is_not_fabricated() -> None:
    from app.llm.provider import ModelUnavailableError

    with pytest.raises(ModelUnavailableError):
        await RequirementAnalystAgent(MockProvider(unavailable=True)).analyse(
            "WF-1", demo_requirement()
        )


def test_all_agent_prompts_are_external_files() -> None:
    assert len(list(Path("prompts").glob("*/v1.md"))) >= 8
