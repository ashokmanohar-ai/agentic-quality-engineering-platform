from app.agents.requirement_analyst import validate_requirement
from app.knowledge.chunking import chunk_text
from app.knowledge.ingestion import ingest_text
from app.knowledge.retrieval import retrieve
from app.models import Requirement
from app.tools.knowledge_tool import KnowledgeTool


def test_requirement_quality_finds_duplicates_and_short_story() -> None:
    result = validate_requirement(
        Requirement(
            id="R1",
            project_id="P1",
            title="x",
            user_story="reset now",
            acceptance_criteria=["Expires", "expires"],
        )
    )
    assert not result.valid
    assert "Acceptance criteria contain duplicates" in result.findings
    assert "User story is very short" in result.findings


def test_chunk_configuration_validation() -> None:
    try:
        chunk_text("hello", size=10, overlap=10)
    except ValueError as exc:
        assert "invalid" in str(exc)
    else:
        raise AssertionError("invalid overlap was accepted")


def test_retrieval_is_project_scoped_and_cited() -> None:
    tool = KnowledgeTool()
    ingest_text(tool, "A", "ARCH-1", "Payment retries use one idempotency key.")
    ingest_text(tool, "B", "ARCH-2", "Another tenant payment document.")
    results = retrieve(tool, "A", "idempotency payment")
    assert len(results) == 1
    assert results[0].source_id.startswith("ARCH-1")
