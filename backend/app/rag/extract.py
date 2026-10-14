"""PDF text extraction, page by page."""

from pathlib import Path

from pypdf import PdfReader


def extract_pages(path: Path) -> list[str]:
    """Return the text of every page (empty string for pages without a text layer)."""
    reader = PdfReader(str(path))
    return [(page.extract_text() or "").strip() for page in reader.pages]
