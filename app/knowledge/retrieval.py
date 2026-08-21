"""Retrieval facade preserving project scope and source citations."""

from app.tools.knowledge_tool import KnowledgeTool, RetrievalResult


def retrieve(
    tool: KnowledgeTool, project_id: str, query: str, top_k: int = 5
) -> list[RetrievalResult]:
    return tool.search(project_id, query, top_k)
