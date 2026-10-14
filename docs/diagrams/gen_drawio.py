"""Generate docs/diagrams/folio.drawio (2 pages). Export PNGs with the diagrams.net viewer.

    python docs/diagrams/gen_drawio.py
"""

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).with_name("folio.drawio")

TITLE = (
    "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;"
)
PALETTE = {
    "client": ("#E1D5E7", "#9673A6"),
    "proxy": ("#DAE8FC", "#6C8EBF"),
    "api": ("#FFE6CC", "#D79B00"),
    "data": ("#F8CECC", "#B85450"),
    "ai": ("#D5E8D4", "#82B366"),
    "ext": ("#F5F5F5", "#666666"),
    "step": ("#FFFFFF", "#6C8EBF"),
}


class Page:
    def __init__(self, name: str, width: int = 1600, height: int = 900):
        self.name, self.w, self.h = name, width, height
        self.cells: list[str] = []
        self.n = 1

    def _id(self) -> str:
        self.n += 1
        return f"c{self.n}"

    def title(self, heading: str, sub: str) -> None:
        value = (
            f'<b style="font-size:20px;">{escape(heading)}</b><br>'
            f'<span style="font-size:12px;color:#666;">{escape(sub)}</span>'
        )
        self.cells.append(self._cell(self._id(), value, TITLE, self.w / 2 - 400, 14, 800, 46))

    @staticmethod
    def _cell(cid, value, style, x, y, w, h, vertex=True, extra="") -> str:
        value = escape(value, {'"': "&quot;"})
        return (
            f'<mxCell id="{cid}" value="{value}" style="{style}" vertex="1" parent="1"{extra}>'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )

    def box(self, kind, label, x, y, w, h, *, sub="", dashed=False, bold=True) -> str:
        fill, stroke = PALETTE[kind]
        text = f"<b>{escape(label)}</b>" if bold else escape(label)
        if sub:
            text += f'<br><span style="font-size:11px;color:#555;">{sub}</span>'
        style = (
            f"rounded=1;whiteSpace=wrap;html=1;arcSize=8;fillColor={fill};strokeColor={stroke};"
            f"strokeWidth=2;fontSize=13;{'dashed=1;' if dashed else ''}"
        )
        cid = self._id()
        self.cells.append(self._cell(cid, text, style, x, y, w, h))
        return cid

    def group(self, kind, label, x, y, w, h) -> None:
        fill, stroke = PALETTE[kind]
        style = (
            f"rounded=1;whiteSpace=wrap;html=1;arcSize=3;fillColor={fill};strokeColor={stroke};"
            "strokeWidth=2;dashed=1;verticalAlign=top;align=left;spacingLeft=12;spacingTop=6;"
            "fontStyle=1;fontSize=13;opacity=45;"
        )
        self.cells.append(self._cell(self._id(), label, style, x, y, w, h))

    def note(self, text, x, y, w, h) -> None:
        style = (
            "rounded=1;whiteSpace=wrap;html=1;arcSize=6;fillColor=#f5f5f5;strokeColor=#666666;"
            "align=left;verticalAlign=top;spacing=10;fontSize=12;"
        )
        self.cells.append(self._cell(self._id(), text, style, x, y, w, h))

    def edge(self, src, dst, label="", *, color="#333333", dashed=False, exit=None, entry=None):
        style = (
            "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;"
            f"strokeColor={color};strokeWidth=2;fontSize=11;fontColor={color};labelBackgroundColor=#ffffff;"
            f"{'dashed=1;' if dashed else ''}"
        )
        if exit:
            style += f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
        if entry:
            style += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
        cid = self._id()
        self.cells.append(
            f'<mxCell id="{cid}" value="{escape(label)}" style="{style}" edge="1" parent="1" '
            f'source="{src}" target="{dst}"><mxGeometry relative="1" as="geometry"/></mxCell>'
        )

    def xml(self) -> str:
        return (
            f'<diagram name="{escape(self.name)}" id="{self.name.lower().replace(" ", "-")}">'
            f'<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" '
            f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.w}" '
            f'pageHeight="{self.h}" math="0" shadow="0"><root><mxCell id="0"/>'
            f'<mxCell id="1" parent="0"/>{"".join(self.cells)}</root></mxGraphModel></diagram>'
        )


def architecture() -> Page:
    p = Page("Architecture", 1700, 900)
    p.title("Folio: architecture", "React · nginx · FastAPI · PostgreSQL · local embeddings · optional LLM")

    browser = p.box("client", "Browser", 40, 280, 200, 90, sub="React SPA · ES / EN<br>answers stream in as SSE")
    nginx = p.box("proxy", "nginx", 300, 280, 200, 90, sub="static files + /api proxy<br>buffering off for SSE")

    p.group("api", "API container (FastAPI, non-root)", 580, 120, 700, 600)
    docs = p.box("api", "Documents API", 610, 180, 250, 80, sub="upload · arXiv · URL (SSRF guard)")
    chat = p.box("api", "Chat API", 610, 330, 250, 80, sub="ask · history · streamed answers")
    rag = p.box(
        "api", "RAG pipeline", 960, 180, 290, 230,
        sub="extract pages<br>↓<br>chunk (600 / 100)<br>↓<br>BM25 + cosine, fused (RRF)<br>↓<br>"
        "extractive answer (default)<br>or LLM answer with [n] citations",
    )
    embed = p.box("ai", "fastembed (ONNX)", 610, 520, 250, 80, sub="multilingual MiniLM<br>CPU only, no key")
    llm = p.box("ext", "LLM client", 960, 520, 290, 80, sub="Anthropic · OpenAI · Ollama<br>endpoint fixed by operator", dashed=True)

    db = p.box("data", "PostgreSQL", 1380, 160, 250, 110, sub="documents · chunks (+ vectors)<br>chats · messages")
    vol = p.box("data", "PDF storage", 1380, 320, 250, 80, sub="volume · type and magic bytes checked")
    anth = p.box("ext", "Anthropic API", 1380, 480, 250, 60, dashed=True)
    oai = p.box("ext", "OpenAI API", 1380, 560, 250, 60, dashed=True)
    ollama = p.box("ext", "Ollama (local)", 1380, 640, 250, 60, dashed=True, sub="LLM_BASE_URL")

    p.edge(browser, nginx, "HTTP :8080", color="#6C8EBF")
    p.edge(nginx, docs, "", color="#6C8EBF", entry=(0, 0.5))
    p.edge(nginx, chat, "", color="#6C8EBF", entry=(0, 0.5))
    p.edge(docs, rag, "index", color="#D79B00", exit=(1, 0.5), entry=(0, 0.2))
    p.edge(chat, rag, "ask", color="#D79B00", exit=(1, 0.5), entry=(0, 0.8))
    p.edge(rag, embed, "vectors", color="#82B366", exit=(0.1, 1), entry=(0.5, 0))
    p.edge(rag, llm, "passages", color="#666666", dashed=True, exit=(0.5, 1), entry=(0.5, 0))
    p.edge(rag, db, "records", color="#B85450", exit=(1, 0.2), entry=(0, 0.5))
    p.edge(rag, vol, "PDF files", color="#B85450", exit=(1, 0.8), entry=(0, 0.5))
    p.edge(llm, anth, "", color="#666666", dashed=True, exit=(1, 0.2), entry=(0, 0.5))
    p.edge(llm, oai, "", color="#666666", dashed=True, exit=(1, 0.5), entry=(0, 0.5))
    p.edge(llm, ollama, "", color="#666666", dashed=True, exit=(1, 0.8), entry=(0, 0.5))

    p.note(
        "<b>Security</b><br>"
        "• Clients may bring an API key (X-LLM-Key) but never choose the endpoint: no SSRF<br>"
        "• Keys live in memory for one request: never logged, never stored<br>"
        "• URL ingestion blocks private and loopback addresses<br>"
        "• Containers run as non-root; the database is not published",
        40, 440, 500, 150,
    )
    p.note(
        "<b>Why no vector database</b><br>"
        "Retrieval is per document (a few thousand chunks), so scoring in process is fast and "
        "removes a service. pgvector is the next step if documents grow.",
        40, 620, 500, 100,
    )
    p.note("<b>Cost to run:</b> $0. Default mode needs no model, no API key and no cloud.", 580, 770, 700, 60)
    return p


def flow() -> Page:
    p = Page("Question flow", 1700, 760)
    p.title("From PDF to cited answer", "ingestion on upload, retrieval and answering on every question")

    p.group("proxy", "1. Ingestion (once per document)", 30, 90, 1640, 230)
    steps = [
        ("Upload PDF", "file, arXiv or URL<br>validated: type, size, SSRF"),
        ("Extract text", "pypdf, page by page<br>scanned PDFs rejected"),
        ("Chunk", "~600 chars, 100 overlap<br>never across pages"),
        ("Embed (optional)", "fastembed, local<br>float32 vectors"),
        ("Store", "chunks + page + vector<br>document → READY"),
    ]
    ids = []
    for i, (label, sub) in enumerate(steps):
        ids.append(p.box("step", f"{i + 1}. {label}", 60 + i * 320, 150, 270, 100, sub=sub))
    for a, b in zip(ids, ids[1:], strict=False):
        p.edge(a, b, color="#6C8EBF")

    p.group("api", "2. Question (every message)", 30, 350, 1640, 380)
    q = [
        ("Ask", "POST /chats/chat/stream<br>optional X-LLM-* headers"),
        ("Retrieve", "BM25 over chunk text<br>+ cosine over vectors<br>fused with RRF → top 5"),
        ("Answer", "extractive: best sentences<br>LLM: streamed, [n] cited<br>nothing found → says so"),
        ("Stream", "SSE events:<br>meta (citations) · delta … · done"),
        ("Show", "[n] chips link to the<br>source passage and page"),
    ]
    qids = []
    for i, (label, sub) in enumerate(q):
        qids.append(p.box("api", f"{i + 1}. {label}", 60 + i * 320, 410, 270, 110, sub=sub))
    for a, b in zip(qids, qids[1:], strict=False):
        p.edge(a, b, color="#D79B00")

    p.note(
        "<b>Choosing the answer engine</b><br>"
        "1) a key sent by the client (anthropic / openai), 2) the operator's LLM_PROVIDER "
        "(including Ollama), 3) extractive, which needs nothing.",
        60, 570, 780, 110,
    )
    p.note(
        "<b>When retrieval finds nothing</b><br>"
        "The LLM is not called at all (no cost, no hallucination): the reply is "
        "“I could not find that in the document.” in the language of the question.",
        880, 570, 740, 110,
    )
    return p


def main() -> None:
    pages = [architecture(), flow()]
    OUT.write_text(
        '<mxfile host="app.diagrams.net">' + "".join(pg.xml() for pg in pages) + "</mxfile>",
        encoding="utf-8",
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
