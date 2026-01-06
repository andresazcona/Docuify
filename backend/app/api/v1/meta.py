"""API v1 meta endpoint."""
from fastapi import APIRouter, status

from app.core.config import get_settings
from app.domain.schemas import MetaResponse

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("", response_model=MetaResponse, status_code=status.HTTP_200_OK)
async def get_api_meta() -> MetaResponse:
    """
    Get API metadata and non-sensitive configuration.

    Returns version, environment, feature flags, and operational limits.
    """
    settings = get_settings()

    return MetaResponse(
        version=settings.api_version,
        environment=settings.environment,
        features={
            "arxiv_ingestion": True,
            "url_ingestion": True,
            "file_upload": True,
            "streaming_chat": False,  # Not implemented yet
            "graph_rag": False,  # Not implemented yet
        },
        limits={
            "max_upload_mb": settings.max_upload_mb,
            "max_download_mb": settings.max_download_mb,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "rag_top_k": settings.rag_top_k,
        },
    )
