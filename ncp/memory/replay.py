"""Replay buffer - Select items for replay-based consolidation.

Hippocampal-style fast buffer with slow neocortical store.
"""

import random
from dataclasses import dataclass, field
from typing import List

from ncp.memory.episodic import Episode
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ReplayBuffer:
    """Selects items for replay-based consolidation.

    Supports consolidation scheduling and preserves important traces.
    """
    capacity: int = 1000
    buffer: List[Episode] = field(default_factory=list)

    def add(self, episode: Episode) -> None:
        """Add episode to buffer."""
        self.buffer.append(episode)
        if len(self.buffer) > self.capacity:
            self.buffer.pop(0)

    def sample(self, n: int = 5, strategy: str = "mixed") -> List[Episode]:
        """Sample episodes for replay.

        Strategies:
            - random: Random selection
            - recent: Most recent
            - important: Highest importance
            - mixed: Balanced mix
        """
        if not self.buffer:
            return []

        if strategy == "random":
            return random.sample(self.buffer, min(n, len(self.buffer)))

        elif strategy == "recent":
            return self.buffer[-n:]

        elif strategy == "important":
            scored = sorted(self.buffer,
                          key=lambda e: (1 if e.success else 0, e.duration_ms),
                          reverse=True)
            return scored[:n]

        else:  # mixed
            recent_n = max(1, n // 2)
            random_n = n - recent_n
            recent = self.buffer[-recent_n:] if recent_n > 0 else []
            random_pool = [e for e in self.buffer if e not in recent]
            random_samples = random.sample(
                random_pool or self.buffer, min(random_n, len(random_pool or self.buffer))
            ) if random_n > 0 else []
            return recent + random_samples

    def clear(self) -> None:
        """Clear buffer."""
        self.buffer.clear()

    @property
    def size(self) -> int:
        return len(self.buffer)
