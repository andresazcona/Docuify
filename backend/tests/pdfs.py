"""Tiny PDF writer for tests and the sample document: real text PDFs, no third-party library."""

import textwrap


def _escape(line: str) -> bytes:
    data = line.encode("cp1252", errors="replace")
    return data.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def make_pdf(pages: list[str], *, wrap: int = 88) -> bytes:
    """One page per string; blank lines between paragraphs. Text is selectable and extractable."""
    objects: list[bytes] = []
    n = len(pages)
    kids = " ".join(f"{4 + 2 * i} 0 R" for i in range(n))
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode())
    objects.append(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    )
    for i, text in enumerate(pages):
        lines: list[str] = []
        for paragraph in text.split("\n\n"):
            lines.extend(textwrap.wrap(paragraph, wrap) or [""])
            lines.append("")
        body = b"BT /F1 11 Tf 56 790 Td 15 TL\n"
        body += b"".join(b"(" + _escape(line) + b") Tj T*\n" for line in lines)
        body += b"ET"
        content_id = 5 + 2 * i
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode()
        )
        objects.append(f"<< /Length {len(body)} >>\nstream\n".encode() + body + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(out)
