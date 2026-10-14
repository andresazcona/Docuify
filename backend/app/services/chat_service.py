"""Chat over one document: retrieve passages, answer with citations, persist the conversation."""

import asyncio
import json
import re
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import (
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
    generate_secure_id,
    get_settings,
)
from app.db.models import Chat, Chunk, Message
from app.domain import (
    ChatAnswerResponse,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    CitationResponse,
    DocumentStatus,
    MessageResponse,
    MessageRole,
)
from app.rag.answer import extractive_answer, not_found
from app.rag.embeddings import from_bytes
from app.rag.llm import LLMConfig, LLMError, stream_llm, valid_model_name
from app.rag.retrieval import Candidate, Hit, search
from app.rag.text import tokenize
from app.repositories import DocumentRepository
from app.services.ingestion_service import IngestionService

CLIENT_PROVIDERS = {"anthropic", "openai"}
_HISTORY_TURNS = 6


def resolve_llm_config(
    provider: str | None, api_key: str | None, model: str | None
) -> LLMConfig | None:
    """Pick the answer engine for a request: client-supplied key, else server config, else none.

    Clients may choose the provider, key and model but never the endpoint (see rag/llm.py).
    """
    settings = get_settings()
    if provider and settings.allow_client_llm_keys:
        provider = provider.lower()
        if provider not in CLIENT_PROVIDERS:
            raise ValidationError(f"Unsupported provider '{provider}'. Use: anthropic, openai.")
        if not api_key:
            raise ValidationError("X-LLM-Key is required when X-LLM-Provider is set.")
        if model and not valid_model_name(model):
            raise ValidationError("Invalid model name.")
        return LLMConfig(
            provider, api_key, model, None, settings.llm_temperature, settings.llm_max_tokens
        )
    if settings.llm_provider != "extractive":
        return LLMConfig(
            settings.llm_provider,
            settings.llm_api_key,
            settings.llm_model,
            settings.llm_base_url,
            settings.llm_temperature,
            settings.llm_max_tokens,
        )
    return None


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class ChatService:
    def __init__(self, ingestion: IngestionService | None = None):
        self.settings = get_settings()
        self.documents = DocumentRepository()
        self.ingestion = ingestion or IngestionService(self.documents)

    # ---------------------- chats ----------------------
    async def create_chat(self, session: AsyncSession, document_id: str, title: str | None):
        await self.documents.get(session, document_id)
        chat = Chat(id=generate_secure_id("chat"), document_id=document_id, title=title)
        session.add(chat)
        await session.commit()
        await session.refresh(chat)
        return ChatResponse.model_validate(chat, from_attributes=True)

    async def history(self, session: AsyncSession, chat_id: str) -> ChatHistoryResponse:
        chat = await self._get_chat(session, chat_id)
        rows = (
            (
                await session.execute(
                    select(Message)
                    .where(Message.chat_id == chat_id)
                    .order_by(Message.created_at, Message.id)
                )
            )
            .scalars()
            .all()
        )
        messages = [
            MessageResponse(
                id=m.id,
                chat_id=m.chat_id,
                role=m.role,
                content=m.content,
                citations=[CitationResponse(**c) for c in m.citations_json]
                if m.citations_json
                else None,
                created_at=m.created_at,
            )
            for m in rows
        ]
        return ChatHistoryResponse(
            chat=ChatResponse.model_validate(chat, from_attributes=True), messages=messages
        )

    # ---------------------- answering ----------------------
    async def answer(
        self, session: AsyncSession, request: ChatRequest, llm: LLMConfig | None
    ) -> ChatAnswerResponse:
        chat_id, citations, parts, message_id = "", [], [], ""
        try:
            async for kind, value in self.turn(session, request, llm):
                if kind == "meta":
                    chat_id, citations = value
                elif kind == "delta":
                    parts.append(value)
                else:
                    message_id = value
        except LLMError as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return ChatAnswerResponse(
            chat_id=chat_id, message_id=message_id, answer="".join(parts), citations=citations
        )

    async def turn(
        self, session: AsyncSession, request: ChatRequest, llm: LLMConfig | None
    ) -> AsyncIterator[tuple[str, Any]]:
        """Run one question/answer turn, yielding ("meta"|"delta"|"done", value) events."""
        document = await self.documents.get(session, request.document_id)
        if document.status != DocumentStatus.READY:
            raise ConflictError("The document is not ready yet")

        chat = await self._get_or_create_chat(session, request)
        history = await self._recent_messages(session, chat.id)
        session.add(
            Message(
                id=generate_secure_id("msg"),
                chat_id=chat.id,
                role=MessageRole.USER,
                content=request.message,
                created_at=datetime.now(UTC),
            )
        )
        await session.commit()

        hits = await self._retrieve(session, document.id, _search_query(request.message, history))
        citations = [_citation(h) for h in hits]
        yield "meta", (chat.id, citations)

        parts: list[str] = []
        if not hits:
            parts.append(not_found(request.message))
            yield "delta", parts[0]
        elif llm is None:
            for piece in _pieces(extractive_answer(request.message, hits)):
                parts.append(piece)
                yield "delta", piece
        else:
            async for delta in stream_llm(llm, request.message, hits, history):
                parts.append(delta)
                yield "delta", delta

        message = Message(
            id=generate_secure_id("msg"),
            chat_id=chat.id,
            role=MessageRole.ASSISTANT,
            content="".join(parts),
            citations_json=[c.model_dump(mode="json") for c in citations] or None,
            created_at=datetime.now(UTC),
        )
        session.add(message)
        await session.commit()
        yield "done", message.id

    # ---------------------- internals ----------------------
    async def _get_chat(self, session: AsyncSession, chat_id: str) -> Chat:
        chat = (await session.execute(select(Chat).where(Chat.id == chat_id))).scalar_one_or_none()
        if chat is None:
            raise NotFoundError(f"Chat {chat_id} not found", resource_type="chat")
        return chat

    async def _get_or_create_chat(self, session: AsyncSession, request: ChatRequest) -> Chat:
        if request.chat_id:
            chat = await self._get_chat(session, request.chat_id)
            if chat.document_id != request.document_id:
                raise ValidationError("That chat belongs to a different document")
            return chat
        chat = Chat(
            id=generate_secure_id("chat"),
            document_id=request.document_id,
            title=request.message[:60],
        )
        session.add(chat)
        await session.commit()
        return chat

    async def _recent_messages(self, session: AsyncSession, chat_id: str) -> list[tuple[str, str]]:
        rows = (
            (
                await session.execute(
                    select(Message)
                    .where(Message.chat_id == chat_id)
                    .order_by(Message.created_at.desc(), Message.id.desc())
                    .limit(_HISTORY_TURNS)
                )
            )
            .scalars()
            .all()
        )
        return [(m.role.value, m.content) for m in reversed(rows)]

    async def _retrieve(self, session: AsyncSession, document_id: str, query: str) -> list[Hit]:
        rows = (
            (
                await session.execute(
                    select(Chunk)
                    .where(Chunk.document_id == document_id)
                    .order_by(Chunk.chunk_index)
                )
            )
            .scalars()
            .all()
        )
        candidates = [
            Candidate(r.id, r.page, r.text, from_bytes(r.embedding) if r.embedding else None)
            for r in rows
        ]
        query_vec = None
        embedder = self.ingestion.embedder
        if embedder is not None and candidates and all(c.embedding is not None for c in candidates):
            vec = (await asyncio.to_thread(embedder.embed, [query]))[0]
            if vec.shape == candidates[0].embedding.shape:
                query_vec = vec
        return search(query, candidates, top_k=self.settings.rag_top_k, query_embedding=query_vec)


def _search_query(message: str, history: list[tuple[str, str]]) -> str:
    """Short follow-ups ("and in 2023?") borrow the previous question for retrieval."""
    if len(tokenize(message)) < 3:
        previous = [c for role, c in history if role == MessageRole.USER.value]
        if previous:
            return f"{previous[-1]} {message}"
    return message


def _citation(hit: Hit) -> CitationResponse:
    snippet = " ".join(hit.text.split())
    return CitationResponse(
        chunk_id=hit.chunk_id,
        snippet=snippet if len(snippet) <= 700 else snippet[:697] + "...",
        page=hit.page,
        score=min(max(hit.score, 0.0), 1.0),
        locator={"page": hit.page} if hit.page else None,
    )


def _pieces(text: str, words: int = 4) -> list[str]:
    """Split a finished answer into small pieces so the extractive mode streams like the rest."""
    tokens = re.findall(r"\S+\s*", text)
    return ["".join(tokens[i : i + words]) for i in range(0, len(tokens), words)]
