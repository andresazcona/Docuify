"""Unit tests for the retrieval pipeline and the answer providers."""

import json

import httpx
import numpy as np
import pytest

from app.core import ValidationError, get_settings
from app.rag.answer import NOT_FOUND_EN, NOT_FOUND_ES, extractive_answer, not_found
from app.rag.chunking import chunk_pages
from app.rag.llm import LLMConfig, LLMError, build_prompt, stream_llm
from app.rag.retrieval import Candidate, Hit, search
from app.rag.text import fold, looks_spanish, tokenize
from app.services.chat_service import resolve_llm_config

PAGES = [
    "Remote work policy. Employees may work remotely up to three days per week. "
    "Managers must approve exceptions in writing.",
    "Vacation. Every employee receives twenty days of paid vacation per year. "
    "Unused days expire in March.",
]


# ---------------------- text ----------------------
def test_tokenize_folds_accents_and_drops_stopwords() -> None:
    assert tokenize("¿Cuál es la política de vacaciones?") == ["politica", "vacaciones"]
    assert fold("Política") == "politica"


def test_looks_spanish() -> None:
    assert looks_spanish("¿Cuántos días de vacaciones hay?")
    assert looks_spanish("el plazo para la entrega")
    assert not looks_spanish("How many vacation days are there?")


# ---------------------- chunking ----------------------
def test_chunks_never_cross_pages_and_keep_page_numbers() -> None:
    chunks = chunk_pages(PAGES, size=80, overlap=20)
    assert {c.page for c in chunks} == {1, 2}
    assert [c.index for c in chunks] == list(range(len(chunks)))
    assert all("Vacation" not in c.text for c in chunks if c.page == 1)
    assert all(len(c.text) <= 160 for c in chunks)


def test_chunk_overlap_repeats_the_tail() -> None:
    text = ". ".join(f"Sentence number {i} about topic {i}" for i in range(12)) + "."
    chunks = chunk_pages([text], size=100, overlap=40)
    assert len(chunks) > 1
    first_words = chunks[1].text.split()[:2]
    assert " ".join(first_words) in chunks[0].text


def test_empty_pages_produce_no_chunks() -> None:
    assert chunk_pages(["", "   "], size=100, overlap=10) == []


# ---------------------- retrieval ----------------------
def _candidates(vectors: list[list[float]] | None = None) -> list[Candidate]:
    texts = [
        "Employees may work remotely up to three days per week.",
        "Every employee receives twenty days of paid vacation per year.",
        "The cafeteria is open from eight to four.",
    ]
    return [
        Candidate(f"c{i}", i + 1, t, None if vectors is None else np.array(vectors[i], np.float32))
        for i, t in enumerate(texts)
    ]


def test_bm25_ranks_the_matching_chunk_first() -> None:
    hits = search("vacation days", _candidates(), top_k=3)
    assert hits[0].chunk_id == "c1"
    assert hits[0].score == 1.0
    assert all(0 < h.score <= 1 for h in hits)


def test_no_lexical_signal_returns_nothing() -> None:
    assert search("quantum entanglement", _candidates(), top_k=3) == []


def test_dense_scores_rescue_a_paraphrase() -> None:
    """The question shares no words with the answer; the embedding still finds it."""
    vectors = [[1, 0], [0, 1], [0.7, 0.7]]
    query = np.array([0, 1.0], np.float32)
    hits = search("time off", _candidates(vectors), top_k=3, query_embedding=query)
    assert hits[0].chunk_id == "c1"


def test_dense_is_skipped_when_a_chunk_lacks_an_embedding() -> None:
    cands = _candidates([[1, 0], [0, 1], [0.5, 0.5]])
    cands[2] = Candidate("c2", 3, cands[2].text, None)
    query = np.array([0, 1.0], np.float32)
    assert search("time off", cands, top_k=3, query_embedding=query) == []


# ---------------------- extractive answers ----------------------
def _hits() -> list[Hit]:
    return [
        Hit(
            "c1", 2, "Vacation. Every employee receives twenty days of paid vacation per year.", 1.0
        ),
        Hit("c0", 1, "Employees may work remotely up to three days per week.", 0.5),
    ]


def test_extractive_answer_cites_the_chunk_it_quotes() -> None:
    answer = extractive_answer("How many vacation days do I get?", _hits())
    assert "twenty days of paid vacation" in answer
    assert answer.rstrip().endswith("[1]")


def test_extractive_answer_not_found_in_both_languages() -> None:
    assert extractive_answer("What is the capital of France?", _hits()) == NOT_FOUND_EN
    assert extractive_answer("¿Cuál es la capital de Francia?", _hits()) == NOT_FOUND_ES
    assert not_found("hola, ¿qué tal?") == NOT_FOUND_ES


# ---------------------- LLM providers (mocked HTTP) ----------------------
def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _sse(*events: dict) -> bytes:
    return b"".join(b"data: " + json.dumps(e).encode() + b"\n\n" for e in events)


async def _collect(config: LLMConfig, handler) -> str:
    async with _client(handler) as client:
        deltas = [d async for d in stream_llm(config, "How many days?", _hits(), [], client=client)]
    return "".join(deltas)


async def test_anthropic_stream_is_parsed_and_sends_the_key_header() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["key"] = request.headers["x-api-key"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            content=_sse(
                {"type": "message_start"},
                {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Twenty "}},
                {
                    "type": "content_block_delta",
                    "delta": {"type": "text_delta", "text": "days [1]."},
                },
            ),
        )

    text = await _collect(LLMConfig("anthropic", "sk-test"), handler)
    assert text == "Twenty days [1]."
    assert seen["key"] == "sk-test"
    assert seen["body"]["stream"] is True
    assert "[1] (page 2)" in seen["body"]["messages"][-1]["content"]


async def test_openai_compatible_stream_uses_the_operator_base_url() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        deltas = _sse(
            {"choices": [{"delta": {"content": "Hi "}}]},
            {"choices": [{"delta": {"content": "there"}}]},
        )
        return httpx.Response(200, content=deltas + b"data: [DONE]\n\n")

    config = LLMConfig("ollama", None, "llama3.1", "http://ollama:11434/v1")
    assert await _collect(config, handler) == "Hi there"
    assert seen["url"] == "http://ollama:11434/v1/chat/completions"


@pytest.mark.parametrize(
    ("status", "needle"),
    [(401, "rejected the API key"), (429, "rate limit"), (500, "returned an error")],
)
async def test_provider_errors_become_safe_messages(status: int, needle: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"error": {"message": "secret detail sk-leak"}})

    with pytest.raises(LLMError) as err:
        await _collect(LLMConfig("openai", "sk-test"), handler)
    assert needle in str(err.value)
    assert "sk-" not in str(err.value)


async def test_missing_key_fails_before_any_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - must not run
        raise AssertionError("no request expected")

    with pytest.raises(LLMError):
        await _collect(LLMConfig("anthropic", None), handler)


def test_prompt_numbers_the_passages_with_their_pages() -> None:
    prompt = build_prompt("How many days?", _hits())
    assert prompt.index("[1] (page 2)") < prompt.index("[2] (page 1)")
    assert prompt.endswith("Question: How many days?")


# ---------------------- choosing the engine ----------------------
@pytest.fixture(autouse=True)
def _fresh_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_default_engine_is_extractive() -> None:
    assert resolve_llm_config(None, None, None) is None


def test_client_can_bring_its_own_key() -> None:
    cfg = resolve_llm_config("Anthropic", "sk-abc", "claude-haiku-4-5-20251001")
    assert (cfg.provider, cfg.api_key, cfg.base_url) == ("anthropic", "sk-abc", None)


@pytest.mark.parametrize(
    ("provider", "key", "model"),
    [("ollama", "k", None), ("openai", None, None), ("openai", "k", "bad model; rm -rf /")],
)
def test_client_cannot_pick_ollama_skip_the_key_or_inject_a_model(provider, key, model) -> None:
    with pytest.raises(ValidationError):
        resolve_llm_config(provider, key, model)


def test_client_keys_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setenv("ALLOW_CLIENT_LLM_KEYS", "false")
    assert resolve_llm_config("anthropic", "sk-abc", None) is None


def test_operator_configured_llm_is_used_when_the_client_sends_nothing(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_BASE_URL", "http://ollama:11434/v1")
    cfg = resolve_llm_config(None, None, None)
    assert (cfg.provider, cfg.base_url) == ("ollama", "http://ollama:11434/v1")
