"""Vector store - Semantic retrieval support."""

import math
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class VectorStore:
    """In-memory vector store for embeddings."""

    vectors: Dict[str, List[float]] = field(default_factory=dict)

    def store_embedding(self, key: str, vector: List[float]) -> None:
        self.vectors[key] = vector

    def search(self, query: List[float], top_k: int = 10) -> List[str]:
        """Nearest neighbor search using cosine similarity."""
        scored = []
        for key, vec in self.vectors.items():
            sim = self._cosine_similarity(query, vec)
            scored.append((key, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [k for k, _ in scored[:top_k]]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
