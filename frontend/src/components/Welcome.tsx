import type { Messages } from "../i18n";
import { Logo } from "./icons";

export function Welcome({ t, hasDocs }: { t: Messages; hasDocs: boolean }) {
  return (
    <main className="chat welcome">
      <div className="hero">
        <Logo size={44} />
        <h2>{t.welcomeTitle}</h2>
        <p>{t.welcomeText}</p>
        <ul className="features">
          {t.features.map(([title, text]) => (
            <li key={title}>
              <strong>{title}</strong>
              <span>{text}</span>
            </li>
          ))}
        </ul>
        <p className="hero-hint">{hasDocs ? t.welcomePick : t.welcomeEmpty}</p>
      </div>
    </main>
  );
}
