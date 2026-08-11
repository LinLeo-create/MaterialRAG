from pydantic import BaseModel, Field


class PageResult(BaseModel):
    page_number: int = Field(ge=1)
    text: str
    character_count: int = Field(ge=0)


class DocumentResult(BaseModel):
    filename: str
    page_count: int = Field(ge=0)
    character_count: int = Field(ge=0)
    has_extractable_text: bool
    pages: list[PageResult]


class ParseResponse(BaseModel):
    documents: list[DocumentResult]
