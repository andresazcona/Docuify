"""Pydantic schemas for API contracts."""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class DocumentStatus(str, Enum):
    """Document processing status."""

    CREATED = "CREATED"
    DOWNLOADING = "DOWNLOADING"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    CHUNKING = "CHUNKING"
    INDEXING = "INDEXING"
    READY = "READY"
    FAILED = "FAILED"


class SourceType(str, Enum):
    """Document source type."""

    ARXIV = "ARXIV"
    UPLOAD = "UPLOAD"
    URL = "URL"


class MessageRole(str, Enum):
    """Chat message role."""

    USER = "user"
    ASSISTANT = "assistant"


# Health & Meta Schemas


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReadyResponse(BaseModel):
    """Readiness check response."""

    status: str = "ready"
    database: str = "connected"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MetaResponse(BaseModel):
    """API metadata and configuration."""

    version: str
    environment: str
    features: dict[str, bool]
    limits: dict[str, Any]


# Document Schemas


class DocumentCreateArxivRequest(BaseModel):
    """Request to create document from arXiv."""

    arxiv_url: HttpUrl = Field(
        ...,
        description="arXiv URL (abs or pdf)",
        examples=["https://arxiv.org/abs/2201.08239"],
    )

    @field_validator("arxiv_url")
    @classmethod
    def validate_arxiv_url(cls, v: HttpUrl) -> HttpUrl:
        """Validate that URL is from arXiv."""
        url_str = str(v)
        if "arxiv.org" not in url_str:
            raise ValueError("URL must be from arxiv.org")
        return v


class DocumentCreateUrlRequest(BaseModel):
    """Request to create document from public URL."""

    pdf_url: HttpUrl = Field(
        ...,
        description="Public URL to PDF file",
        examples=["https://example.com/document.pdf"],
    )


class DocumentCreateResponse(BaseModel):
    """Response after creating a document."""

    document_id: str
    status: DocumentStatus
    message: str | None = None


class DocumentMetadata(BaseModel):
    """Document metadata."""

    arxiv_id: str | None = None
    title: str | None = None
    authors: list[str] | None = None
    publication_date: str | None = None
    pages: int | None = None


class DocumentResponse(BaseModel):
    """Document detail response."""

    id: str
    source_type: SourceType
    source_ref: str | None = None
    original_filename: str | None = None
    status: DocumentStatus
    error_message: str | None = None
    metadata: DocumentMetadata | None = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """List of documents with pagination."""

    documents: list[DocumentResponse]
    total: int
    limit: int
    offset: int


# Chat Schemas


class ChatCreateRequest(BaseModel):
    """Request to create a new chat."""

    document_id: str = Field(..., description="Document ID to chat with")
    title: str | None = Field(None, max_length=200, description="Optional chat title")


class ChatResponse(BaseModel):
    """Chat detail response."""

    id: str
    document_id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class CitationResponse(BaseModel):
    """Citation/source for an answer."""

    chunk_id: str
    snippet: str = Field(..., description="Text snippet from source")
    page: int | None = Field(None, description="Page number if available")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    locator: dict[str, Any] | None = Field(
        None, description="Additional location metadata"
    )


class ChatRequest(BaseModel):
    """Request to send a message in chat."""

    document_id: str = Field(..., description="Document ID")
    chat_id: str | None = Field(None, description="Chat ID (creates new if not provided)")
    message: str = Field(..., min_length=1, max_length=5000, description="User message")


class ChatAnswerResponse(BaseModel):
    """Response from chat with answer and citations."""

    chat_id: str
    message_id: str
    answer: str
    citations: list[CitationResponse]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MessageResponse(BaseModel):
    """Chat message."""

    id: str
    chat_id: str
    role: MessageRole
    content: str
    citations: list[CitationResponse] | None = None
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    """Chat history with messages."""

    chat: ChatResponse
    messages: list[MessageResponse]
