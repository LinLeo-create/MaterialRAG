# MaterialRAG

MaterialRAG 是面向材料科學文獻的本機 RAG 工具。使用者可逐份解析 PDF、建立向量索引、指定比較欄位，並透過 Gemini 或 OpenAI 從檢索證據中產生帶有來源頁碼的結構化結果。

## 主要功能

- 逐份解析 PDF，顯示等待中、解析中、已完成及失敗狀態。
- 保留 PDF 頁碼，將文字切分後寫入本機 ChromaDB。
- 使用 `BAAI/bge-m3` 建立多語言 Embedding。
- 搜尋 Top-K 證據，顯示相似度、文件、頁碼及原文。
- 使用 Gemini 或 OpenAI 擷取指定欄位；無有效引用的結果會被捨棄。
- 匯出材料文獻比較表 CSV。
- 提供可獨立執行的 Windows 發行包。

目前只解析 PDF 內嵌文字。純掃描 PDF 尚未執行 OCR，介面會將其標示為可能需要 OCR。

## 使用 Windows 發行包

1. 下載並完整解壓 `MaterialRAG-1.0.0-windows-x64.zip`。
2. 保留 `MaterialRAG.exe` 與 `_internal` 資料夾的相對位置。
3. 雙擊 `MaterialRAG.exe`。
4. 等待瀏覽器自動開啟；若沒有開啟，請使用命令視窗顯示的網址。
5. 第一次建立索引時保持網路連線，程式需要下載 Embedding 模型。

Windows 成品不需要另外安裝 Python、Conda 或 Node.js。

## 申請 Gemini API Key

MaterialRAG 使用 Gemini 執行「自動擷取欄位」。PDF 解析、向量索引及檢索驗證不需要 Gemini API Key。

1. 前往 [Google AI Studio](https://aistudio.google.com/)，登入 Google 帳戶並接受相關服務條款。
2. 開啟 [API Keys](https://aistudio.google.com/app/apikey) 頁面。
3. 新使用者通常會看到預設專案與金鑰；若沒有，選擇 **Create API key**，並建立或選取 Google Cloud 專案。
4. 複製新金鑰並妥善保存。不要將金鑰貼到 GitHub、聊天訊息或前端程式碼。
5. 如使用舊的 unrestricted standard key，請依 [Google 官方 API Key 指南](https://ai.google.dev/gemini-api/docs/api-key) 改用新金鑰，或將金鑰限制為僅供 Gemini API 使用。
6. 免費層、速率限制與可用模型會依地區及帳戶而異；使用前可查看 [Gemini API 計費說明](https://ai.google.dev/gemini-api/docs/billing)。

### 在 Windows 成品中設定

啟動 MaterialRAG 後，在 Gemini 設定區貼上 API Key 並儲存。金鑰會透過 Windows DPAPI 加密，保存在目前 Windows 使用者的本機設定中，不會寫入 exe 或 ZIP。

### 在開發環境中設定

複製 `.env.example` 為 `.env.local`，再填入：

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=你的_Gemini_API_Key
GEMINI_EXTRACTION_MODEL=gemini-3.5-flash
```

API Key 是後端機密，不可使用 `VITE_` 前綴；所有 `VITE_` 變數都可能被編譯到瀏覽器端。

## 開發環境需求

- Windows 10／11 64 位元
- Node.js 20.19 以上或 22.12 以上
- npm 10 以上
- Miniconda 或 Anaconda

本專案以 Conda `materialrag` 環境為標準，不使用根目錄 `.venv`。

## 第一次安裝

在 Anaconda Prompt 或已啟用 Conda 的終端執行：

```bat
conda env create -f environment.yml
conda activate materialrag
npm.cmd ci
copy .env.example .env.local
```

PowerShell 複製設定檔的寫法：

```powershell
Copy-Item .env.example .env.local
```

若 Conda 環境已存在，可同步更新：

```bat
conda env update -n materialrag -f environment.yml --prune
```

`.env.local` 包含本機設定與可能的 API Key，已由 Git 忽略。

## 啟動開發環境

開啟第一個終端啟動後端：

```bat
conda activate materialrag
python -m uvicorn backend.main:app --reload --port 8000 --env-file .env.local
```

開啟第二個終端啟動前端：

```bat
npm.cmd run dev
```

- 前端：`http://localhost:5173`
- 後端健康檢查：`http://localhost:8000/api/health`

也可以先建立前端，再使用整合入口由 FastAPI 同時提供前後端：

```bat
npm.cmd run build
conda activate materialrag
python -m backend.launcher
```

若 8000 已被占用，啟動器會嘗試下一個連接埠。使用 `--no-browser` 可禁止自動開啟瀏覽器。

## 使用限制與資料流程

- 每次最多上傳 10 份 PDF。
- 每份 PDF 上限為 20 MB。
- PDF 依清單順序逐份解析；單份失敗不會阻止後續文件。
- 文字預設以 1,000 字元切分，重疊 150 字元，而且不跨頁。
- 相同 PDF 以 SHA-256 辨識，不會建立重複索引。
- `BAAI/bge-m3` 在第一次索引時下載，之後使用本機快取。
- LLM 只接收檢索出的文字證據，不會接收整個 ChromaDB。
- 雲端 API 額度與 Gemini 網頁版或 Google One 訂閱分開計算。

## 使用者資料與安全

Windows 成品的資料預設保存在：

```text
%LOCALAPPDATA%\MaterialRAG
├── data\chroma    ChromaDB 索引
├── models         Hugging Face／Embedding 模型快取
└── gemini.json    由 Windows DPAPI 加密的 Gemini 設定
```

可用 `MATERIALRAG_DATA_ROOT` 指定其他資料根目錄。移除程式不會自動刪除上述資料；若要完整清除，可在關閉 MaterialRAG 後手動刪除該資料夾。

## 測試與品質檢查

```bat
npm.cmd test
npm.cmd run build
conda run -n materialrag python -m unittest discover -s backend\tests -v
```

測試涵蓋 PDF 解析、切塊、索引、搜尋、引用驗證、Gemini 結構化回應、啟動器與 CSV 處理。

## 建立 Windows 成品

安裝建置工具：

```bat
conda activate materialrag
python -m pip install -r requirements-build.txt
```

建立未壓縮成品：

```bat
powershell -ExecutionPolicy Bypass -File build_windows.ps1
```

成品位於 `dist\MaterialRAG`。建立 ZIP 發行包：

```bat
powershell -ExecutionPolicy Bypass -File package_windows.ps1
```

ZIP 位於 `release` 目錄。Embedding 模型、索引、`.env.local` 及 API Key 都不會被打包。

## 專案結構

```text
backend/                  FastAPI、PDF 解析、向量索引與 LLM 擷取
backend/tests/            後端單元測試
src/                      React 前端
test/                     前端／CSV 測試
docs/                     API 文件
MaterialRAG.spec          PyInstaller 設定
build_windows.ps1         Windows 成品建置腳本
package_windows.ps1       ZIP 發行腳本
environment.yml           Conda 環境
```

## 環境變數

| 名稱 | 用途 | 預設值 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | 開發前端呼叫的 API 網址 | `http://localhost:8000` |
| `FRONTEND_ORIGIN` | 後端允許的開發前端來源 | `http://localhost:5173` |
| `MATERIALRAG_DATA_ROOT` | Windows 成品的模型、索引資料根目錄 | `%LOCALAPPDATA%\MaterialRAG` |
| `MATERIALRAG_FRONTEND_PATH` | FastAPI 提供的前端成品目錄 | `dist` |
| `MATERIALRAG_INDEX_PATH` | ChromaDB 索引路徑 | 開發環境為 `data/chroma` |
| `MATERIALRAG_EMBEDDING_MODEL` | Sentence Transformers 模型 | `BAAI/bge-m3` |
| `MATERIALRAG_EMBEDDING_BATCH_SIZE` | 模型推論批次大小 | `32` |
| `MATERIALRAG_UPSERT_BATCH_SIZE` | ChromaDB 寫入批次大小 | `256` |
| `MATERIALRAG_PORT` | 整合啟動器優先使用的連接埠 | `8000` |
| `LLM_PROVIDER` | 欄位擷取服務：`gemini` 或 `openai` | `gemini` |
| `GEMINI_API_KEY` | Gemini API Key | 無 |
| `GEMINI_EXTRACTION_MODEL` | Gemini 擷取模型 | `gemini-3.5-flash` |
| `OPENAI_API_KEY` | 可選的 OpenAI API Key | 無 |
| `OPENAI_EXTRACTION_MODEL` | 可選的 OpenAI 擷取模型 | `gpt-5.6-luna` |

## 常見問題

### 第一次建立索引看起來很久

第一次需要下載並載入 `BAAI/bge-m3`。後續會使用本機模型快取；介面也會逐份顯示 PDF 的處理狀態。

### PDF 顯示沒有可擷取文字

文件可能是掃描影像或受密碼保護。目前版本尚未提供 OCR，請改用含文字層的 PDF。

### Gemini 回傳 401、403 或權限錯誤

確認 API Key 已完整貼上、Google AI Studio 條款已接受、所在區域受支援，且金鑰所屬專案有權使用 Gemini API。公司／學校 Workspace 帳戶也可能受到管理員政策限制。

### Gemini 回傳 404 或模型不存在

模型可用性可能依帳戶與地區不同。請在 Google AI Studio 確認可用模型，並修改 `GEMINI_EXTRACTION_MODEL` 後重新啟動後端。

### 出現 429

代表目前已達速率或額度限制。請稍後重試，或在 Google AI Studio 的 Usage／Billing 頁面檢查用量與方案。
