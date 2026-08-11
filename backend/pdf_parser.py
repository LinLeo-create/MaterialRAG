from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .schemas import DocumentResult, PageResult


class InvalidPdfError(ValueError):
    """Raised when uploaded content cannot be parsed as a PDF."""


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
    except InvalidPdfError:
        raise
    except (PdfReadError, ValueError, OSError, KeyError) as exc:
        raise InvalidPdfError("PDF 已損壞或格式不受支援。") from exc

    character_count = sum(page.character_count for page in pages)
    return DocumentResult(
        filename=filename,
        page_count=len(pages),
        character_count=character_count,
        has_extractable_text=character_count > 0,
        pages=pages,
    )
