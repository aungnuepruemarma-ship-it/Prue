"""Event bus - Central communication hub.

Event flow:
    Planner Finished -> Event Bus -> Memory -> Monitoring -> Research -> Workers
No module directly calls another. Everything emits events.
"""

import logging
from threading import RLock
from typing import Callable, Dict, Optional

from ncp.events.event import Event
from ncp.events.queue import EventQueue
from ncp.events.registry import EventRegistry

logger = logging.getLogger(__name__)


class EventBus:
    """Central event bus for decoupled communication.

    All subsystems communicate through the event bus.
    Direct module-to-module calls are avoided.
    """

    def __init__(self, queue_size: int = 100000):
        self._queue = EventQueue(max_size=queue_size)
        self._registry = EventRegistry()
        self._running = False
        self._lock = RLock()
        self._subscribers: Dict[str, int] = {}
        logger.info("EventBus initialized (queue_size=%d)", queue_size)

    def publish(self, event: Optional[Event] = None, **kwargs) -> bool:
        """Publish an event to the bus.

        Accepts either a prebuilt Event or keyword fields
        (type=..., payload=..., source=...) from which one is constructed —
        both call styles are used throughout the platform.
        """
        if event is None:
            event = Event(
                type=kwargs.get("type", ""),
                payload=kwargs.get("payload") or {},
                source=kwargs.get("source"),
                priority=kwargs.get("priority", 0),
                correlation_id=kwargs.get("correlation_id"),
            )
        if not self._running:
            logger.warning("EventBus not running, event dropped: %s", event.type)
            return False
        success = self._queue.put(event)
        if success:
            logger.debug("Published event: %s from %s", event.type, event.source)
        else:
            logger.warning("Event queue full, event dropped: %s", event.type)
        return success

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        with self._lock:
            self._registry.subscribe(event_type, handler)
            self._subscribers[event_type] = self._subscribers.get(event_type, 0) + 1
        logger.debug("Subscribed to %s", event_type)

    def subscribe_all(self, handler: Callable[[Event], None]) -> None:
        """Subscribe to all events."""
        self._registry.subscribe_all(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type."""
        with self._lock:
            self._registry.unsubscribe(event_type, handler)
            if event_type in self._subscribers:
                self._subscribers[event_type] -= 1

    def dispatch(self, event: Event) -> None:
        """Dispatch an event to all subscribers."""
        handlers = self._registry.get_handlers(event.type)
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error("Error dispatching event %s: %s", event.type, e)

    def process_one(self) -> Optional[Event]:
        """Process one event from the queue."""
        event = self._queue.get()
        if event:
            self.dispatch(event)
        return event

    def start(self) -> None:
        """Start the event bus."""
        self._running = True
        logger.info("EventBus started")

    def stop(self) -> None:
        """Stop the event bus."""
        self._running = False
        logger.info("EventBus stopped")

    def flush(self) -> None:
        """Process all remaining events in queue."""
        logger.info("Flushing event queue (%d events)", self._queue.size())
        count = 0
        while not self._queue.is_empty():
            event = self._queue.get()
            if event:
                self.dispatch(event)
                count += 1
        logger.info("Flushed %d events", count)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def queue_size(self) -> int:
        return self._queue.size()

    @property
    def subscription_count(self) -> int:
        return sum(self._subscribers.values())
