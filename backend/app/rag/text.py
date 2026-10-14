"""Tokenisation shared by retrieval and extractive answers (English and Spanish)."""

import re
import unicodedata

_WORD = re.compile(r"[a-z0-9]+")

STOPWORDS = frozenset(
    (
        # English
        "a an and are as at be but by can do does for from has have how i if in is it its of on or "
        "that the their then there these this to was were what when where which who why will with you "
        # Spanish
        "el la los las un una unos unas y o de del al en es son por para con sin que como cuando donde "
        "cual quien se su sus lo le les mi tu mas muy pero si no ya hay fue ser esta este estos estas "
        "cuanto cuantos cuanta cuantas"
    ).split()
)


def fold(text: str) -> str:
    """Lowercase and strip accents so 'política' matches 'politica'."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def tokenize(text: str, *, keep_stopwords: bool = False) -> list[str]:
    tokens = _WORD.findall(fold(text))
    return tokens if keep_stopwords else [t for t in tokens if t not in STOPWORDS]


def looks_spanish(text: str) -> bool:
    """Cheap language guess, used only to pick the wording of canned replies."""
    lowered = text.lower()
    if "¿" in lowered or any(c in lowered for c in "ñáéíóú"):
        return True
    words = set(_WORD.findall(fold(text)))
    return len(words & {"el", "la", "los", "que", "como", "cuanto", "para", "por", "es"}) >= 2
