import re

from .schemas import ChunkResult, PageResult

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150
_BOUNDARIES = ("\n\n", ". ", "。", "；", "; ", "，", ", ", " ")


def normalize_page_text(text: str) -> str:
    """Normalize PDF line wrapping while retaining paragraph boundaries."""
    paragraphs = re.split(r"\n\s*\n", text.replace("\r\n", "\n"))
    normalized = []
    for paragraph in paragraphs:
        compact = re.sub(r"(?<!-)\n", " ", paragraph)
        compact = compact.replace("-\n", "")
        compact = re.sub(r"[ \t]+", " ", compact).strip()
        if compact:
            normalized.append(compact)
    return "\n\n".join(normalized)


def _boundary_before(text: str, start: int, target: int) -> int:
    minimum = start + int((target - start) * 0.6)
    for separator in _BOUNDARIES:
        position = text.rfind(separator, minimum, target)
        if position >= 0:
            return position + len(separator)
    return target


def chunk_pages(
    pages: list[PageResult],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[ChunkResult]:
    if chunk_size < 100:
        raise ValueError("chunk_size must be at least 100 characters")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between 0 and chunk_size")

    chunks = []
    chunk_index = 0
    for page in pages:
        text = normalize_page_text(page.text)
        start = 0
        while start < len(text):
            target = min(start + chunk_size, len(text))
            end = target if target == len(text) else _boundary_before(text, start, target)
            content = text[start:end].strip()
            if content:
                chunks.append(
                    ChunkResult(
                        chunk_index=chunk_index,
                        page_number=page.page_number,
                        text=content,
                        character_count=len(content),
                    )
                )
                chunk_index += 1
            if end >= len(text):
                break
            start = max(start + 1, end - overlap)
    return chunks
