import { useEffect, useRef, useState } from "react";
import { streamChat } from "../api";
import type { Messages } from "../i18n";
import { splitCitations } from "../sse";
import type { ChatMessage, Citation, DocumentInfo, EngineSettings } from "../types";

interface Props {
  t: Messages;
  doc: DocumentInfo | null;
  engine: EngineSettings;
}

let counter = 0;
const nextId = () => `m${++counter}`;

export function Chat({ t, doc, engine }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatId, setChatId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [focus, setFocus] = useState<{ messageId: string; n: number } | null>(null);
  const abort = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  useEffect(() => () => abort.current?.abort(), []);

  if (!doc) {
    return (
      <>
        <main className="chat empty-state">
          <p>{t.pickDoc}</p>
        </main>
        <aside className="sources">
          <h2>{t.sources}</h2>
          <p className="empty">{t.noSources}</p>
        </aside>
      </>
    );
  }

  const lastAnswer = [...messages].reverse().find((m) => m.role === "assistant" && m.citations?.length);
  const sourceOwner = focus ? messages.find((m) => m.id === focus.messageId) : lastAnswer;

  function patch(id: string, change: (m: ChatMessage) => ChatMessage) {
    setMessages((all) => all.map((m) => (m.id === id ? change(m) : m)));
  }

  async function send() {
    const question = input.trim();
    if (!question || busy || !doc) return;
    const answerId = nextId();
    setInput("");
    setBusy(true);
    setFocus(null);
    setMessages((all) => [
      ...all,
      { id: nextId(), role: "user", content: question },
      { id: answerId, role: "assistant", content: "" },
    ]);
    abort.current = new AbortController();
    try {
      await streamChat(
        { documentId: doc.id, chatId, message: question },
        engine,
        {
          onMeta: (id, citations) => {
            setChatId(id);
            patch(answerId, (m) => ({ ...m, citations }));
          },
          onDelta: (text) => patch(answerId, (m) => ({ ...m, content: m.content + text })),
          onDone: () => undefined,
          onError: (message) => patch(answerId, (m) => ({ ...m, content: message, error: true })),
        },
        abort.current.signal,
      );
    } catch (e) {
      if ((e as Error).name === "AbortError") patch(answerId, (m) => ({ ...m, content: m.content || t.stopped }));
      else patch(answerId, (m) => ({ ...m, content: (e as Error).message, error: true }));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <main className="chat">
        <div className="messages" aria-live="polite">
          {messages.map((m) => (
            <div key={m.id} className={`msg ${m.role} ${m.error ? "error" : ""}`}>
              {m.role === "assistant" && !m.error ? (
                <Answer message={m} onCite={(n) => setFocus({ messageId: m.id, n })} />
              ) : (
                m.content
              )}
              {m.role === "assistant" && !m.content && busy && <span className="dots" aria-hidden="true" />}
            </div>
          ))}
          <div ref={bottom} />
        </div>
        <form
          className="composer"
          onSubmit={(e) => {
            e.preventDefault();
            void send();
          }}
        >
          <input value={input} onChange={(e) => setInput(e.target.value)} placeholder={t.ask} aria-label={t.ask} />
          {busy ? (
            <button type="button" onClick={() => abort.current?.abort()}>
              {t.stop}
            </button>
          ) : (
            <button disabled={!input.trim()}>{t.send}</button>
          )}
        </form>
      </main>

      <aside className="sources">
        <h2>{t.sources}</h2>
        {sourceOwner?.citations?.length ? (
          <ol>
            {sourceOwner.citations.map((c, i) => (
              <Source key={c.chunk_id} t={t} citation={c} n={i + 1} active={focus?.n === i + 1} />
            ))}
          </ol>
        ) : (
          <p className="empty">{t.noSources}</p>
        )}
      </aside>
    </>
  );
}

function Answer({ message, onCite }: { message: ChatMessage; onCite: (n: number) => void }) {
  const max = message.citations?.length ?? 0;
  return (
    <>
      {splitCitations(message.content).map((part, i) =>
        typeof part === "string" ? (
          <span key={i}>{part}</span>
        ) : part.n >= 1 && part.n <= max ? (
          <button key={i} className="cite" onClick={() => onCite(part.n)} aria-label={`Source ${part.n}`}>
            {part.n}
          </button>
        ) : (
          <span key={i}>[{part.n}]</span>
        ),
      )}
    </>
  );
}

function Source({ t, citation, n, active }: { t: Messages; citation: Citation; n: number; active: boolean }) {
  const ref = useRef<HTMLLIElement>(null);
  useEffect(() => {
    if (active) ref.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [active]);
  return (
    <li ref={ref} className={`source ${active ? "active" : ""}`}>
      <div className="source-head">
        <span className="cite static">{n}</span>
        {citation.page ? <span>{t.page} {citation.page}</span> : null}
        <span className="relevance" title={`${t.relevance} ${Math.round(citation.score * 100)}%`}>
          <i style={{ width: `${Math.round(citation.score * 100)}%` }} />
        </span>
      </div>
      <p>{citation.snippet}</p>
    </li>
  );
}
