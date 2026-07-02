"""Dependency injection container.

Container creates all subsystems:
    Planner, Router, Executor, Memory, Storage, Research, Simulator
    -> Runtime

Everything created in one place.
"""

from dataclasses import dataclass, field
from typing import Optional

from ncp.events.bus import EventBus
from ncp.interfaces.constraints import ConstraintInterface
from ncp.interfaces.executor import ExecutorInterface
from ncp.interfaces.memory import MemoryInterface
from ncp.interfaces.planner import PlannerInterface
from ncp.interfaces.research import ResearchInterface
from ncp.interfaces.router import RouterInterface
from ncp.interfaces.simulator import SimulatorInterface
from ncp.interfaces.storage import StorageInterface
from ncp.utils.config import Config
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Container:
    """Dependency injection container.

    Builds concrete instances and hands them to Runtime.
    Prevents circular imports by centralizing construction.
    """
    config: Config = field(default_factory=Config)

    # Subsystems (initialized on build)
    kernel: Optional["Kernel"] = field(default=None, repr=False)  # noqa: F821 - imported lazily in build()
    event_bus: Optional[EventBus] = field(default=None, repr=False)
    planner: Optional[PlannerInterface] = field(default=None, repr=False)
    router: Optional[RouterInterface] = field(default=None, repr=False)
    executor: Optional[ExecutorInterface] = field(default=None, repr=False)
    memory: Optional[MemoryInterface] = field(default=None, repr=False)
    storage: Optional[StorageInterface] = field(default=None, repr=False)
    constraints: Optional[ConstraintInterface] = field(default=None, repr=False)
    simulator: Optional[SimulatorInterface] = field(default=None, repr=False)
    research: Optional[ResearchInterface] = field(default=None, repr=False)

    def build(self) -> "Container":
        """Build all subsystems."""
        logger.info("Building container...")

        # 1. Event bus (no dependencies)
        queue_size = self.config.get("events.queue_size", 100000)
        self.event_bus = EventBus(queue_size=queue_size)
        logger.info("EventBus created")

        # 2. Storage (no dependencies on other subsystems)
        from ncp.storage.storage import Storage
        self.storage = Storage(config=self.config)
        logger.info("Storage created")

        # 3. Memory (depends on storage, event bus)
        from ncp.memory.manager import MemoryManager
        self.memory = MemoryManager(
            storage=self.storage,
            event_bus=self.event_bus,
            config=self.config,
        )
        logger.info("MemoryManager created")

        # 4. Router (depends on memory for history)
        from ncp.router.router import Router
        self.router = Router(
            memory=self.memory,
            event_bus=self.event_bus,
            config=self.config,
        )
        logger.info("Router created")

        # 5. Constraints (no subsystem deps)
        from ncp.constraints.solver import ConstraintSolver
        self.constraints = ConstraintSolver(config=self.config)
        logger.info("ConstraintSolver created")

        # 6. Simulator (depends on constraints)
        from ncp.simulator.simulator import Simulator
        self.simulator = Simulator(
            constraints=self.constraints,
            config=self.config,
        )
        logger.info("Simulator created")

        # 7. Executor (depends on router, event bus)
        from ncp.runtime.executor import Executor
        self.executor = Executor(
            router=self.router,
            event_bus=self.event_bus,
            config=self.config,
        )
        logger.info("Executor created")

        # 8. Planner (depends on router, memory, constraints, simulator)
        from ncp.planner.planner import Planner
        self.planner = Planner(
            router=self.router,
            memory=self.memory,
            constraints=self.constraints,
            simulator=self.simulator,
            event_bus=self.event_bus,
            config=self.config,
        )
        logger.info("Planner created")

        # 9. Research (depends on memory, event bus)
        from ncp.research.manager import ResearchManager
        self.research = ResearchManager(
            memory=self.memory,
            event_bus=self.event_bus,
            config=self.config,
        )
        logger.info("ResearchManager created")

        # 10. Kernel (the unified execution engine; shares this container's
        # subsystem instances so its activity is observable on this event
        # bus and memory — Runtime.execute_goal delegates to it)
        from ncp.kernel.kernel import Kernel
        self.kernel = Kernel(
            storage_root=self.config.get("storage.root", "storage"),
            learning_enabled=self.config.get("learning.enabled", True),
            event_bus=self.event_bus,
            memory=self.memory,
            planner=self.planner,
            router=self.router,
            constraints=self.constraints,
            simulator=self.simulator,
            research=self.research,
            executor=self.executor,
        )
        logger.info("Kernel created")

        logger.info("Container build complete")
        return self

    def get_runtime(self) -> "Runtime":  # noqa: F821 - imported lazily to avoid a cycle
        """Create Runtime from built container."""
        from ncp.runtime.runtime import Runtime
        return Runtime(container=self)
