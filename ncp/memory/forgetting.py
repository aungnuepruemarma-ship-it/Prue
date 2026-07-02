"""Forgetting policy - Decay unused memories.

Tied to consolidation, replay, and lifelong learning.
"""

from dataclasses import dataclass
from typing import List

from ncp.core.entities import Memory
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ForgettingPolicy:
    """Decides which memories to forget.

    Implements importance-based forgetting with consolidation awareness.
    """
    decay_rate: float = 0.01  # Per-hour decay
    importance_threshold: float = 0.3
    min_confidence: float = 0.1

    def should_forget(self, memory: Memory) -> bool:
        """Check if a memory should be forgotten."""
        # Never forget high-importance consolidated memories
        if memory.importance > 0.8 and memory.memory_type == "semantic":
            return False

        # Check confidence threshold
        if memory.confidence < self.min_confidence:
            return True

        # Check importance threshold
        if memory.importance < self.importance_threshold:
            return True

        # Check recency
        if memory.recency < 0.1 and memory.access_count < 2:
            return True

        return False

    def apply_decay(self, memory: Memory, hours: float = 1.0) -> None:
        """Apply time-based decay to memory."""
        memory.recency *= (1 - self.decay_rate) ** hours
        memory.recency = max(0.0, memory.recency)

    def forget_batch(self, memories: List[Memory]) -> List[Memory]:
        """Filter out memories that should be forgotten."""
        kept = [m for m in memories if not self.should_forget(m)]
        forgotten = len(memories) - len(kept)
        if forgotten > 0:
            logger.debug("Forgot %d memories", forgotten)
        return kept
