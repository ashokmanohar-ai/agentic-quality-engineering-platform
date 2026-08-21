"""LangGraph orchestration with persistent pause/resume at the human gate."""

from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from app.agents.automation_generator import AutomationGeneratorAgent
from app.agents.coverage_reviewer import CoverageReviewerAgent
from app.agents.execution_agent import ExecutionAgent
from app.agents.failure_triage import FailureTriageAgent
from app.agents.quality_reviewer import QualityReviewerAgent
from app.agents.regression_selector import RegressionSelectorAgent
from app.agents.requirement_analyst import RequirementAnalystAgent
from app.agents.risk_analyst import RiskAnalysisAgent
from app.agents.test_designer import TestDesignAgent
from app.config import Settings
from app.llm import ModelProvider
from app.models import ApprovalDecision, AuditEvent, WorkflowStatus
from app.orchestration.state import QEWorkflowState
from app.persistence.repositories import EvidenceRepository, WorkflowRepository
from app.tools.automation_tool import AutomationWorkspace
from app.tools.git_diff_tool import GitDiff


def serialise_state(state: QEWorkflowState) -> dict[str, Any]:
    def convert(value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, list):
            return [convert(item) for item in value]
        if isinstance(value, dict):
            return {key: convert(item) for key, item in value.items()}
        return value

    return cast(dict[str, Any], convert(dict(state)))


class WorkflowEngine:
    def __init__(
        self,
        settings: Settings,
        provider: ModelProvider,
        workflows: WorkflowRepository,
        evidence: EvidenceRepository,
    ) -> None:
        self.settings = settings
        self.workflows = workflows
        self.evidence = evidence
        self.requirement_agent = RequirementAnalystAgent(provider)
        self.risk_agent = RiskAnalysisAgent(provider)
        self.test_agent = TestDesignAgent(provider)
        self.coverage_agent = CoverageReviewerAgent()
        self.regression_agent = RegressionSelectorAgent(provider)
        self.automation_agent = AutomationGeneratorAgent(provider)
        self.workspace = AutomationWorkspace(settings.automation_workspace)
        self.execution_agent: ExecutionAgent | None = None
        self.triage_agent = FailureTriageAgent(provider)
        self.quality_agent = QualityReviewerAgent()
        self.graph = self._build_planning_graph()
        self.resume_graph = self._build_resume_graph()

    def set_execution_agent(self, agent: ExecutionAgent) -> None:
        self.execution_agent = agent

    def _build_planning_graph(self) -> Any:
        graph = StateGraph(QEWorkflowState)
        graph.add_node("requirement_analysis", self._analyse_requirement)
        graph.add_node("risk_analysis", self._analyse_risk)
        graph.add_node("test_design", self._design_tests)
        graph.add_node("coverage_review", self._review_coverage)
        graph.add_node("regression_selection", self._select_regression)
        graph.add_node("automation_generation", self._generate_automation)
        graph.add_node("code_validation", self._validate_automation)
        graph.add_node("human_approval", self._await_approval)
        graph.add_edge(START, "requirement_analysis")
        graph.add_edge("requirement_analysis", "risk_analysis")
        graph.add_edge("risk_analysis", "test_design")
        graph.add_edge("test_design", "coverage_review")
        graph.add_conditional_edges(
            "coverage_review",
            self._coverage_route,
            {"retry": "test_design", "continue": "regression_selection", "stop": END},
        )
        graph.add_edge("regression_selection", "automation_generation")
        graph.add_edge("automation_generation", "code_validation")
        graph.add_edge("code_validation", "human_approval")
        graph.add_edge("human_approval", END)
        return graph.compile()

    def _build_resume_graph(self) -> Any:
        graph = StateGraph(QEWorkflowState)
        graph.add_node("execution", self._execute)
        graph.add_node("failure_triage", self._triage)
        graph.add_node("quality_review", self._quality_review)
        graph.add_edge(START, "execution")
        graph.add_edge("execution", "failure_triage")
        graph.add_edge("failure_triage", "quality_review")
        graph.add_edge("quality_review", END)
        return graph.compile()

    async def start(self, state: QEWorkflowState) -> QEWorkflowState:
        result = await self.graph.ainvoke(state, {"recursion_limit": self.settings.max_agent_steps})
        return cast(QEWorkflowState, result)

    async def resume(self, state: QEWorkflowState) -> QEWorkflowState:
        approval = state.get("approval")
        if approval is None or approval.decision != ApprovalDecision.APPROVED:
            raise PermissionError("workflow cannot resume without approval")
        result = await self.resume_graph.ainvoke(
            state, {"recursion_limit": self.settings.max_agent_steps}
        )
        return cast(QEWorkflowState, result)

    def _checkpoint(self, state: QEWorkflowState, stage: str, status: str = "RUNNING") -> None:
        state["current_stage"] = stage
        state["status"] = status
        state.setdefault("agent_timeline", []).append({"stage": stage, "status": status})
        requirement = state["requirement"]
        self.workflows.save(
            state["workflow_id"],
            state["project_id"],
            state["tenant_id"],
            requirement.id,
            status,
            stage,
            serialise_state(state),
        )
        self.evidence.audit(
            AuditEvent(
                workflow_id=state["workflow_id"],
                actor=state["actor"],
                action="STAGE_CHECKPOINT",
                entity_type="WORKFLOW",
                entity_id=stage,
                details={"status": status},
            )
        )

    def _capture_run(self, agent: Any) -> None:
        if agent.last_run is not None:
            self.evidence.add_agent_run(agent.last_run)

    async def _analyse_requirement(self, state: QEWorkflowState) -> dict[str, Any]:
        analysis = await self.requirement_agent.analyse(state["workflow_id"], state["requirement"])
        state["analysis"] = analysis
        self._capture_run(self.requirement_agent)
        self._checkpoint(state, "REQUIREMENT_ANALYSIS")
        return {
            "analysis": analysis,
            "current_stage": state["current_stage"],
            "status": state["status"],
            "agent_timeline": state["agent_timeline"],
        }

    async def _analyse_risk(self, state: QEWorkflowState) -> dict[str, Any]:
        analysis = state.get("analysis")
        if analysis is None:
            raise ValueError("requirement analysis is missing")
        risks = await self.risk_agent.analyse(state["workflow_id"], state["requirement"], analysis)
        state["risks"] = risks
        self._capture_run(self.risk_agent)
        self._checkpoint(state, "RISK_ANALYSIS")
        return {
            "risks": risks,
            "current_stage": state["current_stage"],
            "status": state["status"],
            "agent_timeline": state["agent_timeline"],
        }

    async def _design_tests(self, state: QEWorkflowState) -> dict[str, Any]:
        analysis = state.get("analysis")
        if analysis is None:
            raise ValueError("requirement analysis is missing")
        tests = await self.test_agent.design(
            state["workflow_id"], state["requirement"], analysis, state.get("risks", [])
        )
        state["tests"] = tests
        self._capture_run(self.test_agent)
        self._checkpoint(state, "TEST_DESIGN")
        return {
            "tests": tests,
            "current_stage": state["current_stage"],
            "status": state["status"],
            "agent_timeline": state["agent_timeline"],
        }

    def _review_coverage(self, state: QEWorkflowState) -> dict[str, Any]:
        coverage = self.coverage_agent.review(
            [state["requirement"]], state.get("risks", []), state.get("tests", [])
        )
        state["coverage"] = coverage
        self._checkpoint(state, "COVERAGE_REVIEW")
        return {
            "coverage": coverage,
            "current_stage": state["current_stage"],
            "status": state["status"],
            "agent_timeline": state["agent_timeline"],
        }

    def _coverage_route(self, state: QEWorkflowState) -> str:
        coverage = state.get("coverage")
        if coverage and coverage.gate_passed:
            return "continue"
        retries = state.get("coverage_retry_count", 0)
        if retries < self.settings.max_coverage_retries:
            state["coverage_retry_count"] = retries + 1
            return "retry"
        state["status"] = WorkflowStatus.FAILED.value
        return "stop"

    async def _select_regression(self, state: QEWorkflowState) -> dict[str, Any]:
        diff = GitDiff(changed_files=[], added_files=[], deleted_files=[], changed_modules=[])
        regression = await self.regression_agent.select(
            state["workflow_id"], diff, state.get("tests", [])
        )
        state["regression"] = regression
        self._capture_run(self.regression_agent)
        self._checkpoint(state, "REGRESSION_SELECTION")
        return {
            "regression": regression,
            "current_stage": state["current_stage"],
            "status": state["status"],
            "agent_timeline": state["agent_timeline"],
        }

    async def _generate_automation(self, state: QEWorkflowState) -> dict[str, Any]:
        candidates = [test for test in state.get("tests", []) if test.automation_candidate]
        artifacts = [
            await self.automation_agent.generate(state["workflow_id"], test)
            for test in candidates[:1]
        ]
        state["automation"] = artifacts
        self._capture_run(self.automation_agent)
        self._checkpoint(state, "AUTOMATION_GENERATION")
        return {
            "automation": artifacts,
            "current_stage": state["current_stage"],
            "status": state["status"],
            "agent_timeline": state["agent_timeline"],
        }

    def _validate_automation(self, state: QEWorkflowState) -> dict[str, Any]:
        artifacts = state.get("automation", [])
        for artifact in artifacts:
            self.workspace.write_validated(artifact)
        self._checkpoint(state, "CODE_VALIDATION")
        return {
            "automation": artifacts,
            "current_stage": state["current_stage"],
            "status": state["status"],
            "agent_timeline": state["agent_timeline"],
        }

    def _await_approval(self, state: QEWorkflowState) -> dict[str, Any]:
        self._checkpoint(state, "AUTOMATION_REVIEW", WorkflowStatus.AWAITING_APPROVAL.value)
        return {
            "current_stage": state["current_stage"],
            "status": state["status"],
            "agent_timeline": state["agent_timeline"],
        }

    async def _execute(self, state: QEWorkflowState) -> dict[str, Any]:
        if self.execution_agent is None:
            raise RuntimeError("execution agent is not configured")
        results = []
        for artifact in state.get("automation", []):
            results.extend(await self.execution_agent.execute(artifact, state.get("approval")))
        state["execution"] = results
        self._checkpoint(state, "EXECUTION")
        return {
            "execution": results,
            "current_stage": state["current_stage"],
            "status": state["status"],
            "agent_timeline": state["agent_timeline"],
        }

    async def _triage(self, state: QEWorkflowState) -> dict[str, Any]:
        analyses = [
            await self.triage_agent.triage(state["workflow_id"], result)
            for result in state.get("execution", [])
            if result.status == "FAILED"
        ]
        state["triage"] = analyses
        if analyses:
            self._capture_run(self.triage_agent)
        self._checkpoint(state, "FAILURE_TRIAGE")
        return {
            "triage": analyses,
            "current_stage": state["current_stage"],
            "status": state["status"],
            "agent_timeline": state["agent_timeline"],
        }

    def _quality_review(self, state: QEWorkflowState) -> dict[str, Any]:
        coverage = state.get("coverage")
        if coverage is None:
            raise ValueError("coverage report is missing")
        release = self.quality_agent.review(
            coverage, state.get("risks", []), state.get("execution", []), state.get("triage", [])
        )
        state["release"] = release
        self._checkpoint(state, "QUALITY_REVIEW", WorkflowStatus.COMPLETED.value)
        return {
            "release": release,
            "current_stage": state["current_stage"],
            "status": state["status"],
            "agent_timeline": state["agent_timeline"],
        }
