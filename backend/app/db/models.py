"""Database models."""
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.domain.schemas import DocumentStatus, MessageRole, SourceType


class Document(Base):
    """Document model."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, native_enum=False), nullable=False
    )
    source_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False),
        nullable=False,
        default=DocumentStatus.CREATED,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Chat(Base):
    """Chat model."""

    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Message(Base):
    """Message model."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    chat_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, native_enum=False), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Chunk(Base):
    """Chunk model (optional, for storing chunks separately)."""

    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    locator_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
