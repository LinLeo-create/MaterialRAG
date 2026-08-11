from pydantic import BaseModel, Field


class PageResult(BaseModel):
    page_number: int = Field(ge=1)
    text: str
    character_count: int = Field(ge=0)


class ChunkResult(BaseModel):
    chunk_index: int = Field(ge=0)
    page_number: int = Field(ge=1)
    text: str
    character_count: int = Field(ge=0)


class DocumentResult(BaseModel):
    filename: str
    page_count: int = Field(ge=0)
    character_count: int = Field(ge=0)
    has_extractable_text: bool
    pages: list[PageResult]
    chunk_count: int = Field(ge=0)
    chunks: list[ChunkResult]


class ParseResponse(BaseModel):
    documents: list[DocumentResult]
