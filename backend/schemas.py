from pydantic import BaseModel, Field, SecretStr


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
    title: str
    page_count: int = Field(ge=0)
    character_count: int = Field(ge=0)
    has_extractable_text: bool
    pages: list[PageResult]
    chunk_count: int = Field(ge=0)
    chunks: list[ChunkResult]


class ParseResponse(BaseModel):
    documents: list[DocumentResult]


class IndexedDocument(BaseModel):
    document_id: str
    filename: str
    title: str
    page_count: int = Field(ge=0)
    character_count: int = Field(ge=0)
    has_extractable_text: bool
    chunk_count: int = Field(ge=0)
    chunks: list[ChunkResult]
    status: str


class IndexResponse(BaseModel):
    documents: list[IndexedDocument]


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    document_ids: list[str] | None = None


class SearchResult(BaseModel):
    document_id: str
    filename: str
    page_number: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    text: str
    score: float = Field(ge=0, le=1)


class SearchResponse(BaseModel):
    results: list[SearchResult]


class DeleteResponse(BaseModel):
    document_id: str
    deleted_chunks: int = Field(ge=0)


class ExtractionRequest(BaseModel):
    document_ids: list[str] = Field(min_length=1, max_length=10)
    fields: list[str] = Field(min_length=1, max_length=20)
    top_k: int = Field(default=5, ge=1, le=10)


class Citation(BaseModel):
    filename: str
    page_number: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    text: str
    score: float = Field(ge=0, le=1)


class ExtractedField(BaseModel):
    field: str
    value: str | None
    unit: str | None
    confidence: str
    citations: list[Citation]


class DocumentExtraction(BaseModel):
    document_id: str
    filename: str
    fields: list[ExtractedField]


class ExtractionResponse(BaseModel):
    documents: list[DocumentExtraction]


class ExtractionStatus(BaseModel):
    provider: str
    model: str
    configured: bool


class GeminiConfigurationRequest(BaseModel):
    api_key: SecretStr = Field(min_length=1, max_length=500)
    model: str | None = Field(default=None, min_length=1, max_length=200)
