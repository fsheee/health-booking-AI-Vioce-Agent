"""Specialty vocabulary shared by the Gemini agent and the tool endpoints.

Maps patient phrasing ("cardiologist", "heart doctor", "GP") to the canonical
specialization values stored in the doctors table, so a lookup succeeds no
matter which form reaches the database layer.
"""

import re
from difflib import get_close_matches

# Synonym → canonical DB value. Keys are matched case-insensitively on word
# boundaries, longest key first, so "general practitioner" wins over "gp".
SPECIALTY_SYNONYMS: dict[str, str] = {
    "cardiologist": "Cardiology",
    "cardiology": "Cardiology",
    "heart doctor": "Cardiology",
    "heart specialist": "Cardiology",
    "neurologist": "Neurology",
    "neurology": "Neurology",
    "brain doctor": "Neurology",
    "nerve specialist": "Neurology",
    "dermatologist": "Dermatology",
    "dermatology": "Dermatology",
    "skin doctor": "Dermatology",
    "skin specialist": "Dermatology",
    "general practitioner": "General Physician",
    "general physician": "General Physician",
    "family doctor": "General Physician",
    "primary care": "General Physician",
    "gp": "General Physician",
}

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(rf"\b{re.escape(k)}\b", re.IGNORECASE), v)
    for k, v in sorted(SPECIALTY_SYNONYMS.items(), key=lambda kv: -len(kv[0]))
]


_CUTOFF = 0.75


def normalize_specialty(value: str | None) -> str | None:
    """Map any synonym to its canonical DB value; return the input otherwise."""
    if not value:
        return None
    cleaned = value.strip().lower()
    exact = SPECIALTY_SYNONYMS.get(cleaned)
    if exact:
        return exact
    fuzzy = get_close_matches(cleaned, SPECIALTY_SYNONYMS, n=1, cutoff=_CUTOFF)
    if fuzzy:
        return SPECIALTY_SYNONYMS[fuzzy[0]]
    return value.strip()


def _ngrams(tokens: list[str], max_n: int = 3) -> list[str]:
    """Generate n-grams (1..max_n) from a token list as joined phrases."""
    result = []
    for n in range(1, min(max_n, len(tokens)) + 1):
        for i in range(len(tokens) - n + 1):
            result.append(" ".join(tokens[i : i + n]))
    return result


def extract_specialty_from_text(utterance: str) -> str | None:
    """Find the first specialty mentioned in a free-text utterance.

    Fallback for when the LLM calls find_doctors with empty arguments — the
    patient's own words are scanned so the DB query still gets a filter.
    """
    for pattern, canonical in _PATTERNS:
        if pattern.search(utterance):
            return canonical
    tokens = utterance.strip().lower().split()
    for phrase in _ngrams(tokens):
        fuzzy = get_close_matches(phrase, SPECIALTY_SYNONYMS, n=1, cutoff=_CUTOFF)
        if fuzzy:
            return SPECIALTY_SYNONYMS[fuzzy[0]]
    return None
