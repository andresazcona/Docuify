import { describe, expect, it } from "vitest";
import { parseBlock, readSSE, splitCitations } from "./sse";

function streamOf(...chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
}

async function collect(body: ReadableStream<Uint8Array>) {
  const events = [];
  for await (const event of readSSE(body)) events.push(event);
  return events;
}

describe("parseBlock", () => {
  it("reads the event name and JSON payload", () => {
    expect(parseBlock('event: delta\ndata: {"text":"hi"}')).toEqual({
      event: "delta",
      data: { text: "hi" },
    });
  });

  it("ignores blocks without data or with broken JSON", () => {
    expect(parseBlock("event: ping")).toBeNull();
    expect(parseBlock("event: delta\ndata: {nope")).toBeNull();
  });
});

describe("readSSE", () => {
  it("handles events split across network chunks", async () => {
    const events = await collect(
      streamOf('event: meta\ndata: {"chat_id":"c1"}\n', '\nevent: delta\ndata: {"te', 'xt":"a"}\n\n'),
    );
    expect(events.map((e) => e.event)).toEqual(["meta", "delta"]);
    expect(events[1].data.text).toBe("a");
  });

  it("handles CRLF line endings and several events in one chunk", async () => {
    const events = await collect(
      streamOf('event: delta\r\ndata: {"text":"a"}\r\n\r\nevent: done\r\ndata: {"message_id":"m"}\r\n\r\n'),
    );
    expect(events.map((e) => e.event)).toEqual(["delta", "done"]);
  });

  it("keeps multi-byte characters intact across chunks", async () => {
    const bytes = new TextEncoder().encode('event: delta\ndata: {"text":"días"}\n\n');
    const cut = bytes.indexOf(0xc3) + 1; // split in the middle of "í"
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(bytes.slice(0, cut));
        controller.enqueue(bytes.slice(cut));
        controller.close();
      },
    });
    expect((await collect(body))[0].data.text).toBe("días");
  });
});

describe("splitCitations", () => {
  it("turns [n] markers into citation parts", () => {
    expect(splitCitations("Twenty days [1] per year [2].")).toEqual([
      "Twenty days ",
      { n: 1 },
      " per year ",
      { n: 2 },
      ".",
    ]);
  });

  it("leaves text without markers alone", () => {
    expect(splitCitations("No markers here.")).toEqual(["No markers here."]);
  });
});
