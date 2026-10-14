"""End to end: upload a real PDF, ask questions, read the citations."""

import json

import pytest
from httpx import AsyncClient

from app.rag.llm import LLMError
from tests.pdfs import make_pdf

PAGES = [
    "Remote work policy.\n\nEmployees may work remotely up to three days per week. "
    "Managers must approve exceptions in writing.",
    "Vacation.\n\nEvery employee receives twenty days of paid vacation per year. "
    "Unused days expire in March.",
]
API = "/api/v1"


async def upload(client: AsyncClient, data: bytes) -> dict:
    files = {"file": ("handbook.pdf", data, "application/pdf")}
    response = await client.post(f"{API}/documents/upload", files=files)
    assert response.status_code == 202, response.text
    return response.json()


@pytest.fixture
async def doc(client: AsyncClient) -> str:
    created = await upload(client, make_pdf(PAGES))
    assert created["status"] == "READY"
    return created["document_id"]


def sse_events(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.strip().split("\n\n"):
        name, data = block.split("\n", 1)
        events.append((name.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return events


async def test_indexing_records_pages_and_chunks(client: AsyncClient, doc: str) -> None:
    meta = (await client.get(f"{API}/documents/{doc}")).json()["metadata"]
    assert meta["pages"] == 2
    assert meta["chunks"] >= 2


async def test_answer_quotes_the_document_and_cites_the_page(client: AsyncClient, doc: str) -> None:
    response = await client.post(
        f"{API}/chats/chat",
        json={"document_id": doc, "message": "How many vacation days do I get?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "twenty days of paid vacation" in body["answer"]
    assert body["citations"][0]["page"] == 2
    assert 0 < body["citations"][0]["score"] <= 1
    assert body["chat_id"].startswith("chat_")


async def test_history_keeps_the_conversation_in_order(client: AsyncClient, doc: str) -> None:
    first = (
        await client.post(
            f"{API}/chats/chat", json={"document_id": doc, "message": "Vacation days?"}
        )
    ).json()
    await client.post(
        f"{API}/chats/chat",
        json={"document_id": doc, "chat_id": first["chat_id"], "message": "And remote work?"},
    )
    history = (await client.get(f"{API}/chats/{first['chat_id']}")).json()
    roles = [m["role"] for m in history["messages"]]
    assert roles == ["user", "assistant", "user", "assistant"]
    assert history["messages"][1]["citations"][0]["page"] == 2


async def test_a_short_follow_up_reuses_the_previous_question_for_retrieval(
    client: AsyncClient, doc: str
) -> None:
    first = (
        await client.post(
            f"{API}/chats/chat", json={"document_id": doc, "message": "Remote work days"}
        )
    ).json()
    follow = await client.post(
        f"{API}/chats/chat",
        json={"document_id": doc, "chat_id": first["chat_id"], "message": "per week?"},
    )
    assert follow.json()["citations"][0]["page"] == 1


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("What is the capital of France?", "I could not find that in the document."),
        ("¿Cuál es la capital de Francia?", "No encontré eso en el documento."),
    ],
)
async def test_unanswerable_questions_say_so(
    client: AsyncClient, doc: str, question: str, expected: str
) -> None:
    body = (
        await client.post(f"{API}/chats/chat", json={"document_id": doc, "message": question})
    ).json()
    assert body["answer"] == expected
    assert body["citations"] == []


async def test_stream_emits_meta_deltas_and_done(client: AsyncClient, doc: str) -> None:
    response = await client.post(
        f"{API}/chats/chat/stream", json={"document_id": doc, "message": "Vacation days?"}
    )
    assert response.headers["content-type"].startswith("text/event-stream")
    events = sse_events(response.text)
    assert events[0][0] == "meta" and events[-1][0] == "done"
    assert events[0][1]["citations"][0]["page"] == 2
    text = "".join(data["text"] for name, data in events if name == "delta")
    assert "twenty days" in text
    history = (await client.get(f"{API}/chats/{events[0][1]['chat_id']}")).json()
    assert history["messages"][-1]["content"] == text


async def test_stream_reports_errors_as_events(client: AsyncClient) -> None:
    response = await client.post(
        f"{API}/chats/chat/stream", json={"document_id": "doc_missing", "message": "hello?"}
    )
    ((name, data),) = sse_events(response.text)
    assert name == "error" and "not found" in data["message"].lower()


async def test_documents_that_could_not_be_read_cannot_be_chatted_with(client: AsyncClient) -> None:
    junk = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\nnot really a pdf\n%%EOF\n"
    created = await upload(client, junk)
    assert created["status"] == "FAILED"
    document = (await client.get(f"{API}/documents/{created['document_id']}")).json()
    assert "could not be read" in document["error_message"]
    response = await client.post(
        f"{API}/chats/chat", json={"document_id": created["document_id"], "message": "anything"}
    )
    assert response.status_code == 409


async def test_a_pdf_without_text_is_rejected_with_a_clear_reason(client: AsyncClient) -> None:
    created = await upload(client, make_pdf(["", ""]))
    assert created["status"] == "FAILED"
    document = (await client.get(f"{API}/documents/{created['document_id']}")).json()
    assert "no extractable text" in document["error_message"]


async def test_chat_from_another_document_is_refused(client: AsyncClient, doc: str) -> None:
    other = (await upload(client, make_pdf(["Cafeteria hours are eight to four."])))["document_id"]
    chat = (
        await client.post(f"{API}/chats/chat", json={"document_id": doc, "message": "Vacation?"})
    ).json()
    response = await client.post(
        f"{API}/chats/chat",
        json={"document_id": other, "chat_id": chat["chat_id"], "message": "Cafeteria?"},
    )
    assert response.status_code == 422


async def test_deleting_a_document_removes_its_chats(client: AsyncClient, doc: str) -> None:
    chat = (
        await client.post(f"{API}/chats/chat", json={"document_id": doc, "message": "Vacation?"})
    ).json()
    assert (await client.delete(f"{API}/documents/{doc}")).status_code == 204
    assert (await client.get(f"{API}/chats/{chat['chat_id']}")).status_code == 404


# ---------------------- bring your own key ----------------------
async def test_a_client_key_switches_the_answer_to_the_llm(
    client: AsyncClient, doc: str, monkeypatch
) -> None:
    seen = {}

    async def fake_stream(config, question, hits, history, **_):
        seen["config"], seen["hits"] = config, hits
        for piece in ("Twenty ", "days [1]."):
            yield piece

    monkeypatch.setattr("app.services.chat_service.stream_llm", fake_stream)
    headers = {"X-LLM-Provider": "anthropic", "X-LLM-Key": "sk-secret-value"}
    response = await client.post(
        f"{API}/chats/chat", json={"document_id": doc, "message": "Vacation days?"}, headers=headers
    )
    assert response.json()["answer"] == "Twenty days [1]."
    assert seen["config"].provider == "anthropic" and seen["hits"][0].page == 2
    assert "sk-secret-value" not in response.text


async def test_llm_failures_surface_as_503_without_the_key(
    client: AsyncClient, doc: str, monkeypatch
) -> None:
    async def failing_stream(*args, **kwargs):
        raise LLMError("The Anthropic API rejected the API key.")
        yield  # pragma: no cover

    monkeypatch.setattr("app.services.chat_service.stream_llm", failing_stream)
    headers = {"X-LLM-Provider": "anthropic", "X-LLM-Key": "sk-bad"}
    response = await client.post(
        f"{API}/chats/chat", json={"document_id": doc, "message": "Vacation days?"}, headers=headers
    )
    assert response.status_code == 503
    assert "rejected the API key" in response.text and "sk-bad" not in response.text


async def test_the_client_cannot_choose_the_endpoint(client: AsyncClient, doc: str) -> None:
    for provider in ("ollama", "evil"):
        response = await client.post(
            f"{API}/chats/chat",
            json={"document_id": doc, "message": "Vacation days?"},
            headers={"X-LLM-Provider": provider, "X-LLM-Key": "k"},
        )
        assert response.status_code == 422


async def test_meta_advertises_the_available_features(client: AsyncClient) -> None:
    features = (await client.get(f"{API}/meta")).json()["features"]
    assert features["streaming_chat"] is True
    assert features["llm_answers"] is False and features["client_llm_keys"] is True
