"""Event publisher."""

from typing import Any, Dict, Optional
from uuid import UUID

from ncp.events.bus import EventBus
from ncp.events.event import Event, EventType


class EventPublisher:
    """Publishes events to the event bus."""

    def __init__(self, bus: EventBus, source: str = ""):
        self._bus = bus
        self._source = source

    def publish(self, event_type: EventType, payload: Dict[str, Any],
                priority: int = 0, correlation_id: Optional[UUID] = None) -> Event:
        """Publish an event."""
        event = Event.create(
            event_type=event_type,
            payload=payload,
            source=self._source,
            priority=priority,
            correlation_id=correlation_id,
        )
        self._bus.publish(event)
        return event

    def set_source(self, source: str) -> None:
        """Set the event source identifier."""
        self._source = source
