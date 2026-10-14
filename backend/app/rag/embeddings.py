"""Optional dense embeddings. Without them retrieval is lexical (BM25) only."""

from typing import Protocol

import numpy as np


class Embedder(Protocol):
    name: str

    def embed(self, texts: list[str]) -> np.ndarray:
        """Return an (n, dim) float32 array of L2-normalised vectors."""


class FastEmbedEmbedder:
    """Local ONNX embeddings through fastembed: no API key, runs on CPU."""

    def __init__(self, model_name: str):
        from fastembed import TextEmbedding  # optional dependency: pip install ".[embeddings]"

        self.name = model_name
        self._model = TextEmbedding(model_name=model_name)

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = np.array(list(self._model.embed(texts)), dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.clip(norms, 1e-12, None)


_cache: dict[str, Embedder] = {}


def get_embedder(provider: str, model_name: str) -> Embedder | None:
    if provider == "none":
        return None
    if provider != "fastembed":
        raise ValueError(f"Unknown embedding provider: {provider}")
    if model_name not in _cache:
        _cache[model_name] = FastEmbedEmbedder(model_name)
    return _cache[model_name]


def to_bytes(vector: np.ndarray) -> bytes:
    return np.asarray(vector, dtype=np.float32).tobytes()


def from_bytes(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)
