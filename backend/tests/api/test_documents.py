"""Tests for document endpoints."""
from fastapi import status
from fastapi.testclient import TestClient


def test_create_document_arxiv_not_implemented(client: TestClient) -> None:
    """Test that arXiv endpoint returns not implemented."""
    response = client.post(
        "/api/v1/documents/arxiv",
        json={"arxiv_url": "https://arxiv.org/abs/2201.08239"},
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert "trace_id" in data


def test_create_document_url_not_implemented(client: TestClient) -> None:
    """Test that URL endpoint returns not implemented."""
    response = client.post(
        "/api/v1/documents/url",
        json={"pdf_url": "https://example.com/document.pdf"},
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


def test_list_documents_not_implemented(client: TestClient) -> None:
    """Test that list documents endpoint returns not implemented."""
    response = client.get("/api/v1/documents")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
