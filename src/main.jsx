import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertCircle, ArrowLeft, ArrowRight, Check, Clock3, Download, FileText,
  FlaskConical, GripVertical, LoaderCircle, Plus, Search, Sparkles, Trash2,
  Upload, X
} from "lucide-react";
import "./styles.css";
import { downloadCsv } from "./csv.js";
import { extractFields, getExtractionStatus, indexDocuments, searchDocuments } from "./api.js";

const initialFields = ["材料名稱", "製程方法", "退火溫度", "能隙"];

function Header() {
  return (
    <header>
      <div className="logo"><FlaskConical size={19}/><span>MaterialRAG</span></div>
      <span className="project-name">新增 Benchmark</span>
    </header>
  );
}

function Stepper({ step }) {
  const steps = ["指定項目", "上傳文獻", "整理表格"];
  return (
    <div className="stepper">
      {steps.map((label, index) => {
        const number = index + 1;
        const done = step > number;
        return (
          <React.Fragment key={label}>
            <div className={`step ${step === number ? "active" : ""} ${done ? "done" : ""}`}>
              <span>{done ? <Check size={14}/> : number}</span>
              <b>{label}</b>
            </div>
            {index < 2 && <i className={step > number ? "filled" : ""}/>}
          </React.Fragment>
        );
      })}
    </div>
  );
}

function FieldStep({ fields, setFields, next }) {
  const [draft, setDraft] = useState("");
  const add = () => {
    const value = draft.trim();
    if (value && !fields.includes(value)) setFields([...fields, value]);
    setDraft("");
  };
  return (
    <section className="card field-step">
      <div className="intro">
        <span>步驟 1</span>
        <h1>你想比較哪些項目？</h1>
        <p>設定要從每篇文獻中擷取的欄位，之後仍可調整。</p>
      </div>
      <div className="field-list">
        {fields.map((field, index) => (
          <div className="field-row" key={`${field}-${index}`}>
            <GripVertical size={16}/>
            <span>{field}</span>
            <button aria-label="刪除欄位" onClick={() => setFields(fields.filter((_, i) => i !== index))}><X size={15}/></button>
          </div>
        ))}
      </div>
      <div className="add-field">
        <Plus size={16}/>
        <input value={draft} onChange={e => setDraft(e.target.value)} onKeyDown={e => e.key === "Enter" && add()} placeholder="新增項目，例如：電阻率"/>
        <button onClick={add}>加入</button>
      </div>
      <div className="examples">
        <span>常用項目</span>
        {["晶體結構", "退火時間", "摻雜濃度"].filter(x => !fields.includes(x)).map(x =>
          <button key={x} onClick={() => setFields([...fields, x])}>+ {x}</button>
        )}
      </div>
      <div className="actions"><button className="primary" disabled={!fields.length} onClick={next}>下一步<ArrowRight size={16}/></button></div>
    </section>
  );
}

function UploadStep({ files, setFiles, back, onParse }) {
  const inputRef = useRef();
  const [isParsing, setIsParsing] = useState(false);
  const [error, setError] = useState("");
  const [fileStatuses, setFileStatuses] = useState({});
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const addFiles = e => {
    const selected = [...e.target.files].filter(file => !files.some(f => f.name === file.name));
    setFiles([...files, ...selected]);
    setFileStatuses(statuses => ({
      ...statuses,
      ...Object.fromEntries(selected.map(file => [file.name, { state: "pending" }]))
    }));
    setError("");
    e.target.value = "";
  };
  const removeFile = index => {
    const filename = files[index].name;
    setFiles(files.filter((_, i) => i !== index));
    setFileStatuses(statuses => {
      const next = { ...statuses };
      delete next[filename];
      return next;
    });
  };
  const parse = async () => {
    setIsParsing(true);
    setError("");
    setProgress({ current: 0, total: files.length });
    setFileStatuses(Object.fromEntries(files.map(file => [file.name, { state: "pending" }])));
    const documents = [];
    const failures = [];

    for (const [index, file] of files.entries()) {
      setProgress({ current: index + 1, total: files.length });
      setFileStatuses(statuses => ({
        ...statuses,
        [file.name]: { state: "parsing" }
      }));
      try {
        const [document] = await indexDocuments([file]);
        documents.push(document);
        setFileStatuses(statuses => ({
          ...statuses,
          [file.name]: { state: "completed" }
        }));
      } catch (parseError) {
        failures.push(file.name);
        setFileStatuses(statuses => ({
          ...statuses,
          [file.name]: { state: "failed", message: parseError.message }
        }));
      }
    }

    if (failures.length === 0) {
      onParse(documents);
    } else {
      setError(`${failures.length} 份 PDF 解析失敗；可查看各檔案狀態後重新執行。`);
    }
    setIsParsing(false);
  };
  const statusView = file => {
    const status = fileStatuses[file.name]?.state || "pending";
    if (status === "parsing") return <span className="file-status parsing"><LoaderCircle size={13}/>解析中</span>;
    if (status === "completed") return <span className="file-status completed"><Check size={13}/>已完成</span>;
    if (status === "failed") return <span className="file-status failed" title={fileStatuses[file.name]?.message}><AlertCircle size={13}/>失敗</span>;
    return <span className="file-status pending"><Clock3 size={13}/>等待中</span>;
  };
  return (
    <section className="card upload-step">
      <div className="intro">
        <span>步驟 2</span>
        <h1>上傳研究文獻</h1>
        <p>加入要整理成 Benchmark 的 PDF 文件，系統會解析並建立本機索引。</p>
      </div>
      <input ref={inputRef} hidden type="file" accept=".pdf" multiple onChange={addFiles}/>
      <button className="dropzone" onClick={() => inputRef.current?.click()}>
        <div><Upload size={22}/></div>
        <b>選擇 PDF 文件</b>
        <span>支援一次上傳多份文獻</span>
      </button>
      {files.length > 0 && (
        <div className="file-list">
          <p>已選擇 {files.length} 份文獻</p>
          {files.map((file, index) => (
            <div className="file-row" key={file.name}>
              <FileText size={17}/>
              <div><b>{file.name}</b><span>{(file.size / 1048576).toFixed(1)} MB</span></div>
              {statusView(file)}
              <button disabled={isParsing} onClick={() => removeFile(index)}><Trash2 size={15}/></button>
            </div>
          ))}
        </div>
      )}
      {error && <div className="error-message" role="alert">{error}</div>}
      <div className="actions split">
        <button className="back" disabled={isParsing} onClick={back}><ArrowLeft size={16}/>上一步</button>
        <button className="primary" disabled={!files.length || isParsing} onClick={parse}>{isParsing ? `正在解析 ${progress.current}/${progress.total}` : "逐份解析並建立索引"}<Sparkles size={15}/></button>
      </div>
    </section>
  );
}

function RetrievalPanel({ documents }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState("");
  const search = async () => {
    const value = query.trim();
    if (!value) return;
    setIsSearching(true);
    setHasSearched(true);
    setError("");
    try {
      setResults(await searchDocuments(value, 5, documents.map(document => document.document_id)));
    } catch (searchError) {
      setError(searchError.message);
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };
  return (
    <section className="retrieval-panel">
      <div className="retrieval-heading"><div><b>檢索驗證</b><span>先確認正確證據能否被找到，再進行欄位擷取。</span></div></div>
      <div className="search-box">
        <Search size={16}/>
        <input value={query} onChange={event => setQuery(event.target.value)} onKeyDown={event => event.key === "Enter" && search()} placeholder="例如：ZnO 的退火溫度是多少？"/>
        <button disabled={!query.trim() || isSearching} onClick={search}>{isSearching ? "搜尋中…" : "搜尋 Top 5"}</button>
      </div>
      {error && <div className="error-message" role="alert">{error}</div>}
      {results.length > 0 && <div className="retrieval-results">{results.map((result, index) => (
        <article key={`${result.document_id}-${result.chunk_index}`}>
          <div><b>#{index + 1} · {result.filename}</b><span>第 {result.page_number} 頁 · Chunk {result.chunk_index + 1} · 相似度 {(result.score * 100).toFixed(1)}%</span></div>
          <p>{result.text}</p>
        </article>
      ))}</div>}
      {!isSearching && hasSearched && results.length === 0 && !error && <p className="no-results">索引中沒有相符內容。</p>}
    </section>
  );
}

function TableStep({ fields, documents, back }) {
  const [rows, setRows] = useState(() => {
    return documents.map(() => fields.map(() => "—"));
  });
  const [extractions, setExtractions] = useState([]);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState("");
  const [providerStatus, setProviderStatus] = useState(null);
  useEffect(() => {
    getExtractionStatus().then(setProviderStatus);
  }, []);
  const updateCell = (ri, ci, value) => setRows(rows.map((row, r) => r === ri ? row.map((cell, c) => c === ci ? value : cell) : row));
  const addRow = () => setRows([...rows, fields.map(() => "—")]);
  const exportCsv = () => {
    downloadCsv([
      ["文獻標題", ...fields],
      ...rows.map((row, index) => [documents[index]?.title || "—", ...row]),
    ]);
  };
  const runExtraction = async () => {
    setIsExtracting(true);
    setExtractionError("");
    try {
      const extractedDocuments = await extractFields(documents.map(document => document.document_id), fields);
      setExtractions(extractedDocuments);
      setRows(documents.map(document => {
        const extracted = extractedDocuments.find(item => item.document_id === document.document_id);
        return fields.map(field => {
          const result = extracted?.fields.find(item => item.field === field);
          return result?.value ? `${result.value}${result.unit ? ` ${result.unit}` : ""}` : "—";
        });
      }));
    } catch (extractError) {
      setExtractionError(extractError.message);
    } finally {
      setIsExtracting(false);
    }
  };
  return (
    <section className="table-page">
      <div className="table-heading">
        <div><span>步驟 3</span><h1>PDF 解析結果</h1><p>{documents.length} 份文獻 · {fields.length} 個待擷取欄位</p></div>
        <div className="heading-actions">
          <button className="extract" disabled={isExtracting} onClick={runExtraction}><Sparkles size={15}/>{isExtracting ? "正在擷取…" : "自動擷取欄位"}</button>
          <button className="export" onClick={exportCsv}><Download size={15}/>匯出 CSV</button>
        </div>
      </div>
      {extractionError && <div className="error-message table-error" role="alert">{extractionError}</div>}
      {providerStatus && <div className={`provider-status ${providerStatus.configured ? "provider-ready" : "provider-missing"}`}>
        LLM：{providerStatus.provider} · {providerStatus.model} · {providerStatus.configured ? "已設定" : "缺少 API 金鑰"}
      </div>}
      <div className="document-summary">
        {documents.map(document => (
          <div key={document.filename} className="document-summary-item">
            <div className="document-summary-row">
              <FileText size={16}/>
              <div><b>{document.title}</b><span>{document.filename} · {document.page_count} 頁 · {document.character_count.toLocaleString()} 個字元 · {document.chunk_count} 個 chunks</span></div>
              <span className={document.has_extractable_text ? "text-ready" : "text-missing"}>{document.has_extractable_text ? "文字已擷取" : "未偵測到文字，可能需要 OCR"}</span>
            </div>
            {document.chunks.length > 0 && (
              <details className="chunk-preview">
                <summary>檢視切分預覽</summary>
                {document.chunks.slice(0, 3).map(chunk => (
                  <div className="chunk-card" key={chunk.chunk_index}>
                    <span>Chunk {chunk.chunk_index + 1} · 第 {chunk.page_number} 頁 · {chunk.character_count} 字元</span>
                    <p>{chunk.text}</p>
                  </div>
                ))}
                {document.chunk_count > 3 && <small>目前顯示前 3 個，共 {document.chunk_count} 個 chunks。</small>}
              </details>
            )}
          </div>
        ))}
      </div>
      <RetrievalPanel documents={documents}/>
      <div className="table-card">
        <table>
          <thead><tr><th>#</th><th>文獻標題</th>{fields.map(field => <th key={field}>{field}</th>)}</tr></thead>
          <tbody>{rows.map((row, ri) => (
            <tr key={ri}><td>{ri + 1}</td><td className="title-cell">{documents[ri]?.title || "—"}</td>{row.map((cell, ci) =>
              <td key={ci}><input value={cell} onChange={e => updateCell(ri, ci, e.target.value)}/></td>
            )}</tr>
          ))}</tbody>
        </table>
        <button className="add-row" onClick={addRow}><Plus size={15}/>新增一列</button>
      </div>
      {extractions.length > 0 && <section className="citation-panel">
        <h2>擷取證據</h2>
        {extractions.map(document => (
          <details key={document.document_id}>
            <summary>{document.filename}</summary>
            {document.fields.map(field => (
              <div className="citation-field" key={field.field}>
                <b>{field.field}</b><span>{field.value ? `${field.value}${field.unit ? ` ${field.unit}` : ""}` : "未找到"} · {field.confidence}</span>
                {field.citations.map(citation => <blockquote key={`${citation.page_number}-${citation.chunk_index}`}><small>第 {citation.page_number} 頁 · 相似度 {(citation.score * 100).toFixed(1)}%</small>{citation.text}</blockquote>)}
              </div>
            ))}
          </details>
        ))}
      </section>}
      <div className="actions split table-actions">
        <button className="back" onClick={back}><ArrowLeft size={16}/>返回文獻</button>
        <span><Check size={14}/>表格內容可直接點擊修改</span>
      </div>
    </section>
  );
}

function App() {
  const [step, setStep] = useState(1);
  const [fields, setFields] = useState(initialFields);
  const [files, setFiles] = useState([]);
  const [documents, setDocuments] = useState([]);
  const finishParsing = parsedDocuments => {
    setDocuments(parsedDocuments);
    setStep(3);
  };
  return (
    <div className="app">
      <Header/>
      <main>
        <Stepper step={step}/>
        {step === 1 && <FieldStep fields={fields} setFields={setFields} next={() => setStep(2)}/>}
        {step === 2 && <UploadStep files={files} setFiles={setFiles} back={() => setStep(1)} onParse={finishParsing}/>}
        {step === 3 && <TableStep fields={fields} documents={documents} back={() => setStep(2)}/>}
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App/>);
