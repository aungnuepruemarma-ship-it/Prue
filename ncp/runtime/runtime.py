"""Runtime - Central orchestrator.

Runtime owns every subsystem. Nothing owns Runtime.

Constructor:
    Runtime(planner, router, executor, memory, storage, constraints, simulator, research, events)

No global variables.
"""

from dataclasses import dataclass
from typing import List

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
        """Execute a goal end-to-end.

        Flow:
            Goal -> Planner -> Router -> Constraint Engine -> Simulator
            -> Executor -> Event Bus -> Memory -> Storage
        """
        if not self._initialized:
            self.initialize()

        logger.info("Executing goal: %s", goal.name)
        self._state.tasks_processed += 1

        # 1. Plan
        plan = self.container.planner.plan(goal)
        logger.info("Plan created with %d tasks", len(plan))

        # 2. Execute each task
        results = []
        for task in plan:
            # 3. Route
            capability = self.container.router.route(task)
            logger.debug("Task %s routed to %s", task.name, capability.name)

            # 4. Validate constraints
            if not self.container.constraints.validate(task):
                logger.warning("Task %s failed constraint validation", task.name)
                continue

            # 5. Execute
            result = self.container.executor.execute(task)
            results.append(result)

            # 6. Store in memory
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
