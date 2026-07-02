"""Event registry for tracking handlers and subscriptions."""

from collections import defaultdict
from typing import Callable, Dict, List, Set

from ncp.events.event import Event


class EventRegistry:
    """Registry for event subscriptions."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable[[Event], None]]] = defaultdict(list)
        self._global_handlers: List[Callable[[Event], None]] = []
        self._sources: Set[str] = set()

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: Callable[[Event], None]) -> None:
        """Subscribe to all events."""
        self._global_handlers.append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    def get_handlers(self, event_type: str) -> List[Callable[[Event], None]]:
        """Get handlers for an event type."""
        return self._handlers.get(event_type, []) + self._global_handlers

    def list_subscriptions(self) -> Dict[str, int]:
        """List subscription counts by event type."""
        return {
            event_type: len(handlers)
            for event_type, handlers in self._handlers.items()
        }

    def clear(self) -> None:
        """Clear all subscriptions."""
        self._handlers.clear()
        self._global_handlers.clear()
