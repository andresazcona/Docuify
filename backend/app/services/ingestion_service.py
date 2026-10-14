"""Turn a stored PDF into searchable chunks: extract, chunk, embed, persist."""

import asyncio
import hashlib
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import ValidationError, generate_secure_id, get_logger, get_settings
from app.db.models import Chat, Chunk, Message
from app.domain import DocumentStatus
from app.rag.chunking import chunk_pages
from app.rag.embeddings import Embedder, get_embedder, to_bytes
from app.rag.extract import extract_pages
from app.repositories import DocumentRepository


class IngestionService:
    def __init__(
        self,
        repository: DocumentRepository | None = None,
        embedder: Embedder | None | str = "auto",
    ):
        self.settings = get_settings()
        self.repository = repository or DocumentRepository()
        self._embedder = embedder
        self.logger = get_logger(self.__class__.__name__)

    @property
    def embedder(self) -> Embedder | None:
        if self._embedder == "auto":
            self._embedder = get_embedder(
                self.settings.embedding_provider, self.settings.embedding_model
            )
        return self._embedder  # type: ignore[return-value]

    async def process(self, session: AsyncSession, document_id: str):
        """Index a document. Raises ValidationError when the PDF has nothing to index."""
        document = await self.repository.get(session, document_id)
        if not document.storage_path:
            raise ValidationError("The document has no stored file")

        pages = await asyncio.to_thread(extract_pages, Path(document.storage_path))
        chunks = chunk_pages(pages, self.settings.chunk_size, self.settings.chunk_overlap)
        if not chunks:
            raise ValidationError(
                "The PDF has no extractable text. Scanned documents (images) are not supported yet."
            )

        embedder = self.embedder
        vectors = (
            await asyncio.to_thread(embedder.embed, [c.text for c in chunks]) if embedder else None
        )

        await session.execute(delete(Chunk).where(Chunk.document_id == document_id))
        session.add_all(
            Chunk(
                id=generate_secure_id("chk"),
                document_id=document_id,
                chunk_index=c.index,
                page=c.page,
                text=c.text,
                hash=hashlib.sha256(c.text.encode()).hexdigest(),
                embedding=to_bytes(vectors[i]) if vectors is not None else None,
            )
            for i, c in enumerate(chunks)
        )
        await session.commit()

        meta = {**(document.meta_json or {}), "pages": len(pages), "chunks": len(chunks)}
        meta["embedding_model"] = embedder.name if embedder else None
        self.logger.info(
            "document_indexed", document_id=document_id, pages=len(pages), chunks=len(chunks)
        )
        return await self.repository.update_fields(
            session,
            document_id=document_id,
            status=DocumentStatus.READY,
            error_message=None,
            meta_json=meta,
        )

    @staticmethod
    async def purge(session: AsyncSession, document_id: str) -> None:
        """Delete everything derived from a document: chunks, chats and their messages."""
        chat_ids = (
            (await session.execute(select(Chat.id).where(Chat.document_id == document_id)))
            .scalars()
            .all()
        )
        if chat_ids:
            await session.execute(delete(Message).where(Message.chat_id.in_(chat_ids)))
            await session.execute(delete(Chat).where(Chat.id.in_(chat_ids)))
        await session.execute(delete(Chunk).where(Chunk.document_id == document_id))
        await session.commit()
