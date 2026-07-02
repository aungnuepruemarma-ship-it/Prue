"""Memory ranking - Score items by relevance, confidence, recency, utility."""

from dataclasses import dataclass
from typing import List

from ncp.core.entities import Memory
from ncp.utils.timeutils import utcnow


@dataclass
class MemoryRanker:
    """Scores memory items by multiple factors."""

    relevance_weight: float = 0.4
    confidence_weight: float = 0.2
    recency_weight: float = 0.2
    utility_weight: float = 0.2

    def score(self, memory: Memory, query: str = "") -> float:
        """Calculate composite score for a memory item."""
        # Relevance score
        relevance = memory.score_relevance(query) if query else 0.5

        # Confidence score
        confidence = memory.confidence

        # Recency score (decay over time)
        recency = memory.recency
        if memory.last_accessed:
            age_hours = (utcnow() - memory.last_accessed).total_seconds() / 3600
            recency = max(0.0, 1.0 - age_hours / 168)  # Decay over 1 week

        # Utility score (based on access count)
        utility = min(1.0, memory.access_count / 10.0)

        # Weighted combination
        score = (
            self.relevance_weight * relevance +
            self.confidence_weight * confidence +
            self.recency_weight * recency +
            self.utility_weight * utility
        )

        return score

    def rank(self, memories: List[Memory], query: str = "",
             top_k: int = 10) -> List[Memory]:
        """Rank memories by relevance to query."""
        scored = [(m, self.score(m, query)) for m in memories]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [m for m, _ in scored[:top_k]]
