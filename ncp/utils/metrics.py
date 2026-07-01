from __future__ import annotations
from collections import Counter
from math import log2
from typing import Iterable

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
