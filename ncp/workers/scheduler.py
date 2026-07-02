"""Worker scheduler."""

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from ncp.events.bus import EventBus
from ncp.events.dispatcher import EventDispatcher
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class WorkerScheduler:
    """Schedules background workers.

    Event routing is delegated to an :class:`EventDispatcher`, which keeps
    the event-type -> worker mapping queryable.
    """

    event_bus: EventBus
    workers: List[Callable] = field(default_factory=list)
    dispatcher: Optional[EventDispatcher] = None

    def __post_init__(self):
        if self.dispatcher is None:
            self.dispatcher = EventDispatcher(self.event_bus)

    def register_worker(self, name: str, handler: Callable,
                        event_types: List[str]) -> None:
        """Register a worker for event types."""
        self.dispatcher.register_worker(name, handler, event_types)
        self.workers.append(handler)
        logger.info("Registered worker %s for %s", name, event_types)

    def start_all(self) -> None:
        """Start all workers."""
        logger.info("Starting %d workers", len(self.workers))
