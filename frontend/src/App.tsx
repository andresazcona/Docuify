import { useCallback, useEffect, useState } from "react";
import { deleteDocument, listDocuments } from "./api";
import { Chat } from "./components/Chat";
import { Settings } from "./components/Settings";
import { Sidebar } from "./components/Sidebar";
import { detectLang, messages, type Lang } from "./i18n";
import type { DocumentInfo, EngineSettings } from "./types";

const ENGINE_KEY = "docuify.engine";

function loadEngine(): EngineSettings {
  try {
    const saved = JSON.parse(sessionStorage.getItem(ENGINE_KEY) ?? "null");
    if (saved?.engine) return saved;
  } catch {
    /* sessionStorage can be blocked; fall through to the default */
  }
  return { engine: "extractive", apiKey: "", model: "" };
}

export function App() {
  const [lang, setLang] = useState<Lang>(detectLang);
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [engine, setEngine] = useState<EngineSettings>(loadEngine);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const t = messages[lang];

  const refresh = useCallback(async () => {
    const next = await listDocuments();
    setDocs(next);
    setSelectedId((current) => (current && next.some((d) => d.id === current) ? current : null));
  }, []);

  useEffect(() => {
    refresh().catch(() => setDocs([]));
  }, [refresh]);

  useEffect(() => {
    localStorage.setItem("docuify.lang", lang);
    document.documentElement.lang = lang;
  }, [lang]);

  useEffect(() => {
    try {
      sessionStorage.setItem(ENGINE_KEY, JSON.stringify(engine));
    } catch {
      /* ignore */
    }
  }, [engine]);

  const selected = docs.find((d) => d.id === selectedId) ?? null;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo" aria-hidden="true" />
          <div>
            <h1>Docuify</h1>
            <p>{t.tagline}</p>
          </div>
        </div>
        <div className="topbar-actions">
          <button className="ghost" onClick={() => setSettingsOpen(true)}>
            {t.settings}: <strong>{engine.engine === "extractive" ? "extractive" : engine.engine}</strong>
          </button>
          <button className="ghost" onClick={() => setLang(lang === "es" ? "en" : "es")} aria-label="Language">
            {lang === "es" ? "EN" : "ES"}
          </button>
        </div>
      </header>

      <Sidebar
        t={t}
        docs={docs}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onChanged={async (focusId) => {
          await refresh();
          if (focusId) setSelectedId(focusId);
        }}
        onDelete={async (id) => {
          await deleteDocument(id);
          await refresh();
        }}
      />

      <Chat key={selected?.id ?? "none"} t={t} doc={selected} engine={engine} />

      {settingsOpen && (
        <Settings t={t} value={engine} onChange={setEngine} onClose={() => setSettingsOpen(false)} />
      )}
    </div>
  );
}
