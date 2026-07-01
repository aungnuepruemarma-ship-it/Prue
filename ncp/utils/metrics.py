from __future__ import annotations

from collections import Counter
from math import log2
from typing import Any, Iterable


def tokenize(text: str) -> set[str]:
    return {t.lower().strip(".,;:!?()[]\"'") for t in str(text).split() if t.strip()}

def token_overlap(a: str, b: str) -> float:
    """Fraction of a's tokens that also appear in b, in [0, 1]."""
    ta, tb = tokenize(a), tokenize(b)
    if not ta:
        return 0.0
    return len(ta & tb) / len(ta)

def normalized_entropy(values: Iterable[str]) -> float:
    items = [v for v in values if v is not None]
    if not items:
        return 0.0
    counts = Counter(items)
    total = sum(counts.values())
    if total <= 1:
        return 0.0
    entropy = 0.0
    for c in counts.values():
        p = c / total
        entropy -= p * log2(p)
    return entropy / log2(len(counts)) if len(counts) > 1 else 0.0

def approximate_cost(num_entities: int, num_relations: int, num_active: int) -> float:
    return 0.2 * num_entities + 0.1 * num_relations + 0.05 * num_active

def candidate_text(candidate: Any) -> str:
    """Flatten a candidate's descriptive fields into one matchable string.

    Params are deliberately excluded: they frequently echo the goal string
    verbatim, which would hand every candidate full goal relevance.
    """
    return " ".join([candidate.name, candidate.task_type, candidate.description])
