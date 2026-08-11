import os
from functools import lru_cache

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from .extraction import (
    ExtractionConfigurationError,
    ExtractionService,
    OpenAIExtractionProvider,
)
from .pdf_parser import InvalidPdfError, parse_pdf
from .schemas import (
    DeleteResponse,
    DocumentResult,
    ExtractionRequest,
    ExtractionResponse,
    IndexResponse,
    ParseResponse,
    SearchRequest,
    SearchResponse,
)
from .vector_index import VectorIndex, document_id_for

MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_FILES = 10

app = FastAPI(title="MaterialRAG API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_credentials=False,
    allow_methods=["DELETE", "GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@lru_cache
def get_vector_index() -> VectorIndex:
    return VectorIndex()


@lru_cache
def get_extraction_provider() -> OpenAIExtractionProvider:
    return OpenAIExtractionProvider()


async def read_and_parse_documents(
    files: list[UploadFile],
) -> list[tuple[bytes, DocumentResult]]:
    if not files:
        raise HTTPException(status_code=400, detail="請至少上傳一份 PDF。")
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"一次最多可處理 {MAX_FILES} 份 PDF。",
        )

    documents = []
    for upload in files:
        filename = upload.filename or "未命名.pdf"
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"{filename} 不是 PDF 檔案。",
            )

        content = await upload.read(MAX_FILE_SIZE + 1)
        await upload.close()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"{filename} 超過 20 MB 限制。",
            )

        try:
            document = await run_in_threadpool(parse_pdf, filename, content)
        except InvalidPdfError as exc:
            raise HTTPException(status_code=422, detail=f"{filename}：{exc}") from exc
        documents.append((content, document))

    return documents


@app.post("/api/documents/parse", response_model=ParseResponse)
async def parse_documents(files: list[UploadFile] = File(...)) -> ParseResponse:
    parsed = await read_and_parse_documents(files)
    return ParseResponse(documents=[document for _, document in parsed])


@app.post("/api/documents/index", response_model=IndexResponse)
async def index_documents(
    files: list[UploadFile] = File(...),
    index: VectorIndex = Depends(get_vector_index),
) -> IndexResponse:
    parsed = await read_and_parse_documents(files)
    indexed = []
    for content, document in parsed:
        if not document.chunks:
            raise HTTPException(
                status_code=422,
                detail=f"{document.filename} 沒有可建立索引的文字。",
            )
        indexed.append(
            await run_in_threadpool(
                index.index_document,
                document_id_for(content),
                document,
            )
        )
    return IndexResponse(documents=indexed)


@app.post("/api/retrieval/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    index: VectorIndex = Depends(get_vector_index),
) -> SearchResponse:
    results = await run_in_threadpool(
        index.search,
        request.query.strip(),
        request.top_k,
        request.document_ids,
    )
    return SearchResponse(results=results)


@app.delete("/api/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str,
    index: VectorIndex = Depends(get_vector_index),
) -> DeleteResponse:
    deleted = await run_in_threadpool(index.delete_document, document_id)
    return DeleteResponse(document_id=document_id, deleted_chunks=deleted)


@app.post("/api/extraction/run", response_model=ExtractionResponse)
async def extract_fields(
    request: ExtractionRequest,
    index: VectorIndex = Depends(get_vector_index),
    provider: OpenAIExtractionProvider = Depends(get_extraction_provider),
) -> ExtractionResponse:
    fields = list(dict.fromkeys(field.strip() for field in request.fields if field.strip()))
    if not fields:
        raise HTTPException(status_code=422, detail="請至少提供一個非空白欄位。")
    service = ExtractionService(index, provider)
    try:
        documents = [
            await run_in_threadpool(
                service.extract_document,
                document_id,
                fields,
                request.top_k,
            )
            for document_id in request.document_ids
        ]
    except ExtractionConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM 擷取失敗：{exc}") from exc
    return ExtractionResponse(documents=documents)
