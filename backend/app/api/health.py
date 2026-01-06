"""Health check endpoints."""
from datetime import datetime

from fastapi import APIRouter, status

from app.core.config import get_settings
from app.db.session import check_db_connection
from app.domain.schemas import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse, status_code=status.HTTP_200_OK)
@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns basic service status without external dependencies.
    """
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=settings.api_version,
        timestamp=datetime.utcnow(),
    )


@router.get("/readyz", response_model=ReadyResponse, status_code=status.HTTP_200_OK)
@router.get("/ready", response_model=ReadyResponse, status_code=status.HTTP_200_OK)
async def readiness_check() -> ReadyResponse:
    """
    Readiness check endpoint.

    Validates that all required dependencies (database) are available.
    """
    settings = get_settings()
    db_connected = await check_db_connection()

    if not db_connected:
        return ReadyResponse(
            status="not_ready",
            database="disconnected",
            version=settings.api_version,
            timestamp=datetime.utcnow(),
        )

    return ReadyResponse(
        status="ready",
        database="connected",
        version=settings.api_version,
        timestamp=datetime.utcnow(),
    )
