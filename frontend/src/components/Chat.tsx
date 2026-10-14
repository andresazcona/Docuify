import { Fragment, useEffect, useRef, useState } from "react";
import { streamChat } from "../api";
import { splitBold, toBlocks } from "../blocks";
import type { Messages } from "../i18n";
import { splitCitations } from "../sse";
import type { ChatMessage, Citation, DocumentInfo, EngineSettings } from "../types";
import { CloseIcon, FileIcon, Logo, QuoteIcon, SendIcon, StopIcon } from "./icons";

interface Props {
  t: Messages;
  doc: DocumentInfo;
  engine: EngineSettings;
}

let counter = 0;
const nextId = () => `m${++counter}`;

const docTitle = (doc: DocumentInfo) =>
  (doc.metadata?.title || doc.original_filename || doc.source_ref || doc.id).replace(/\.pdf$/i, "");

export function Chat({ t, doc, engine }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatId, setChatId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [focus, setFocus] = useState<{ messageId: string; n: number } | null>(null);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const abort = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  useEffect(() => () => abort.current?.abort(), []);

  const lastAnswer = [...messages].reverse().find((m) => m.role === "assistant" && m.citations?.length);
  const sourceOwner = focus ? messages.find((m) => m.id === focus.messageId) : lastAnswer;
  const citations = sourceOwner?.citations ?? [];

  function patch(id: string, change: (m: ChatMessage) => ChatMessage) {
    setMessages((all) => all.map((m) => (m.id === id ? change(m) : m)));
  }

  async function send(text = input) {
    const question = text.trim();
    if (!question || busy) return;
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
          onMeta: (id, cites) => {
            setChatId(id);
            patch(answerId, (m) => ({ ...m, citations: cites }));
          },
          onDelta: (delta) => patch(answerId, (m) => ({ ...m, content: m.content + delta })),
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
        <header className="doc-head">
          <span className="doc-icon big" aria-hidden="true">
            <FileIcon />
          </span>
          <div className="doc-head-text">
            <h2 title={docTitle(doc)}>{docTitle(doc)}</h2>
            <p>
              {doc.metadata?.pages ? `${doc.metadata.pages} ${t.pages}` : ""}
              {doc.metadata?.chunks ? ` · ${doc.metadata.chunks} ${t.passages}` : ""}
            </p>
          </div>
          <button className="chip sources-toggle" onClick={() => setSourcesOpen(true)}>
            <QuoteIcon />
            {t.openSources}
            {citations.length > 0 && <b>{citations.length}</b>}
          </button>
        </header>

        <div className="messages" aria-live="polite">
          {messages.length === 0 && (
            <div className="start">
              <Logo size={36} />
              <h3>{t.emptyChatTitle}</h3>
              <div className="suggestions">
                {t.suggestions.map((s) => (
                  <button key={s} onClick={() => void send(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m) =>
            m.role === "user" ? (
              <div key={m.id} className="turn user">
                <div className="bubble">{m.content}</div>
              </div>
            ) : (
              <div key={m.id} className={`turn assistant ${m.error ? "error" : ""}`}>
                <span className="avatar" aria-hidden="true">
                  <Logo size={26} />
                </span>
                <div className="answer">
                  {m.error ? (
                    m.content
                  ) : (
                    <Answer
                      message={m}
                      onCite={(n) => {
                        setFocus({ messageId: m.id, n });
                        setSourcesOpen(true);
                      }}
                    />
                  )}
                  {!m.content && busy && <span className="typing" aria-hidden="true"><i /><i /><i /></span>}
                </div>
              </div>
            ),
          )}
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
            <button type="button" className="send stop" onClick={() => abort.current?.abort()} aria-label={t.stop}>
              <StopIcon />
            </button>
          ) : (
            <button className="send" disabled={!input.trim()} aria-label={t.send}>
              <SendIcon />
            </button>
          )}
        </form>
      </main>

      <aside className={`sources ${sourcesOpen ? "open" : ""}`}>
        <div className="sources-head">
          <h2>{t.sources}</h2>
          <button className="icon-btn close-sources" onClick={() => setSourcesOpen(false)} aria-label={t.close}>
            <CloseIcon />
          </button>
        </div>
        {citations.length ? (
          <ol>
            {citations.map((c, i) => (
              <Source key={c.chunk_id} t={t} citation={c} n={i + 1} active={focus?.n === i + 1} />
            ))}
          </ol>
        ) : (
          <p className="empty">{t.noSources}</p>
        )}
      </aside>
      {sourcesOpen && <button className="scrim right" aria-label={t.close} onClick={() => setSourcesOpen(false)} />}
    </>
  );
}

/** Plain text with **bold** runs and [n] citation chips. */
function Inline({ text, max, onCite }: { text: string; max: number; onCite: (n: number) => void }) {
  return (
    <>
      {splitBold(text).map((run, i) => {
        const parts = splitCitations(run).map((part, j) =>
          typeof part === "string" ? (
            <Fragment key={j}>{part}</Fragment>
          ) : part.n >= 1 && part.n <= max ? (
            <button key={j} className="cite" onClick={() => onCite(part.n)} aria-label={`${part.n}`}>
              {part.n}
            </button>
          ) : (
            <Fragment key={j}>[{part.n}]</Fragment>
          ),
        );
        return i % 2 ? <strong key={i}>{parts}</strong> : <Fragment key={i}>{parts}</Fragment>;
      })}
    </>
  );
}

function Answer({ message, onCite }: { message: ChatMessage; onCite: (n: number) => void }) {
  const max = message.citations?.length ?? 0;
  const inline = (text: string) => <Inline text={text} max={max} onCite={onCite} />;
  return (
    <>
      {toBlocks(message.content).map((b, i) =>
        b.kind === "p" ? (
          <p key={i}>{inline(b.text)}</p>
        ) : b.kind === "ul" ? (
          <ul key={i}>{b.items.map((item, j) => <li key={j}>{inline(item)}</li>)}</ul>
        ) : (
          <ol key={i}>{b.items.map((item, j) => <li key={j}>{inline(item)}</li>)}</ol>
        ),
      )}
    </>
  );
}

function Source({ t, citation, n, active }: { t: Messages; citation: Citation; n: number; active: boolean }) {
  const ref = useRef<HTMLLIElement>(null);
  const pct = Math.round(citation.score * 100);
  useEffect(() => {
    if (active) ref.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [active]);
  return (
    <li ref={ref} className={`source ${active ? "active" : ""}`}>
      <div className="source-head">
        <span className="cite static">{n}</span>
        {citation.page ? <span className="page">{t.page} {citation.page}</span> : null}
        <span className="relevance" title={`${t.relevance} ${pct}%`}>
          <i style={{ width: `${pct}%` }} />
        </span>
        <span className="pct">{pct}%</span>
      </div>
      <p>{citation.snippet}</p>
    </li>
  );
}
