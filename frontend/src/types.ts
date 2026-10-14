export type DocStatus =
  | "CREATED"
  | "DOWNLOADING"
  | "UPLOADED"
  | "PROCESSING"
  | "CHUNKING"
  | "INDEXING"
  | "READY"
  | "FAILED";

export interface DocumentInfo {
  id: string;
  status: DocStatus;
  original_filename: string | null;
  source_ref: string | null;
  error_message: string | null;
  metadata: { pages?: number | null; chunks?: number | null; title?: string | null } | null;
  created_at: string;
}

export interface Citation {
  chunk_id: string;
  snippet: string;
  page: number | null;
  score: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[] | null;
  error?: boolean;
}

export type Engine = "extractive" | "anthropic" | "openai";

export interface EngineSettings {
  engine: Engine;
  apiKey: string;
  model: string;
}
