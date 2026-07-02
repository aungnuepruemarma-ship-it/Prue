"""Default executor implementation."""

from dataclasses import dataclass

from ncp.core.entities import Result, Task
from ncp.events.bus import EventBus
from ncp.interfaces.executor import ExecutorInterface
from ncp.interfaces.router import RouterInterface
from ncp.utils.config import Config
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Executor(ExecutorInterface):
    """Default task executor."""
    router: RouterInterface
    event_bus: EventBus
    config: Config

    def execute(self, task: Task) -> Result:
        """Execute a task."""
        logger.info("Executing task: %s", task.name)

        # Emit started event
        from ncp.events.event import EventType
        self.event_bus.publish(
            type=EventType.EXECUTOR_STARTED.value,
            payload={"task_id": str(task.id), "task_name": task.name},
        )

        # Select capability and execute
        try:
            capability = self.router.route(task)
            result = Result(
                task_id=task.id,
                status="success",
                output=f"Executed with {capability.name}",
                execution_time_ms=100.0,
                confidence=0.9,
            )
            self.event_bus.publish(
                type=EventType.EXECUTOR_FINISHED.value,
                payload={"task_id": str(task.id), "status": "success"},
            )
        except Exception as e:
            logger.error("Task execution failed: %s", e)
            result = Result(
                task_id=task.id,
                status="failure",
                error=str(e),
                confidence=0.0,
            )
            self.event_bus.publish(
                type=EventType.EXECUTOR_FAILED.value,
                payload={"task_id": str(task.id), "error": str(e)},
            )

        return result

    def can_execute(self, task: Task) -> bool:
        """Check if this executor can handle a task."""
        return True
