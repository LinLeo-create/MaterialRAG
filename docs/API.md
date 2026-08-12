# MaterialRAG API v0.1

## 健康檢查

`GET /api/health`

```json
{"status": "ok"}
```

## 解析 PDF

`POST /api/documents/parse`

請求格式為 `multipart/form-data`，可重複使用 `files` 欄位上傳最多 10 份 PDF，每份上限 20 MB。

成功回應：

```json
{
  "documents": [
    {
      "filename": "paper.pdf",
      "page_count": 2,
      "character_count": 1200,
      "has_extractable_text": true,
      "chunk_count": 2,
      "pages": [
        {
          "page_number": 1,
          "text": "Extracted page text...",
          "character_count": 620
        }
      ],
      "chunks": [
        {
          "chunk_index": 0,
          "page_number": 1,
          "text": "Extracted page text prepared for retrieval...",
          "character_count": 620
        }
      ]
    }
  ]
}
```

每個 chunk 預設最多 1,000 字元、重疊 150 字元，並且不會跨越 PDF 頁面，以確保後續檢索結果可回溯到單一來源頁。

錯誤狀態：

- `413`：檔案超過 20 MB。
- `415`：副檔名不是 PDF。
- `422`：內容並非有效 PDF、PDF 損壞，或受密碼保護。

## 建立向量索引

`POST /api/documents/index`

請求格式與 PDF 解析端點相同。系統以檔案內容的 SHA-256 作為 `document_id`，相同內容重複上傳時會回傳 `unchanged`，不會建立重複 chunks。

```json
{
  "documents": [
    {
      "document_id": "a SHA-256 digest",
      "filename": "paper.pdf",
      "page_count": 2,
      "character_count": 1200,
      "has_extractable_text": true,
      "chunk_count": 2,
      "chunks": [],
      "status": "indexed"
    }
  ]
}
```

## 搜尋索引

`POST /api/retrieval/search`

```json
{
  "query": "ZnO 的退火溫度是多少？",
  "top_k": 5,
  "document_ids": ["optional-document-id"]
}
```

```json
{
  "results": [
    {
      "document_id": "a SHA-256 digest",
      "filename": "paper.pdf",
      "page_number": 4,
      "chunk_index": 8,
      "text": "The films were annealed at 500 °C...",
      "score": 0.87
    }
  ]
}
```

`score` 為由 cosine distance 轉換的 0–1 相似度。`document_ids` 省略時會搜尋整個 collection。

## 刪除文件索引

`DELETE /api/documents/{document_id}`

```json
{
  "document_id": "a SHA-256 digest",
  "deleted_chunks": 12
}
```

## 執行結構化欄位擷取

`POST /api/extraction/run`

```json
{
  "document_ids": ["a SHA-256 digest"],
  "fields": ["材料名稱", "退火溫度", "能隙"],
  "top_k": 5
}
```

每個欄位會先在指定文件內檢索證據，再交由 LLM 產生結構化結果。回傳的 evidence ID 必須存在於檢索結果，否則該值會被改為 `null`。

```json
{
  "documents": [
    {
      "document_id": "a SHA-256 digest",
      "filename": "paper.pdf",
      "fields": [
        {
          "field": "退火溫度",
          "value": "500",
          "unit": "°C",
          "confidence": "high",
          "citations": [
            {
              "filename": "paper.pdf",
              "page_number": 4,
              "chunk_index": 8,
              "text": "The films were annealed at 500 °C...",
              "score": 0.87
            }
          ]
        }
      ]
    }
  ]
}
```

- `502`：模型服務或結構化輸出失敗。
- `503`：目前選擇的 provider 尚未設定 API 金鑰。

實際 provider 由 `LLM_PROVIDER=openai|gemini` 決定。Gemini 使用 `GEMINI_API_KEY` 與 `GEMINI_EXTRACTION_MODEL`；OpenAI 使用對應的 `OPENAI_` 變數。

## 擷取服務狀態

`GET /api/extraction/status`

```json
{
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "configured": true
}
```

此端點只回傳是否已設定金鑰，不會回傳金鑰內容。
