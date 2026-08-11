import os

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from .pdf_parser import InvalidPdfError, parse_pdf
from .schemas import ParseResponse

MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_FILES = 10

app = FastAPI(title="MaterialRAG API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/documents/parse", response_model=ParseResponse)
async def parse_documents(files: list[UploadFile] = File(...)) -> ParseResponse:
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
        documents.append(document)

    return ParseResponse(documents=documents)
