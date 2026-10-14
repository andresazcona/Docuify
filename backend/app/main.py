"""FastAPI application factory and configuration."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import health, v1_router
from app.core import configure_logging, get_logger, get_settings, register_exception_handlers
from app.db import close_db, init_db

# Configure logging first
configure_logging()
logger = get_logger(__name__)


def get_limiter() -> Limiter:
    """Create rate limiter instance."""
    settings = get_settings()

    if not settings.rate_limit_enabled:
        # Create a no-op limiter when rate limiting is disabled
        return Limiter(key_func=get_remote_address, enabled=False)

    return Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.rate_limit_times}/{settings.rate_limit_seconds}second"],
        storage_uri=settings.redis_url,
        strategy="fixed-window",
    )


# Initialize rate limiter
limiter = get_limiter()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for the application.
    """
    settings = get_settings()
    logger.info(
        "starting_application",
        version=settings.api_version,
        environment=settings.environment,
    )

    # Initialize database
    await init_db()
    logger.info("database_initialized")

    yield

    # Cleanup
    logger.info("shutting_down_application")
    await close_db()
    logger.info("application_shutdown_complete")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description="ChatPDF Backend API - Document Q&A with RAG",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Register exception handlers
    register_exception_handlers(app)

    # Include routers
    app.include_router(health.router)
    app.include_router(v1_router, prefix=settings.api_prefix)

    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        """Root endpoint with API info."""
        return {
            "service": settings.api_title,
            "version": settings.api_version,
            "docs": "/docs",
            "health": "/healthz",
        }

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):  # type: ignore
        """Log all incoming requests."""
        logger.info(
            "incoming_request",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )

        response = await call_next(request)

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )

        return response

    logger.info("application_created", version=settings.api_version)
    return app


# Create app instance
app = create_app()
