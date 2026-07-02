"""Working memory - Fast, short-lived memory buffer.

Recent tokens, events, intermediate traces.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Deque, Dict, List

from ncp.core.entities import Entity
from ncp.utils.timeutils import utcnow


@dataclass
class WorkingMemory:
    """Fast, short-lived memory buffer.

    FIFO buffer with size limit. Items age out automatically.
    """
    max_items: int = 1024
    ttl_seconds: float = 300.0

    _buffer: Deque[Entity] = field(default_factory=deque, repr=False)
    _timestamps: Dict[int, datetime] = field(default_factory=dict, repr=False)
    _sequence: int = field(default=0, repr=False)

    def add(self, item: Entity) -> None:
        """Add item to working memory."""
        if len(self._buffer) >= self.max_items:
            self._buffer.popleft()
        self._buffer.append(item)
        self._sequence += 1
        self._timestamps[self._sequence] = utcnow()

    def get_recent(self, n: int = 10) -> List[Entity]:
        """Get n most recent items."""
        return list(self._buffer)[-n:]

    def get_all(self) -> List[Entity]:
        """Get all items."""
        return list(self._buffer)

    def clear(self) -> None:
        """Clear working memory."""
        self._buffer.clear()
        self._timestamps.clear()

    def cleanup_expired(self) -> int:
        """Remove expired items. Returns count removed."""
        cutoff = utcnow() - timedelta(seconds=self.ttl_seconds)
        removed = 0
        while self._buffer:
            oldest_seq = min(self._timestamps.keys()) if self._timestamps else None
            if oldest_seq and self._timestamps.get(oldest_seq, utcnow()) < cutoff:
                self._buffer.popleft()
                del self._timestamps[oldest_seq]
                removed += 1
            else:
                break
        return removed

    @property
    def size(self) -> int:
        return len(self._buffer)
