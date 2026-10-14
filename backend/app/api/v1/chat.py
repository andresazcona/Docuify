"""Chat endpoints: create chats, read history, ask questions (plain or streamed over SSE)."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import AppException
from app.db import get_db
from app.db.session import get_session_factory
from app.domain import (
    ChatAnswerResponse,
    ChatCreateRequest,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
)
from app.rag.llm import LLMError
from app.services import ChatService
from app.services.chat_service import resolve_llm_config, sse

router = APIRouter(prefix="/chats", tags=["chat"])


def get_chat_service() -> ChatService:
    return ChatService()


async def llm_config(
    x_llm_provider: Annotated[str | None, Header()] = None,
    x_llm_key: Annotated[str | None, Header()] = None,
    x_llm_model: Annotated[str | None, Header()] = None,
):
    """Optional per-request answer engine. Without these headers the server default is used
    (extractive unless the operator configured an LLM). The key is never logged or stored."""
    return resolve_llm_config(x_llm_provider, x_llm_key, x_llm_model)


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    request: ChatCreateRequest,
    session: AsyncSession = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Create an empty chat for a document."""
    return await service.create_chat(session, request.document_id, request.title)


@router.get("/{chat_id}", response_model=ChatHistoryResponse)
async def get_chat(
    chat_id: str,
    session: AsyncSession = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
) -> ChatHistoryResponse:
    """Chat details with every message and its citations."""
    return await service.history(session, chat_id)


@router.post("/chat", response_model=ChatAnswerResponse)
async def send_message(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
    llm=Depends(llm_config),
) -> ChatAnswerResponse:
    """Ask a question. Creates a chat when `chat_id` is omitted."""
    return await service.answer(session, request, llm)


@router.post("/chat/stream")
async def send_message_stream(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
    llm=Depends(llm_config),
) -> StreamingResponse:
    """Same as /chat but streamed as server-sent events: meta, delta..., done (or error).

    The generator opens its own database session: the request-scoped one is closed before the
    body finishes streaming.
    """

    async def events() -> AsyncIterator[str]:
        factory = get_session_factory()
        async with factory() as session:
            try:
                async for kind, value in service.turn(session, request, llm):
                    if kind == "meta":
                        chat_id, citations = value
                        yield sse(
                            "meta",
                            {
                                "chat_id": chat_id,
                                "citations": [c.model_dump(mode="json") for c in citations],
                            },
                        )
                    elif kind == "delta":
                        yield sse("delta", {"text": value})
                    else:
                        yield sse("done", {"message_id": value})
            except (LLMError, AppException) as exc:
                yield sse("error", {"message": getattr(exc, "message", None) or str(exc)})

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(events(), media_type="text/event-stream", headers=headers)
