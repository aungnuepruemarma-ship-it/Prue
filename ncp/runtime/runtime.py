"""Runtime - Central orchestrator.

Runtime owns every subsystem. Nothing owns Runtime.

Constructor:
    Runtime(planner, router, executor, memory, storage, constraints, simulator, research, events)

No global variables.
"""

from dataclasses import dataclass
from typing import List
from uuid import uuid4

from ncp.core.entities import Goal, Result, Task
from ncp.runtime.container import Container
from ncp.runtime.lifecycle import LifecycleManager
from ncp.runtime.scheduler import Scheduler
from ncp.runtime.state import RuntimeState
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Runtime:
    """Central orchestrator for NCP.

    Responsibilities:
    - Receive goal
    - Start planning
    - Route subtasks
    - Verify constraints
    - Execute action
    - Emit events
    - Store results
    - Trigger memory updates

    Dependency graph:
        Application -> Runtime -> Interfaces -> Implementations -> Storage
    """
    container: Container

    def __post_init__(self):
        self._state = RuntimeState()
        self._scheduler = Scheduler(
            event_bus=self.container.event_bus,
            planner=self.container.planner,
            max_workers=self.container.config.get("scheduler.workers", 8),
        )
        self._lifecycle = LifecycleManager(
            event_bus=self.container.event_bus,
            state=self._state,
        )
        self._initialized = False
        logger.info("Runtime created")

    def initialize(self) -> None:
        """Initialize the runtime."""
        if self._initialized:
            return

        logger.info("Initializing Runtime...")
        self._lifecycle.startup()
        self._scheduler.start()
        self._initialized = True
        logger.info("Runtime initialized and ready")

    def execute_goal(self, goal: Goal) -> List[Result]:
        """Execute a goal end-to-end by delegating to the Kernel.

        Flow:
            Goal -> Kernel.submit -> DAG (platform planner/simulator annotate)
            -> providers (platform router/executor run per node)
            -> Verifier (incl. platform constraints) -> Memory -> Results
        """
        if not self._initialized:
            self.initialize()

        logger.info("Executing goal: %s", goal.name)
        self._state.tasks_processed += 1

        response = self.container.kernel.submit(goal.name, project=None)

        results: List[Result] = []
        for node in response.node_results:
            node_result = node.get("result", {})
            verification = node_result.get("verification", {})
            status = "success" if node["status"] == "completed" else ("partial" if node["status"] == "skipped" else "failure")
            result = Result(
                task_id=uuid4(),
                status=status,
                output=node_result.get("response", ""),
                error=node_result.get("error"),
                confidence=verification.get("confidence", 0.0),
            )
            results.append(result)
            self.container.memory.store(result)

        logger.info("Goal execution complete: %d results", len(results))
        return results

    def submit_task(self, task: Task) -> None:
        """Submit a task for async execution."""
        self._scheduler.submit(task)

    def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Shutting down Runtime...")
        self._scheduler.stop()
        self._lifecycle.shutdown()
        self._initialized = False
        logger.info("Runtime shutdown complete")

    @property
    def state(self) -> RuntimeState:
        return self._state

    @property
    def is_initialized(self) -> bool:
        return self._initialized
