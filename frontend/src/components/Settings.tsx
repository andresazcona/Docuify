import type { Messages } from "../i18n";
import { CloseIcon } from "./icons";
import type { Engine, EngineSettings } from "../types";

interface Props {
  t: Messages;
  value: EngineSettings;
  onChange: (next: EngineSettings) => void;
  onClose: () => void;
}

export function Settings({ t, value, onChange, onClose }: Props) {
  const options: Array<{ id: Engine; label: string; help: string }> = [
    { id: "extractive", label: t.engineExtractive, help: t.engineExtractiveHelp },
    { id: "anthropic", label: t.engineAnthropic, help: t.engineHelp },
    { id: "openai", label: t.engineOpenai, help: t.engineHelp },
  ];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={t.settings} onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h2>{t.settings}</h2>
          <button className="icon-btn" onClick={onClose} aria-label={t.close}>
            <CloseIcon />
          </button>
        </div>
        {options.map((o) => (
          <label key={o.id} className={`option ${value.engine === o.id ? "selected" : ""}`}>
            <input
              type="radio"
              name="engine"
              checked={value.engine === o.id}
              onChange={() => onChange({ ...value, engine: o.id })}
            />
            <span>
              <strong>{o.label}</strong>
              <small>{o.help}</small>
            </span>
          </label>
        ))}

        {value.engine !== "extractive" && (
          <div className="fields">
            <label>
              {t.apiKey}
              <input
                type="password"
                autoComplete="off"
                value={value.apiKey}
                onChange={(e) => onChange({ ...value, apiKey: e.target.value })}
                placeholder="sk-…"
              />
            </label>
            <small>{t.keyHelp}</small>
            <label>
              {t.model}
              <input value={value.model} onChange={(e) => onChange({ ...value, model: e.target.value })} />
            </label>
          </div>
        )}

        <div className="modal-actions">
          <button className="primary" onClick={onClose}>{t.close}</button>
        </div>
      </div>
    </div>
  );
}
