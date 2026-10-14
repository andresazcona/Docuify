import { readSSE } from "./sse";
import type { Citation, DocumentInfo, EngineSettings } from "./types";

const BASE = "/api/v1";

async function failure(res: Response): Promise<Error> {
  try {
    const body = await res.json();
    return new Error(body.message ?? body.detail ?? res.statusText);
  } catch {
    return new Error(res.statusText || `HTTP ${res.status}`);
  }
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw await failure(res);
  return res.json() as Promise<T>;
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  const body = await json<{ documents: DocumentInfo[] }>(await fetch(`${BASE}/documents?limit=100`));
  return body.documents;
}

export async function uploadDocument(file: File): Promise<void> {
  const form = new FormData();
  form.append("file", file);
  await json(await fetch(`${BASE}/documents/upload`, { method: "POST", body: form }));
}

/** arXiv links are resolved by the API; any other URL must point straight at a PDF. */
export async function addByUrl(raw: string): Promise<void> {
  const url = new URL(raw.trim());
  const isArxiv = /(^|\.)arxiv\.org$/.test(url.hostname);
  const path = isArxiv ? "arxiv" : "url";
  const body = isArxiv ? { arxiv_url: url.href } : { pdf_url: url.href };
  await json(
    await fetch(`${BASE}/documents/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  );
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await fetch(`${BASE}/documents/${id}`, { method: "DELETE" });
  if (!res.ok) throw await failure(res);
}

export interface StreamHandlers {
  onMeta: (chatId: string, citations: Citation[]) => void;
  onDelta: (text: string) => void;
  onDone: () => void;
  onError: (message: string) => void;
}

/** Ask a question and stream the answer. The key, if any, is sent only to the Docuify API. */
export async function streamChat(
  req: { documentId: string; chatId: string | null; message: string },
  engine: EngineSettings,
  handlers: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (engine.engine !== "extractive" && engine.apiKey) {
    headers["X-LLM-Provider"] = engine.engine;
    headers["X-LLM-Key"] = engine.apiKey;
    if (engine.model.trim()) headers["X-LLM-Model"] = engine.model.trim();
  }
  const res = await fetch(`${BASE}/chats/chat/stream`, {
    method: "POST",
    headers,
    signal,
    body: JSON.stringify({
      document_id: req.documentId,
      chat_id: req.chatId,
      message: req.message,
    }),
  });
  if (!res.ok || !res.body) {
    handlers.onError((await failure(res)).message);
    return;
  }
  for await (const { event, data } of readSSE(res.body)) {
    if (event === "meta") handlers.onMeta(data.chat_id, data.citations);
    else if (event === "delta") handlers.onDelta(data.text);
    else if (event === "done") handlers.onDone();
    else if (event === "error") handlers.onError(data.message);
  }
}
