# MaterialRAG

MaterialRAG 是材料科學文獻資料擷取工具的前端原型。目前提供三個操作步驟：設定擷取欄位、選擇 PDF，以及檢視並匯出比較表。

> 目前 PDF 尚未送往後端解析，結果頁使用示範資料。下一階段將建立 PDF 上傳與逐頁解析 API。

## 環境需求

- Node.js 20.19 以上，或 22.12 以上
- npm 10 以上
- Miniconda 或 Anaconda

## 本機啟動

### Windows 命令提示字元（CMD）

```bat
npm.cmd ci
copy .env.example .env.local
npm.cmd run dev
```

### PowerShell

```powershell
npm.cmd ci
Copy-Item .env.example .env.local
npm.cmd run dev
```

開啟終端顯示的本機網址即可使用。`.env.local` 不會被提交至版本控制。

## 啟動 PDF 解析服務

第一次設定後端時，在 Anaconda Prompt 或已啟用 Conda 的終端執行：

```bat
conda env create -f environment.yml
conda activate materialrag
```

若 `environment.yml` 日後有更新，可執行 `conda env update -n materialrag -f environment.yml --prune` 同步套件。

之後開啟第一個 CMD 視窗啟動後端：

```bat
conda activate materialrag
python -m uvicorn backend.main:app --reload --port 8000 --env-file .env.local
```

正式建置前端後，FastAPI 會直接提供 `dist` 內容，因此只需開啟
`http://localhost:8000`，不需要另外啟動 Vite。可使用
`MATERIALRAG_FRONTEND_PATH` 指定其他前端成品目錄。

也可以使用整合啟動入口；若 8000 已被占用，程式會自動嘗試下一個連接埠：

```bat
conda activate materialrag
python -m backend.launcher
```

若不希望自動開啟瀏覽器，可加上 `--no-browser`。

再開啟第二個 CMD 視窗啟動前端：

```bat
npm.cmd run dev
```

前端位於 `http://localhost:5173`，後端健康檢查位於 `http://localhost:8000/api/health`。上傳上限為每次 10 份 PDF、每份 20 MB。這一階段只解析 PDF 內嵌文字；掃描文件會標示為可能需要 OCR。

第一次按下「解析並建立索引」時，Sentence Transformers 會下載 `BAAI/bge-m3` 模型；所需時間與空間取決於模型快取狀態。之後模型會直接由本機快取載入。ChromaDB 索引預設保存在 `data/chroma`，此資料夾不會提交至 Git。

建立索引後，可在結果頁的「檢索驗證」輸入問題並查看 Top-5 內容、相似度、來源文件與頁碼。目前此功能只驗證證據檢索，尚未呼叫 LLM 生成答案。

解析 PDF 時會優先讀取文件 metadata 的標題；若 metadata 缺失或只是檔名，則從首頁文字推定。文獻標題會固定顯示為比較表與 CSV 的第一個資料欄位，不會額外消耗 LLM API 用量。

若要使用「自動擷取欄位」，建議在 `.env.local` 設定 Gemini API：

```text
LLM_PROVIDER=gemini
GEMINI_API_KEY=你的 Google AI Studio API 金鑰
GEMINI_EXTRACTION_MODEL=gemini-3.5-flash
```

也可切回 OpenAI：

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=你的 OpenAI Platform API 金鑰
OPENAI_EXTRACTION_MODEL=你的帳戶可用模型
```

API 金鑰屬於後端設定，請勿加上 `VITE_` 前綴。欄位擷取會針對每份文件逐欄檢索證據，再要求模型回傳結構化結果；沒有有效來源引用的值會被捨棄。雲端 API 的額度與網頁版登入或訂閱分開。

## 品質檢查

```powershell
npm.cmd test
npm.cmd run build
conda run -n materialrag python -m unittest discover -s backend\tests -v
```

測試會檢查 CSV 內容與特殊字元處理；正式建置則同時驗證 React 程式可被 Vite 正確編譯。

## 專案結構

```text
src/main.jsx       操作流程與畫面元件
src/styles.css     畫面樣式
src/csv.js         CSV 序列化與下載
test/              自動測試
backend/           PDF 解析 API 與後端測試
```

## 環境變數

| 名稱 | 用途 | 預設開發值 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | 後續 PDF API 的基底網址 | `http://localhost:8000` |
| `FRONTEND_ORIGIN` | 允許呼叫後端的前端來源 | `http://localhost:5173` |
| `MATERIALRAG_INDEX_PATH` | ChromaDB 持久化路徑 | `data/chroma` |
| `MATERIALRAG_EMBEDDING_MODEL` | Sentence Transformers 模型 | `BAAI/bge-m3` |
| `MATERIALRAG_EMBEDDING_BATCH_SIZE` | 每次送入向量模型的 chunks 數量；GPU 記憶體足夠時可提高 | `32` |
| `MATERIALRAG_UPSERT_BATCH_SIZE` | 每批向量化並寫入 ChromaDB 的 chunks 數量 | `256` |
| `LLM_PROVIDER` | 欄位擷取服務 | `gemini` |
| `GEMINI_API_KEY` | Google AI Studio API 金鑰 | 無 |
| `GEMINI_EXTRACTION_MODEL` | Gemini 結構化擷取模型 | `gemini-3.5-flash` |
| `OPENAI_API_KEY` | 可選的 OpenAI API 金鑰 | 無 |
| `OPENAI_EXTRACTION_MODEL` | 可選的 OpenAI 擷取模型 | `gpt-5.6-luna` |

請勿將 API 金鑰放在 `VITE_` 開頭的變數中；這類變數會被打包到瀏覽器端。模型金鑰將由後端環境管理。
