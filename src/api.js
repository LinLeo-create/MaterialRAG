const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export async function indexDocuments(files) {
  const body = new FormData();
  files.forEach((file) => body.append("files", file));

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/documents/index`, {
      method: "POST",
      body,
    });
  } catch {
    throw new Error("無法連線到索引服務，請確認後端已啟動。");
  }

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "PDF 索引失敗，請稍後再試。");
  }
  return payload.documents;
}

export async function searchDocuments(query, topK = 5, documentIds = null) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/retrieval/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: topK, document_ids: documentIds }),
    });
  } catch {
    throw new Error("無法連線到檢索服務，請確認後端已啟動。");
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "檢索失敗，請稍後再試。");
  }
  return payload.results;
}

export async function extractFields(documentIds, fields, topK = 5) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/extraction/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_ids: documentIds, fields, top_k: topK }),
    });
  } catch {
    throw new Error("無法連線到欄位擷取服務，請確認後端已啟動。");
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "欄位擷取失敗，請稍後再試。");
  }
  return payload.documents;
}

export async function getExtractionStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/extraction/status`);
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}
