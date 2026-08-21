"""Typed application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "sqlite:///./aqe.db"
    model_provider: str = "mock"
    model_name: str = ""
    temperature: float = 0.0
    jwt_secret: str = Field(min_length=32)
    demo_password: str = Field(min_length=12)
    access_token_minutes: int = 60
    max_agent_steps: int = 25
    agent_timeout_seconds: int = 60
    max_coverage_retries: int = 1
    triage_review_threshold: float = 0.85
    triage_unknown_threshold: float = 0.60
    otel_enabled: bool = False
    phoenix_endpoint: str = ""
    automation_workspace: Path = Path("automation/playwright/generated")
    playwright_runner: Path = Path("automation/playwright/src/runner.mjs")


@lru_cache
def get_settings() -> Settings:
    return Settings()
