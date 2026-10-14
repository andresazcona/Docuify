"""Tests for DocumentService helpers."""

from pathlib import Path

import pytest

from app.core.errors import ValidationError
from app.services.document_service import DocumentService


def test_validate_pdf_chunk_valid() -> None:
    """Test PDF validation with valid PDF chunk."""
    service = DocumentService()

    # Valid PDF header
    chunk = b"%PDF-1.4\n"
    service._validate_pdf_chunk(chunk, "application/pdf")

    # Valid with content type
    service._validate_pdf_chunk(chunk, "")


def test_validate_pdf_chunk_invalid() -> None:
    """Test PDF validation with invalid chunk."""
    service = DocumentService()

    # Not a PDF
    chunk = b"<html><body>Not a PDF</body></html>"
    with pytest.raises(ValidationError, match="not a valid PDF"):
        service._validate_pdf_chunk(chunk, "text/html")


def test_build_storage_path() -> None:
    """Test storage path generation."""
    service = DocumentService()
    doc_id = "doc_abc123"
    filename = "paper.pdf"

    path = service._build_storage_path(doc_id, filename)

    assert doc_id in str(path)
    assert filename in str(path)
    assert path.name == filename


def test_resolve_arxiv_pdf_url_abs() -> None:
    """Test resolving arXiv abstract URL to PDF."""
    service = DocumentService()

    url = "https://arxiv.org/abs/2201.08239"
    pdf_url, arxiv_id = service._resolve_arxiv_pdf_url(url)

    assert "pdf" in pdf_url
    assert arxiv_id == "2201.08239"


def test_resolve_arxiv_pdf_url_pdf() -> None:
    """Test resolving arXiv PDF URL."""
    service = DocumentService()

    url = "https://arxiv.org/pdf/2201.08239.pdf"
    pdf_url, arxiv_id = service._resolve_arxiv_pdf_url(url)

    assert pdf_url == url
    assert arxiv_id == "2201.08239"


def test_delete_storage_nonexistent(tmp_path: Path) -> None:
    """Test deleting non-existent storage."""
    service = DocumentService()

    # Should not raise
    service._delete_storage(str(tmp_path / "nonexistent.pdf"))


def test_delete_storage_existing(tmp_path: Path) -> None:
    """Test deleting existing storage."""
    service = DocumentService()

    # Create a test file
    test_dir = tmp_path / "doc_test"
    test_dir.mkdir()
    test_file = test_dir / "test.pdf"
    test_file.write_bytes(b"test")

    service._delete_storage(str(test_file))

    assert not test_file.exists()
    assert not test_dir.exists()  # Parent dir removed if empty


def test_to_response_model() -> None:
    """Test conversion of Document to response model."""
    from datetime import datetime

    from app.db.models import Document
    from app.domain.schemas import DocumentStatus, SourceType

    service = DocumentService()

    now = datetime.utcnow()
    doc = Document(
        id="doc_123",
        source_type=SourceType.UPLOAD,
        source_ref="test.pdf",
        original_filename="test.pdf",
        status=DocumentStatus.READY,
        storage_path="/storage/doc_123/test.pdf",
        error_message=None,
        meta_json=None,
    )
    doc.created_at = now
    doc.updated_at = now

    response = service._to_response_model(doc)

    assert response.id == "doc_123"
    assert response.status == DocumentStatus.READY
    assert response.source_type == SourceType.UPLOAD
