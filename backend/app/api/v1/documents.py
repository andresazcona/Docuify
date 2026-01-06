"""Document management endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.domain.schemas import (
    DocumentCreateArxivRequest,
    DocumentCreateResponse,
    DocumentCreateUrlRequest,
    DocumentListResponse,
    DocumentResponse,
)
from app.services import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service() -> DocumentService:
    """Dependency provider for DocumentService."""
    return DocumentService()


@router.post(
    "/arxiv",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_document_from_arxiv(
    request: DocumentCreateArxivRequest,
    session: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
) -> DocumentCreateResponse:
    """Create document from arXiv URL (ingestion)."""
    return await service.create_from_arxiv(request, session)


@router.post(
    "/url",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_document_from_url(
    request: DocumentCreateUrlRequest,
    session: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
) -> DocumentCreateResponse:
    """Create document from public PDF URL with SSRF protection."""
    return await service.create_from_url(request, session)


@router.post(
    "/upload",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    file: Annotated[UploadFile, File(description="PDF file to upload")],
    session: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
) -> DocumentCreateResponse:
    """Upload a PDF document."""
    return await service.create_from_upload(file, session)


@router.get("", response_model=DocumentListResponse, status_code=status.HTTP_200_OK)
async def list_documents(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    """List documents with pagination."""
    return await service.list_documents(session, limit=limit, offset=offset)


@router.get("/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Get document details by ID."""
    return await service.get_document(session, document_id)


@router.post(
    "/{document_id}/retry",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_document_processing(
    document_id: str,
    session: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
) -> DocumentCreateResponse:
    """Retry processing for a failed document."""
    return await service.retry_document(session, document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    session: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
) -> None:
    """Delete a document and its stored file."""
    await service.delete_document(session, document_id)
