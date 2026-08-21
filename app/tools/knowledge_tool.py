"""Project-scoped lexical retrieval with source IDs and scores."""

import math
import re
from collections import Counter

from pydantic import BaseModel, ConfigDict, Field

from app.tools.security import ToolCategory


class KnowledgeChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str
    source_id: str
    text: str


class RetrievalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    chunk: str
    score: float = Field(ge=0)


def _tokens(text: str) -> Counter[str]:
    return Counter(re.findall(r"[a-z0-9]+", text.casefold()))


class KnowledgeTool:
    category = ToolCategory.READ_ONLY

    def __init__(self) -> None:
        self._chunks: list[KnowledgeChunk] = []

    def ingest(self, chunk: KnowledgeChunk) -> None:
        self._chunks.append(chunk)

    def search(self, project_id: str, query: str, top_k: int = 5) -> list[RetrievalResult]:
        query_tokens = _tokens(query)
        if not query_tokens:
            return []
        scored: list[RetrievalResult] = []
        for chunk in self._chunks:
            if chunk.project_id != project_id:
                continue
            chunk_tokens = _tokens(chunk.text)
            overlap = sum((query_tokens & chunk_tokens).values())
            denominator = math.sqrt(sum(query_tokens.values()) * max(1, sum(chunk_tokens.values())))
            score = overlap / denominator
            if score:
                scored.append(
                    RetrievalResult(source_id=chunk.source_id, chunk=chunk.text, score=score)
                )
        return sorted(scored, key=lambda item: item.score, reverse=True)[: max(1, min(top_k, 20))]
