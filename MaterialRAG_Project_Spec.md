# 固態材料論文 AI 數據自動擷取與分析助手 (MaterialRAG)
> **暑期專題實作計畫與技術架構文件**  
> *Dedicated AI-Driven Literature Processing System for Solid-State Physics & Materials Science*

---

## 📌 專案簡介 (Project Overview)

在固態物理與材料科學領域，研讀大量文獻並從中萃取實驗參數（如燒結溫度、退火時間、摻雜比例、帶隙 Bandgap、電導率等）是極度耗時且容易出錯的工作。傳統泛用型 LLM（如 ChatGPT）在處理此類需求時，常遇到**數據幻覺 (Hallucination)**、**論文長度限制**以及**無法處理 PDF 表格與精確溯源**等問題。

本專案旨在建構一個基於 **RAG（檢索增強生成，Retrieval-Augmented Generation）** 架構的材料文獻 AI 助手。研究人員只需上傳批量 PDF 論文，系統即可自動提取結構化數據、生成對比表格，並提供具備**原文頁碼與段落標註（Traceability）**的精準問答功能。

---

## ✨ 系統核心特點 (Key Features)

### 1. 零幻覺與精準溯源機制 (Zero-Hallucination & Traceability)
* **引用驗證 (Source Attribution)：** 每筆提煉出的數據（如 $E_g = 3.2\text{ eV}$）均附帶可點擊的引用標籤，直達 PDF 原始頁碼與高亮段落。
* **嚴謹基於文獻 (Strict RAG Constraint)：** 提示詞（Prompting）限制模型僅能根據檢索到的上下文（Context）回答，避免 LLM 自行推測數據。

### 2. 多模態文獻解析 (Multimodal Literature Parsing)
* **跨頁表格與文本解析：** 針對固態論文常見的複雜表格（包含下標、化學式、單位），採用專用 Parse 工具（如 `pdfplumber` / `unstructured`）進行結構化抽取。
* **材料化學式與單位識別：** 針對 $\text{YBa}_2\text{Cu}_3\text{O}_{7-\delta}$ 等複雜化學式與微米/奈米級單位進行特化 Text Splitting，避免切塊（Chunking）破壞語意。

### 3. 多文件對比與結構化輸出 (Multi-Doc Synthesis & Export)
* **自動生成材料特性矩陣 (Property Matrix)：** 自動將不同論文的「合成條件 vs. 材料性質」匯整為比較表格。
* **一鍵導出 CSV / JSON：** 提煉出的數據可直接導出，方便接續進行數據分析、繪圖或微調 machine learning 模型。

### 4. 低門檻與高效展示 (Ease of Use & Live Demo)
* **互動式 Web 介面：** 基於 Streamlit / Gradio，提供直觀的「檔案拖曳上傳 ➔ 數據自動擷取 ➔ 互動式對答 ➔ 表格導出」流程。
* **即時回應速度：** 結合高效向量檢索，單篇 PDF 分析平均少於 10 秒。

---

## 🛠️ 技術架構與實作方法 (Technical Architecture & Implementation)

### 1. 系統整體架構圖 (System Architecture)

```
[ PDF 論文文件庫 ]
       │
       ▼
[ 文獻解析與切塊 (PDF Parsing & Special Chunking) ]
  ├── 文本解析 (Recursive Character Text Splitter)
  └── 表格解析 (pdfplumber / LayoutPDFReader)
       │
       ▼
[ 向量化 (Embedding) ] -> (e.g., text-embedding-3-small / BGE-M3)
       │
       ▼
[ 向量資料庫 (Vector DB) ] -> (ChromaDB / FAISS)
       │
 ┌─────┴──────────────────────────┐
 │ 使用者提問 (User Query / Prompt)│
 └─────┬──────────────────────────┘
       ▼
[ 語意檢索 (Hybrid Retrieval + Reranking) ]
       │
       ▼ (撈出最相關 Top-K 數據段落 + 頁碼標記)
[ LLM 結構化生成 (Prompt Engineering) ] -> (GPT-4o-mini / Claude 3.5 Sonnet)
       │
       ▼
[ 前端展示與導出 (Streamlit UI / CSV Output) ]
```

---

### 2. 技術堆疊選型 (Technology Stack)

| 層級 (Layer) | 推薦技術 / 套件 | 說明與選型理由 |
| :--- | :--- | :--- |
| **前端 UI (Frontend)** | `Streamlit` / `Gradio` | 開發快速、支援 Markdown 與表格顯示，極適合暑期成果 Demo |
| **LLM 框架 (Framework)** | `LangChain` 或 `LlamaIndex` | 提供成熟的 RAG Pipeline、VectorStore 與 Document Loader API |
| **PDF 解析 (PDF Parsing)** | `pdfplumber` + `PyPDF` | 精準提取 PDF 內文與表格，保留座標與頁碼資訊 |
| **文本切塊 (Chunking)** | `RecursiveCharacterTextSplitter` | Chunk size ~ 500-1000, Overlap ~ 100-200，維護段落完整度 |
| **向量化 (Embedding)** | OpenAI `text-embedding-3-small` / HuggingFace `bge-m3` | 高維度語意特徵向量化，對學術論文詞義有極佳理解 |
| **向量庫 (Vector DB)** | `ChromaDB` / `FAISS` | 輕量級本地向量資料庫，免複雜部署即可快速上手 |
| **核心語言模型 (LLM)** | OpenAI `gpt-4o-mini` / `claude-3-5-sonnet` | 具備強大的 Structured Output (JSON Mode) 與邏輯推理能力 |

---

### 3. 核心實作步驟 (Step-by-Step Implementation)

#### Step 1: 文獻載入與專用切塊 (Document Processing)
1. 使用 `pdfplumber` 讀取 PDF，並記錄文字所處的 `page_number`。
2. 採用自訂的 Chunking 策略，依據學術論文章節（Introduction, Experimental, Results, Conclusion）與段落進行切割，確保「實驗條件」與「測量結果」留在同一個 Chunk 中。

#### Step 2: 建立向量索引 (Vector Indexing)
1. 將切塊後的文本與元數據（Metadata: `{filename, page_number}`）進行 Embedding。
2. 將向量存入本地 ChromaDB 向量庫中。

#### Step 3: Prompt 設計與檢索 (Retrieval & Structured Prompting)
1. 建立固態材料專用的 Prompt 範本，要求 LLM 回答必須遵循以下 JSON 格式或 Markdown 表格：
   ```json
   {
     "material_name": "材料名稱/化學式",
     "sintering_temperature": "燒結溫度 (°C)",
     "annealing_time": "退火時間 (hrs)",
     "bandgap": "帶隙 (eV)",
     "citation_page": "頁碼"
   }
   ```
2. 當使用者查詢特定材料或要求生成對比表時，向量庫撈出相關性最高的 Top-K 區塊注入 Prompt。

#### Step 4: UI 開發與成果呈現 (UI & Demo)
1. 左側欄：PDF 上傳與文件列表管理。
2. 主畫面：
   * **Tab 1: 論文問答與對映**（詢問具體問題，顯示答案與原文頁碼對照）。
   * **Tab 2: 數據總表 (Matrix View)**（一鍵匯總所有已上傳論文的實驗參數表格）。
   * **Tab 3: 導出功能**（匯出 CSV / JSON 檔案）。

---

## 📈 預期效益與展示亮點 (Expected Deliverables)

1. **大幅提升研讀效率：** 數據擷取速度提升 10 倍以上（從每篇 15 分鐘縮短至 10 秒內）。
2. **完全可追溯 (Traceable)：** 解決 LLM 幻覺，所有數據均可反查原文，符合科研嚴謹性要求。
3. **成果展示度高：** 成果發表會現場上傳未曾看過的最新固態論文，AI 現場在 10 秒內生成結構化參數表並提供可點擊的原文溯源標註。
