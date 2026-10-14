import { useRef, useState } from "react";
import { addByUrl, listDocuments, uploadDocument } from "../api";
import type { Messages } from "../i18n";
import type { DocumentInfo } from "../types";

interface Props {
  t: Messages;
  docs: DocumentInfo[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onChanged: (focusId?: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

function statusLabel(t: Messages, doc: DocumentInfo): string {
  if (doc.status === "READY") return t.ready;
  if (doc.status === "FAILED") return t.failed;
  return t.processing;
}

export function Sidebar({ t, docs, selectedId, onSelect, onChanged, onDelete }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drag, setDrag] = useState(false);
  const [url, setUrl] = useState("");
  const input = useRef<HTMLInputElement>(null);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      const before = new Set(docs.map((d) => d.id));
      await action();
      const after = await listDocuments();
      const created = after.find((d) => !before.has(d.id));
      await onChanged(created?.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <aside className="sidebar">
      <div
        className={`drop ${drag ? "over" : ""}`}
        role="button"
        tabIndex={0}
        onClick={() => input.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && input.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          const file = e.dataTransfer.files[0];
          if (file) run(() => uploadDocument(file));
        }}
      >
        {busy ? t.uploading : t.upload}
        <input
          ref={input}
          type="file"
          accept="application/pdf,.pdf"
          hidden
          onChange={(e) => {
            const file = e.target.files?.[0];
            e.target.value = "";
            if (file) run(() => uploadDocument(file));
          }}
        />
      </div>

      <form
        className="url-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (url.trim()) run(() => addByUrl(url).then(() => setUrl("")));
        }}
      >
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder={t.urlPlaceholder}
          aria-label={t.urlPlaceholder}
        />
        <button disabled={busy || !url.trim()}>{t.add}</button>
      </form>

      {error && <p className="error" role="alert">{error}</p>}

      {docs.length === 0 ? (
        <p className="empty">{t.noDocs}</p>
      ) : (
        <ul className="docs">
          {docs.map((doc) => (
            <li key={doc.id} className={doc.id === selectedId ? "active" : ""}>
              <button
                className="doc"
                disabled={doc.status !== "READY"}
                onClick={() => onSelect(doc.id)}
                title={doc.error_message ?? undefined}
              >
                <span className="doc-name">{doc.original_filename ?? doc.source_ref ?? doc.id}</span>
                <span className="doc-meta">
                  <span className={`badge ${doc.status.toLowerCase()}`}>{statusLabel(t, doc)}</span>
                  {doc.metadata?.pages ? `${doc.metadata.pages} ${t.pages}` : ""}
                </span>
              </button>
              <button
                className="remove"
                aria-label={`${t.remove} ${doc.original_filename ?? ""}`}
                onClick={() => onDelete(doc.id).catch((e) => setError(String(e.message ?? e)))}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
