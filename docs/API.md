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
