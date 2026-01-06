"""Chat endpoints (placeholder)."""
from fastapi import APIRouter, status

from app.core.errors import NotFoundError, ServiceUnavailableError
from app.domain.schemas import (
    ChatAnswerResponse,
    ChatCreateRequest,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
)

router = APIRouter(prefix="/chats", tags=["chat"])


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(request: ChatCreateRequest) -> ChatResponse:
    """
    Create a new chat for a document.

    Initializes a new chat session for conversing with a document.

    **Status: Not Implemented** - Returns 501 for now.
    """
    raise ServiceUnavailableError("Chat creation not yet implemented")


@router.get("/{chat_id}", response_model=ChatHistoryResponse, status_code=status.HTTP_200_OK)
async def get_chat(chat_id: str) -> ChatHistoryResponse:
    """
    Get chat details and message history.

    Returns complete chat history with all messages and citations.

    **Status: Not Implemented** - Returns 501 for now.
    """
    raise NotFoundError("Chat not found or feature not yet implemented")


@router.post("/chat", response_model=ChatAnswerResponse, status_code=status.HTTP_200_OK)
async def send_message(request: ChatRequest) -> ChatAnswerResponse:
    """
    Send a message in a chat.

    Sends user message, performs RAG retrieval, generates answer with citations.
    Creates new chat if chat_id not provided.

    **Status: Not Implemented** - Returns 501 for now.
    """
    raise ServiceUnavailableError("Chat messaging not yet implemented")


@router.post("/chat/stream", status_code=status.HTTP_200_OK)
async def send_message_stream(request: ChatRequest) -> None:
    """
    Send a message with streaming response (SSE).

    **Status: Not Implemented** - Placeholder for future streaming support.
    """
    raise ServiceUnavailableError("Streaming chat not yet implemented")
