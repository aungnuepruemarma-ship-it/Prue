"""Planner - Converts goals into executable plans.

Main planning orchestrator that creates task graphs.
"""

from dataclasses import dataclass
from typing import List

from ncp.core.entities import Goal, Task
from ncp.events.bus import EventBus
from ncp.events.event import EventType
from ncp.interfaces.constraints import ConstraintInterface
from ncp.interfaces.memory import MemoryInterface
from ncp.interfaces.planner import PlannerInterface
from ncp.interfaces.router import RouterInterface
from ncp.interfaces.simulator import SimulatorInterface
from ncp.planner.decomposition import Decomposer
from ncp.planner.objective import ObjectiveFunction
from ncp.utils.config import Config
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Planner(PlannerInterface):
    """Main planner implementation.

    Converts goals into plans, creates task graphs,
    calls router for each task, attaches constraints.

    Responsibilities:
    - Convert goal into plan
    - Create task graph
    - Call router for each task
    - Attach constraints
    - Return executable plan
    """

    router: RouterInterface
    memory: MemoryInterface
    constraints: ConstraintInterface
    simulator: SimulatorInterface
    event_bus: EventBus
    config: Config

    decomposer: Decomposer = None
    objective: ObjectiveFunction = None

    def __post_init__(self):
        if self.decomposer is None:
            self.decomposer = Decomposer()
        if self.objective is None:
            self.objective = ObjectiveFunction()

    def plan(self, goal: Goal) -> List[Task]:
        """Convert a goal into an executable plan.

        1. Decompose goal into subtasks
        2. Score candidate plans
        3. Select best plan
        4. Validate constraints
        5. Return executable plan
        """
        logger.info("Planning for goal: %s", goal.name)

        self.event_bus.publish(
            type=EventType.PLANNER_STARTED.value,
            payload={"goal": goal.name, "goal_id": str(goal.id)},
        )

        try:
            # 1. Decompose
            tasks = self.decompose(goal)

            # 2. Validate constraints
            valid_tasks = [t for t in tasks if self.validate(t)]

            # 3. Score plan
            score = self.score(valid_tasks)
            logger.debug("Plan score: %.3f (%d tasks)", score, len(valid_tasks))

            # 4. Emit completion event
            self.event_bus.publish(
                type=EventType.PLANNER_FINISHED.value,
                payload={
                    "goal": goal.name,
                    "task_count": len(valid_tasks),
                    "score": score,
                },
            )

            return valid_tasks

        except Exception as e:
            logger.error("Planning failed: %s", e)
            self.event_bus.publish(
                type=EventType.PLANNER_FAILED.value,
                payload={"goal": goal.name, "error": str(e)},
            )
            return []

    def decompose(self, goal: Goal) -> List[Task]:
        """Decompose goal into subtasks."""
        return self.decomposer.decompose(goal)

    def validate(self, plan: List[Task]) -> bool:
        """Validate a plan against constraints."""
        if isinstance(plan, list):
            return all(self.constraints.validate(t) for t in plan)
        return self.constraints.validate(plan)

    def score(self, plan: List[Task]) -> float:
        """Score a plan's quality."""
        return self.objective.score(plan)
