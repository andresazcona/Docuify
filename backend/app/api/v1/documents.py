"""Document management endpoints (placeholder)."""
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.core.errors import NotFoundError, ServiceUnavailableError
from app.domain.schemas import (
    DocumentCreateArxivRequest,
    DocumentCreateResponse,
    DocumentCreateUrlRequest,
    DocumentListResponse,
    DocumentResponse,
    DocumentStatus,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/arxiv",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_document_from_arxiv(
    request: DocumentCreateArxivRequest,
) -> DocumentCreateResponse:
    """
    Create document from arXiv URL.

    Accepts arXiv abstract or PDF URLs and queues the document for processing.

    **Status: Not Implemented** - Returns 501 for now.
    """
    raise ServiceUnavailableError("ArXiv ingestion not yet implemented")


@router.post(
    "/url",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_document_from_url(
    request: DocumentCreateUrlRequest,
) -> DocumentCreateResponse:
    """
    Create document from public PDF URL.

    Downloads PDF from provided URL and queues for processing.
    Includes SSRF protection.

    **Status: Not Implemented** - Returns 501 for now.
    """
    raise ServiceUnavailableError("URL ingestion not yet implemented")


@router.post(
    "/upload",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    file: Annotated[UploadFile, File(description="PDF file to upload")],
) -> DocumentCreateResponse:
    """
    Upload a PDF document.

    Accepts multipart file upload and queues document for processing.

    **Status: Not Implemented** - Returns 501 for now.
    """
    raise ServiceUnavailableError("File upload not yet implemented")


@router.get("", response_model=DocumentListResponse, status_code=status.HTTP_200_OK)
async def list_documents(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DocumentListResponse:
    """
    List all documents with pagination.

    Returns paginated list of documents with their current status.

    **Status: Not Implemented** - Returns 501 for now.
    """
    raise ServiceUnavailableError("Document listing not yet implemented")


@router.get("/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_document(document_id: str) -> DocumentResponse:
    """
    Get document details by ID.

    Returns full document information including status and metadata.

    **Status: Not Implemented** - Returns 501 for now.
    """
    raise NotFoundError("Document not found or feature not yet implemented")


@router.post(
    "/{document_id}/retry",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_document_processing(document_id: str) -> DocumentCreateResponse:
    """
    Retry processing for a failed document.

    Re-queues a failed document for processing.

    **Status: Not Implemented** - Returns 501 for now.
    """
    raise ServiceUnavailableError("Document retry not yet implemented")


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str) -> None:
    """
    Delete a document.

    Removes document and all associated data (chunks, chats, messages).

    **Status: Not Implemented** - Returns 501 for now.
    """
    raise ServiceUnavailableError("Document deletion not yet implemented")
