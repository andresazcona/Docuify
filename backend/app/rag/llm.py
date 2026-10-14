"""Optional LLM answers with streaming. Providers: Anthropic, OpenAI and OpenAI-compatible (Ollama).

Security notes:
* A client may bring its own API key per request, but never its own base URL: letting callers
  choose where the server sends requests would be an SSRF hole. Custom base URLs (Ollama,
  vLLM...) are configured by the operator through LLM_BASE_URL.
* Keys are used for the single outgoing request and are never logged or stored.
"""

import json
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx

from app.rag.retrieval import Hit

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_BASE = "https://api.openai.com/v1"
DEFAULT_MODELS = {
    "anthropic": "claude-haiku-4-5-20251001",
    "openai": "gpt-4o-mini",
    "ollama": "llama3.1",
}
_MODEL_RE = re.compile(r"^[A-Za-z0-9._:/-]{1,80}$")

SYSTEM_PROMPT = (
    "You answer questions about a document using ONLY the numbered passages provided. "
    "Cite the passages you use as [1], [2]... right after the claim. "
    "If the passages do not contain the answer, say so plainly instead of guessing. "
    "Reply in the language of the question. Be concise."
)


class LLMError(Exception):
    """The provider refused or failed; the message is safe to show to the user."""


@dataclass(frozen=True)
class LLMConfig:
    provider: str  # anthropic | openai | ollama
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None  # operator-configured only
    temperature: float = 0.2
    max_tokens: int = 1024

    @property
    def resolved_model(self) -> str:
        return self.model or DEFAULT_MODELS[self.provider]


def valid_model_name(name: str) -> bool:
    return bool(_MODEL_RE.match(name))


def build_prompt(question: str, hits: list[Hit]) -> str:
    passages = "\n\n".join(
        f"[{i}] (page {h.page or '?'}) {' '.join(h.text.split())}" for i, h in enumerate(hits, 1)
    )
    return f"Passages:\n{passages}\n\nQuestion: {question}"


async def stream_llm(
    config: LLMConfig,
    question: str,
    hits: list[Hit],
    history: list[tuple[str, str]],
    *,
    client: httpx.AsyncClient | None = None,
) -> AsyncIterator[str]:
    """Yield text deltas. `history` is a list of (role, content) from earlier turns."""
    messages = [{"role": r, "content": c} for r, c in history] + [
        {"role": "user", "content": build_prompt(question, hits)}
    ]
    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0))
    try:
        if config.provider == "anthropic":
            stream = _anthropic(client, config, messages)
        else:
            stream = _openai_compatible(client, config, messages)
        async for delta in stream:
            yield delta
    finally:
        if owns_client:
            await client.aclose()


async def _raise_for_status(response: httpx.Response, provider: str) -> None:
    if response.status_code < 400:
        return
    await response.aread()
    if response.status_code in (401, 403):
        raise LLMError(f"The {provider} API rejected the API key.")
    if response.status_code == 429:
        raise LLMError(f"The {provider} API rate limit was reached. Try again in a moment.")
    raise LLMError(f"The {provider} API returned an error ({response.status_code}).")


async def _anthropic(client: httpx.AsyncClient, cfg: LLMConfig, messages: list[dict]):
    if not cfg.api_key:
        raise LLMError("An Anthropic API key is required.")
    body = {
        "model": cfg.resolved_model,
        "max_tokens": cfg.max_tokens,
        "temperature": cfg.temperature,
        "system": SYSTEM_PROMPT,
        "messages": messages,
        "stream": True,
    }
    headers = {"x-api-key": cfg.api_key, "anthropic-version": "2023-06-01"}
    try:
        async with client.stream("POST", ANTHROPIC_URL, json=body, headers=headers) as response:
            await _raise_for_status(response, "Anthropic")
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                event = json.loads(line[5:])
                if event.get("type") == "content_block_delta":
                    text = event.get("delta", {}).get("text")
                    if text:
                        yield text
    except httpx.HTTPError as exc:
        raise LLMError("Could not reach the Anthropic API.") from exc


async def _openai_compatible(client: httpx.AsyncClient, cfg: LLMConfig, messages: list[dict]):
    base = (cfg.base_url or OPENAI_BASE).rstrip("/")
    if cfg.provider == "openai" and not cfg.api_key:
        raise LLMError("An OpenAI API key is required.")
    body = {
        "model": cfg.resolved_model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "stream": True,
    }
    headers = {"Authorization": f"Bearer {cfg.api_key}"} if cfg.api_key else {}
    try:
        async with client.stream(
            "POST", f"{base}/chat/completions", json=body, headers=headers
        ) as response:
            await _raise_for_status(response, cfg.provider)
            async for line in response.aiter_lines():
                if not line.startswith("data:") or line.strip() == "data: [DONE]":
                    continue
                choices = json.loads(line[5:]).get("choices") or [{}]
                text = choices[0].get("delta", {}).get("content")
                if text:
                    yield text
    except httpx.HTTPError as exc:
        raise LLMError(f"Could not reach the {cfg.provider} server.") from exc
