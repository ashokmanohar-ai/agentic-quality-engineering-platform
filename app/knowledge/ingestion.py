"""Untrusted knowledge ingestion into project-scoped chunks."""

from app.knowledge.chunking import chunk_text
from app.tools.knowledge_tool import KnowledgeChunk, KnowledgeTool


def ingest_text(tool: KnowledgeTool, project_id: str, source_id: str, text: str) -> int:
    chunks = chunk_text(text)
    for index, value in enumerate(chunks):
        tool.ingest(
            KnowledgeChunk(
                project_id=project_id,
                source_id=f"{source_id}#chunk-{index + 1}",
                text=value,
            )
        )
    return len(chunks)
