"""Event dispatcher - Routes events to workers."""

import logging
from typing import Callable, Dict, List

from ncp.events.bus import EventBus
from ncp.events.event import Event

logger = logging.getLogger(__name__)


class EventDispatcher:
    """Dispatches events to appropriate workers.

    Routes events to workers based on event type.
    """

    def __init__(self, bus: EventBus):
        self._bus = bus
        self._routes: Dict[str, List[str]] = {}  # event_type -> worker_names
        self._workers: Dict[str, Callable[[Event], None]] = {}

    def register_worker(self, name: str, handler: Callable[[Event], None],
                        event_types: List[str]) -> None:
        """Register a worker for event types."""
        self._workers[name] = handler
        for event_type in event_types:
            if event_type not in self._routes:
                self._routes[event_type] = []
            self._routes[event_type].append(name)
            self._bus.subscribe(event_type, handler)
        logger.debug("Registered worker %s for %s", name, event_types)

    def get_workers_for(self, event_type: str) -> List[str]:
        """Get workers subscribed to an event type."""
        return self._routes.get(event_type, [])
