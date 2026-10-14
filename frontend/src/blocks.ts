/** Splits an answer into paragraphs and lists so it can be rendered without a markdown library. */
export type Block =
  | { kind: "p"; text: string }
  | { kind: "ul" | "ol"; items: string[] };

const BULLET = /^[-*•]\s+(.*)$/;
const NUMBERED = /^\d+[.)]\s+(.*)$/;

export function toBlocks(text: string): Block[] {
  const out: Block[] = [];
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    const bullet = BULLET.exec(line);
    const numbered = bullet ? null : NUMBERED.exec(line);
    const match = bullet ?? numbered;
    if (!match) {
      out.push({ kind: "p", text: line });
      continue;
    }
    const kind = bullet ? "ul" : "ol";
    const last = out[out.length - 1];
    if (last && last.kind === kind) last.items.push(match[1]);
    else out.push({ kind, items: [match[1]] });
  }
  return out;
}

/** Splits `**bold**` runs; odd entries are the bold ones. */
export function splitBold(text: string): string[] {
  return text.split(/\*\*(.+?)\*\*/g);
}
