"""Worker scheduler."""

from dataclasses import dataclass, field
from typing import Callable, List

from ncp.events.bus import EventBus
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class WorkerScheduler:
    """Schedules background workers."""

    event_bus: EventBus
    workers: List[Callable] = field(default_factory=list)

    def register_worker(self, name: str, handler: Callable,
                        event_types: List[str]) -> None:
        """Register a worker for event types."""
        for event_type in event_types:
            self.event_bus.subscribe(event_type, handler)
        self.workers.append(handler)
        logger.info("Registered worker %s for %s", name, event_types)

    def start_all(self) -> None:
        """Start all workers."""
        logger.info("Starting %d workers", len(self.workers))
