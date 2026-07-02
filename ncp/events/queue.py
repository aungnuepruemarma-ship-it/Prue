"""Event queue with priority support."""

import heapq
from dataclasses import dataclass
from typing import List, Optional

from ncp.events.event import Event


@dataclass(order=False)
class PrioritizedEvent:
    """Wrapper for priority queue ordering."""
    priority: int
    sequence: int
    event: Event

    def __lt__(self, other: "PrioritizedEvent") -> bool:
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.sequence < other.sequence


class EventQueue:
    """Priority-based event queue."""

    def __init__(self, max_size: int = 100000):
        self._queue: List[PrioritizedEvent] = []
        self._max_size = max_size
        self._sequence = 0
        self._count = 0

    def put(self, event: Event) -> bool:
        """Add event to queue. Returns False if full."""
        if self._count >= self._max_size:
            return False
        self._sequence += 1
        item = PrioritizedEvent(
            priority=event.priority,
            sequence=self._sequence,
            event=event,
        )
        heapq.heappush(self._queue, item)
        self._count += 1
        return True

    def get(self) -> Optional[Event]:
        """Get highest priority event."""
        if not self._queue:
            return None
        item = heapq.heappop(self._queue)
        self._count -= 1
        return item.event

    def peek(self) -> Optional[Event]:
        """Peek at highest priority event without removing."""
        if not self._queue:
            return None
        return self._queue[0].event

    def size(self) -> int:
        return self._count

    def is_empty(self) -> bool:
        return self._count == 0

    def is_full(self) -> bool:
        return self._count >= self._max_size

    def clear(self) -> None:
        self._queue.clear()
        self._count = 0
