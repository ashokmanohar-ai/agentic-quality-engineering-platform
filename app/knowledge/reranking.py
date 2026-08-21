"""Stable optional lexical reranker."""

from app.tools.knowledge_tool import RetrievalResult


def rerank(results: list[RetrievalResult]) -> list[RetrievalResult]:
    return sorted(results, key=lambda result: (-result.score, result.source_id))
