"""Extractive answers: no model, no API key. Returns the document's own sentences, cited."""

import re

from app.rag.retrieval import Hit
from app.rag.text import looks_spanish, tokenize

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

NOT_FOUND_EN = "I could not find that in the document."
NOT_FOUND_ES = "No encontré eso en el documento."


def not_found(question: str) -> str:
    return NOT_FOUND_ES if looks_spanish(question) else NOT_FOUND_EN


def extractive_answer(question: str, hits: list[Hit], *, max_sentences: int = 3) -> str:
    """Pick the sentences that share the most terms with the question.

    Only sentences covering nearly as many question terms as the best one are kept, so a title
    or a sentence that merely repeats one common word does not pad the answer. Each sentence is
    followed by [n], the 1-based position of its chunk in `hits` (the numbering citations use).
    """
    terms = set(tokenize(question))
    if not terms or not hits:
        return not_found(question)

    scored: list[tuple[int, int, int, str]] = []  # (overlap, hit_rank, position, sentence)
    for rank, hit in enumerate(hits):
        for position, sentence in enumerate(_SENTENCE_END.split(" ".join(hit.text.split()))):
            overlap = len(terms & set(tokenize(sentence)))
            if overlap:
                scored.append((overlap, rank, position, sentence))

    if not scored:
        return not_found(question)

    best_overlap = max(item[0] for item in scored)
    relevant = [item for item in scored if item[0] >= max(1, best_overlap * 0.75)]
    relevant.sort(key=lambda item: (-item[0], item[1], item[2]))  # best first, earlier chunks win
    chosen = sorted(relevant[:max_sentences], key=lambda item: (item[1], item[2]))  # read in order
    return "\n".join(f"- {sentence} [{rank + 1}]" for _, rank, _, sentence in chosen)
