"""Deterministic bounded text chunking."""


def chunk_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("invalid chunk configuration")
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        chunks.append(cleaned[start : start + size])
        start += size - overlap
    return chunks
