import { useCallback, useEffect, useState } from "react";
import { deleteDocument, listDocuments } from "./api";
import { Chat } from "./components/Chat";
import { Logo, MenuIcon, MoonIcon, SunIcon } from "./components/icons";
import { Settings } from "./components/Settings";
import { Sidebar } from "./components/Sidebar";
import { Welcome } from "./components/Welcome";
import { detectLang, messages, type Lang } from "./i18n";
import type { DocumentInfo, EngineSettings } from "./types";

const ENGINE_KEY = "folio.engine";
type Theme = "light" | "dark";

function loadEngine(): EngineSettings {
  try {
    const saved = JSON.parse(sessionStorage.getItem(ENGINE_KEY) ?? "null");
    if (saved?.engine) return saved;
  } catch {
    /* sessionStorage can be blocked; fall through to the default */
  }
  return { engine: "extractive", apiKey: "", model: "" };
}

function detectTheme(): Theme {
  try {
    const saved = localStorage.getItem("folio.theme");
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    /* blocked storage: follow the system */
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function App() {
  const [lang, setLang] = useState<Lang>(detectLang);
  const [theme, setTheme] = useState<Theme>(detectTheme);
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [engine, setEngine] = useState<EngineSettings>(loadEngine);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const t = messages[lang];

  const refresh = useCallback(async () => {
    const next = await listDocuments();
    setDocs(next);
    setSelectedId((current) => (current && next.some((d) => d.id === current) ? current : null));
  }, []);

  useEffect(() => {
    refresh().catch(() => setDocs([]));
  }, [refresh]);

  // Documents still being processed: poll until they settle.
  const pending = docs.some((d) => d.status !== "READY" && d.status !== "FAILED");
  useEffect(() => {
    if (!pending) return;
    const timer = setInterval(() => refresh().catch(() => undefined), 2000);
    return () => clearInterval(timer);
  }, [pending, refresh]);

  useEffect(() => {
    localStorage.setItem("folio.lang", lang);
    document.documentElement.lang = lang;
  }, [lang]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("folio.theme", theme);
    } catch {
      /* ignore */
    }
  }, [theme]);

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
          <button className="icon-btn nav-toggle" onClick={() => setNavOpen(!navOpen)} aria-label={t.library}>
            <MenuIcon />
          </button>
          <Logo />
          <div>
            <h1>Folio</h1>
            <p>{t.tagline}</p>
          </div>
        </div>
        <div className="topbar-actions">
          <button className="chip" onClick={() => setSettingsOpen(true)} title={t.settings}>
            <span className={`dot ${engine.engine}`} aria-hidden="true" />
            {t.engineShort[engine.engine]}
          </button>
          <button className="icon-btn" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label={t.theme}>
            {theme === "dark" ? <SunIcon /> : <MoonIcon />}
          </button>
          <button className="icon-btn lang" onClick={() => setLang(lang === "es" ? "en" : "es")} aria-label="Language">
            {lang === "es" ? "EN" : "ES"}
          </button>
        </div>
      </header>

      <Sidebar
        t={t}
        open={navOpen}
        docs={docs}
        selectedId={selectedId}
        onSelect={(id) => {
          setSelectedId(id);
          setNavOpen(false);
        }}
        onChanged={async (focusId) => {
          await refresh();
          if (focusId) {
            setSelectedId(focusId);
            setNavOpen(false);
          }
        }}
        onDelete={async (id) => {
          await deleteDocument(id);
          await refresh();
        }}
      />
      {navOpen && <button className="scrim" aria-label={t.close} onClick={() => setNavOpen(false)} />}

      {selected ? (
        <Chat key={selected.id} t={t} doc={selected} engine={engine} />
      ) : (
        <Welcome t={t} hasDocs={docs.length > 0} />
      )}

      {settingsOpen && (
        <Settings t={t} value={engine} onChange={setEngine} onClose={() => setSettingsOpen(false)} />
      )}
    </div>
  );
}
