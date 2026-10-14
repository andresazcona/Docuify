"""Hybrid retrieval over the chunks of ONE document: BM25 plus optional cosine similarity.

A document has at most a few thousand chunks, so scoring them in process is fast and avoids
running a vector database. The two rankings are merged with reciprocal rank fusion.
"""

import math
from collections import Counter
from dataclasses import dataclass

import numpy as np

from app.rag.text import tokenize

_RRF_K = 60


@dataclass(frozen=True)
class Candidate:
    chunk_id: str
    page: int | None
    text: str
    embedding: np.ndarray | None = None


@dataclass(frozen=True)
class Hit:
    chunk_id: str
    page: int | None
    text: str
    score: float  # 0..1, relative to the best hit of this query


def _bm25_scores(query_terms: list[str], docs: list[list[str]], k1=1.5, b=0.75) -> np.ndarray:
    n = len(docs)
    avg_len = (sum(len(d) for d in docs) / n) if n else 0.0
    doc_freq: Counter[str] = Counter()
    for d in docs:
        doc_freq.update(set(d))
    scores = np.zeros(n, dtype=np.float64)
    for i, d in enumerate(docs):
        tf = Counter(d)
        for term in query_terms:
            if term not in tf:
                continue
            idf = math.log(1 + (n - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
            freq = tf[term]
            norm = 1 - b + b * len(d) / (avg_len or 1)
            scores[i] += idf * freq * (k1 + 1) / (freq + k1 * norm)
    return scores


def _ranks(scores: np.ndarray) -> dict[int, int]:
    order = np.argsort(-scores, kind="stable")
    return {int(idx): rank for rank, idx in enumerate(order) if scores[idx] > 0}


def search(
    query: str,
    candidates: list[Candidate],
    *,
    top_k: int,
    query_embedding: np.ndarray | None = None,
) -> list[Hit]:
    """Return up to `top_k` hits, best first. Chunks with no signal at all are dropped."""
    if not candidates:
        return []

    lexical = _bm25_scores(tokenize(query), [tokenize(c.text) for c in candidates])
    fused: dict[int, float] = {i: 1 / (_RRF_K + r) for i, r in _ranks(lexical).items()}

    if query_embedding is not None and all(c.embedding is not None for c in candidates):
        matrix = np.vstack([c.embedding for c in candidates])
        for i, rank in _ranks(matrix @ query_embedding).items():
            fused[i] = fused.get(i, 0.0) + 1 / (_RRF_K + rank)

    best = sorted(fused.items(), key=lambda item: item[1], reverse=True)[:top_k]
    if not best:
        return []
    top = best[0][1]
    return [
        Hit(candidates[i].chunk_id, candidates[i].page, candidates[i].text, round(s / top, 4))
        for i, s in best
    ]
