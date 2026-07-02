"""Event subscriber."""

from typing import Callable

from ncp.events.bus import EventBus
from ncp.events.event import Event


class EventSubscriber:
    """Subscribes to events from the event bus."""

    def __init__(self, bus: EventBus, name: str = ""):
        self._bus = bus
        self._name = name

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        self._bus.subscribe(event_type, handler)

    def subscribe_all(self, handler: Callable[[Event], None]) -> None:
        """Subscribe to all events."""
        self._bus.subscribe_all(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type."""
        self._bus.unsubscribe(event_type, handler)
