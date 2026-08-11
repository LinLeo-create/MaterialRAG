const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export async function parseDocuments(files) {
  const body = new FormData();
  files.forEach((file) => body.append("files", file));

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/documents/parse`, {
      method: "POST",
      body,
    });
  } catch {
    throw new Error("無法連線到 PDF 解析服務，請確認後端已啟動。");
  }

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "PDF 解析失敗，請稍後再試。");
  }
  return payload.documents;
}
