"""Error handling and exception definitions."""
import uuid
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger(__name__)


class ErrorDetail(BaseModel):
    """Error detail model."""

    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    code: str
    message: str
    trace_id: str
    details: list[ErrorDetail] | None = None


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: list[ErrorDetail] | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, message: str, details: list[ErrorDetail] | None = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class NotFoundError(AppException):
    """Resource not found error."""

    def __init__(self, message: str, resource_type: str | None = None):
        details = (
            [ErrorDetail(field="resource_type", message=resource_type)]
            if resource_type
            else None
        )
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class UnauthorizedError(AppException):
    """Unauthorized access error."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenError(AppException):
    """Forbidden access error."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ConflictError(AppException):
    """Resource conflict error."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
        )


class RateLimitError(AppException):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class ServiceUnavailableError(AppException):
    """Service temporarily unavailable."""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


def generate_trace_id() -> str:
    """Generate a unique trace ID for request tracking."""
    return str(uuid.uuid4())


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions."""
    trace_id = generate_trace_id()

    logger.error(
        "application_exception",
        code=exc.code,
        message=exc.message,
        trace_id=trace_id,
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=exc.code,
            message=exc.message,
            trace_id=trace_id,
            details=exc.details,
        ).model_dump(),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    trace_id = generate_trace_id()

    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        trace_id=trace_id,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code="HTTP_ERROR",
            message=exc.detail if isinstance(exc.detail, str) else "HTTP error occurred",
            trace_id=trace_id,
        ).model_dump(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions."""
    trace_id = generate_trace_id()

    logger.exception(
        "unhandled_exception",
        trace_id=trace_id,
        path=request.url.path,
        method=request.method,
        exc_info=exc,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            code="INTERNAL_ERROR",
            message="An internal error occurred. Please contact support with trace_id.",
            trace_id=trace_id,
        ).model_dump(),
    )


def register_exception_handlers(app: Any) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
