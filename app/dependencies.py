"""Application service container."""

from functools import lru_cache
from typing import TYPE_CHECKING

from app.config import Settings, get_settings
from app.llm import create_provider
from app.orchestration.graph import WorkflowEngine
from app.persistence.database import Database
from app.persistence.repositories import (
    EvidenceRepository,
    RequirementRepository,
    WorkflowRepository,
)
from app.tools.playwright_tool import PlaywrightTool

if TYPE_CHECKING:
    from app.agents.execution_agent import ExecutionAgent


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db = Database(settings.database_url)
        self.db.initialize()
        self.requirements = RequirementRepository(self.db)
        self.workflows = WorkflowRepository(self.db)
        self.evidence = EvidenceRepository(self.db)
        self.engine = WorkflowEngine(
            settings, create_provider(settings), self.workflows, self.evidence
        )
        self.engine.set_execution_agent(PlaywrightToolAgentFactory.build())


class PlaywrightToolAgentFactory:
    @staticmethod
    def build() -> "ExecutionAgent":
        from app.agents.execution_agent import ExecutionAgent

        return ExecutionAgent(PlaywrightTool())


@lru_cache
def get_container() -> Container:
    return Container(get_settings())
