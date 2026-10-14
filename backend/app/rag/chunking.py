"""Split page text into overlapping chunks that never cross a page boundary."""

import re
from dataclasses import dataclass

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class ChunkData:
    index: int
    page: int  # 1-based
    text: str


def _split_units(text: str) -> list[str]:
    """Paragraphs first, then sentences, so chunks end on natural boundaries."""
    units: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = " ".join(paragraph.split())
        if paragraph:
            units.extend(s for s in _SENTENCE_END.split(paragraph) if s)
    return units


def chunk_pages(pages: list[str], size: int, overlap: int) -> list[ChunkData]:
    """Greedy packing of sentences into chunks of about `size` characters.

    The tail of a chunk (about `overlap` characters) is repeated at the start of the next one,
    on the same page only, so an answer that straddles a boundary stays retrievable.
    """
    chunks: list[ChunkData] = []
    for page_number, text in enumerate(pages, start=1):
        current = ""
        for unit in _split_units(text):
            if current and len(current) + len(unit) + 1 > size:
                chunks.append(ChunkData(len(chunks), page_number, current))
                tail = current[-overlap:] if overlap else ""
                current = tail.split(" ", 1)[-1] if " " in tail else ""
            current = f"{current} {unit}".strip()
            while len(current) > size * 2:  # one enormous "sentence" (tables, code)
                chunks.append(ChunkData(len(chunks), page_number, current[:size]))
                current = current[size - overlap :]
        if current:
            chunks.append(ChunkData(len(chunks), page_number, current))
    return chunks
