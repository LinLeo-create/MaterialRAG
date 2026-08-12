from io import BytesIO
from pathlib import Path
import re

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .chunker import chunk_pages
from .schemas import DocumentResult, PageResult


class InvalidPdfError(ValueError):
    """Raised when uploaded content cannot be parsed as a PDF."""


def _clean_title(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" \t\r\n-–—|_")


def _is_usable_title(value: str, filename: str) -> bool:
    title = _clean_title(value)
    filename_stem = _clean_title(Path(filename).stem)
    lowered = title.casefold()
    return (
        8 <= len(title) <= 300
        and title.casefold() != filename_stem.casefold()
        and not lowered.startswith(("http://", "https://", "doi:"))
        and not re.fullmatch(r"[\d\W_]+", title)
    )


def infer_title(filename: str, metadata_title: str | None, first_page_text: str) -> str:
    """Prefer PDF metadata, then infer a conservative title from page-one lines."""
    if metadata_title and _is_usable_title(metadata_title, filename):
        return _clean_title(metadata_title)

    lines = [_clean_title(line) for line in first_page_text.splitlines()]
    candidates = []
    for line in lines[:20]:
        lowered = line.casefold()
        if not _is_usable_title(line, filename):
            continue
        if any(marker in lowered for marker in ("doi.org", "www.", "copyright", "received ")):
            continue
        if re.search(r"\b(volume|vol\.|issue|issn)\b", lowered):
            continue
        candidates.append(line)
        if len(candidates) == 2 or len(" ".join(candidates)) >= 80:
            break
    if candidates:
        return _clean_title(" ".join(candidates))
    return _clean_title(Path(filename).stem) or "未命名文獻"


def parse_pdf(filename: str, content: bytes) -> DocumentResult:
    if not content.startswith(b"%PDF-"):
        raise InvalidPdfError("檔案內容不是有效的 PDF。")

    try:
        reader = PdfReader(BytesIO(content), strict=False)
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as exc:
                raise InvalidPdfError("目前無法解析受密碼保護的 PDF。") from exc

        pages = []
        for index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            pages.append(
                PageResult(
                    page_number=index,
                    text=text,
                    character_count=len(text),
                )
            )
        metadata_title = None
        if reader.metadata:
            metadata_title = reader.metadata.title
    except InvalidPdfError:
        raise
    except (PdfReadError, ValueError, OSError, KeyError) as exc:
        raise InvalidPdfError("PDF 已損壞或格式不受支援。") from exc

    character_count = sum(page.character_count for page in pages)
    chunks = chunk_pages(pages)
    title = infer_title(
        filename,
        metadata_title,
        pages[0].text if pages else "",
    )
    return DocumentResult(
        filename=filename,
        title=title,
        page_count=len(pages),
        character_count=character_count,
        has_extractable_text=character_count > 0,
        pages=pages,
        chunk_count=len(chunks),
        chunks=chunks,
    )
