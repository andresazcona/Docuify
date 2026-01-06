"""Repository for document persistence."""
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.models import Document


class DocumentRepository:
    """Data access layer for documents."""

    async def create(self, session: AsyncSession, document: Document) -> Document:
        """Persist a new document."""
        session.add(document)
        await session.commit()
        await session.refresh(document)
        return document

    async def get(self, session: AsyncSession, document_id: str) -> Document:
        """Get a document by ID or raise NotFoundError."""
        result = await session.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if document is None:
            raise NotFoundError(f"Document {document_id} not found", resource_type="document")
        return document

    async def list(
        self, session: AsyncSession, *, limit: int, offset: int
    ) -> tuple[list[Document], int]:
        """List documents with pagination and total count."""
        stmt = select(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        documents = result.scalars().all()

        count_stmt = select(func.count()).select_from(Document)
        total = (await session.execute(count_stmt)).scalar_one()
        return documents, int(total)

    async def update_fields(
        self, session: AsyncSession, document_id: str, **fields: Any
    ) -> Document:
        """Update fields on a document and return the updated instance."""
        await session.execute(update(Document).where(Document.id == document_id).values(**fields))
        await session.commit()
        return await self.get(session, document_id)

    async def delete(self, session: AsyncSession, document_id: str) -> None:
        """Delete a document."""
        document = await self.get(session, document_id)
        await session.delete(document)
        await session.commit()
