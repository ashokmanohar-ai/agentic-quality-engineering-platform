"""Structured judge contract for qualitative dimensions only."""

from pydantic import BaseModel, ConfigDict, Field


class JudgeScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score: float = Field(ge=0, le=1)
    rationale: str
    evidence: list[str]
