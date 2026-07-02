"""Task scheduler for execution ordering."""

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from ncp.core.entities import Task
from ncp.events.bus import EventBus
from ncp.interfaces.planner import PlannerInterface
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Scheduler:
    """Decides execution order and queues tasks.

    Supports pause/resume for async workers later.
    """
    event_bus: EventBus
    planner: Optional[PlannerInterface] = None
    max_workers: int = 8

    _queue: deque = field(default_factory=deque, repr=False)
    _running: bool = field(default=False, repr=False)
    _paused: bool = field(default=False, repr=False)

    def start(self) -> None:
        """Start the scheduler."""
        self._running = True
        self._paused = False
        logger.info("Scheduler started (workers=%d)", self.max_workers)

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        logger.info("Scheduler stopped")

    def pause(self) -> None:
        """Pause task execution."""
        self._paused = True
        logger.info("Scheduler paused")

    def resume(self) -> None:
        """Resume task execution."""
        self._paused = False
        logger.info("Scheduler resumed")

    def submit(self, task: Task) -> None:
        """Submit a task for execution."""
        self._queue.append(task)
        logger.debug("Task submitted: %s", task.name)

    def get_next(self) -> Optional[Task]:
        """Get next task from queue."""
        if self._queue:
            return self._queue.popleft()
        return None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def queue_size(self) -> int:
        return len(self._queue)
