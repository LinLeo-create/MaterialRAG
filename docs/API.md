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
      "pages": [
        {
          "page_number": 1,
          "text": "Extracted page text...",
          "character_count": 620
        }
      ]
    }
  ]
}
```

錯誤狀態：

- `413`：檔案超過 20 MB。
- `415`：副檔名不是 PDF。
- `422`：內容並非有效 PDF、PDF 損壞，或受密碼保護。
