"""Tests for document endpoints."""
import io

import pytest
from fastapi import status
from httpx import AsyncClient

from app.domain.schemas import DocumentStatus


@pytest.mark.asyncio
async def test_list_documents_empty(client: AsyncClient) -> None:
    """Test listing documents when none exist."""
    response = await client.get("/api/v1/documents")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 0
    assert data["documents"] == []


@pytest.mark.asyncio
async def test_create_document_from_upload_success(client: AsyncClient) -> None:
    """Test successful PDF upload."""
    # Create a fake PDF file
    pdf_bytes = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n" + b"Fake PDF content\n%%EOF\n"
    files = {"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    response = await client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert "document_id" in data
    assert data["status"] == DocumentStatus.READY


@pytest.mark.asyncio
async def test_create_document_from_url_ssrf_blocked(client: AsyncClient) -> None:
    """Test that SSRF attempts are blocked."""
    response = await client.post(
        "/api/v1/documents/url",
        json={"pdf_url": "http://127.0.0.1/secret.pdf"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "SSRF" in data["message"] or "validation" in data["message"].lower()


@pytest.mark.asyncio
async def test_create_document_from_url_invalid_scheme(client: AsyncClient) -> None:
    """Test that invalid URL schemes are rejected."""
    response = await client.post(
        "/api/v1/documents/url",
        json={"pdf_url": "ftp://example.com/file.pdf"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_document_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent document."""
    response = await client.get("/api/v1/documents/doc_nonexistent")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_document_not_found(client: AsyncClient) -> None:
    """Test deleting a non-existent document."""
    response = await client.delete("/api/v1/documents/doc_nonexistent")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_and_get_document(client: AsyncClient) -> None:
    """Test creating and retrieving a document."""
    pdf_bytes = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n" + b"Content\n%%EOF\n"
    files = {"file": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    create_response = await client.post("/api/v1/documents/upload", files=files)
    assert create_response.status_code == status.HTTP_202_ACCEPTED
    doc_id = create_response.json()["document_id"]

    get_response = await client.get(f"/api/v1/documents/{doc_id}")
    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()
    assert data["id"] == doc_id
    assert data["status"] == DocumentStatus.READY


@pytest.mark.asyncio
async def test_retry_document_not_failed(client: AsyncClient) -> None:
    """Test retrying a document that is not failed."""
    pdf_bytes = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n" + b"Content\n%%EOF\n"
    files = {"file": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    create_response = await client.post("/api/v1/documents/upload", files=files)
    doc_id = create_response.json()["document_id"]

    retry_response = await client.post(f"/api/v1/documents/{doc_id}/retry")
    assert retry_response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_delete_document(client: AsyncClient) -> None:
    """Test deleting a document."""
    pdf_bytes = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n" + b"Content\n%%EOF\n"
    files = {"file": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    create_response = await client.post("/api/v1/documents/upload", files=files)
    doc_id = create_response.json()["document_id"]

    delete_response = await client.delete(f"/api/v1/documents/{doc_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    get_response = await client.get(f"/api/v1/documents/{doc_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND
