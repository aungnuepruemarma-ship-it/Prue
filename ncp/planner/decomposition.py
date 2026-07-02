"""Goal decomposition - Split goals into subtasks."""

from dataclasses import dataclass
from typing import List

from ncp.core.entities import Goal, Task
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Decomposer:
    """Splits goals into subtasks preserving dependencies.

    Creates task tree or DAG from goal.
    """

    def decompose(self, goal: Goal, depth: int = 0,
                  max_depth: int = 5) -> List[Task]:
        """Decompose a goal into subtasks.

        Returns ordered list of tasks forming the plan.
        """
        if depth >= max_depth:
            # Base case: goal becomes a single task
            return [Task(
                name=goal.name,
                description=goal.description,
                priority=goal.priority,
                inputs={"goal": goal.name},
            )]

        tasks = []

        # Analyze goal and create subtasks
        subgoals = self._identify_subgoals(goal)

        if not subgoals:
            # Atomic goal
            tasks.append(Task(
                name=goal.name,
                description=goal.description,
                priority=goal.priority,
                inputs={"goal": goal.name},
            ))
        else:
            # Decompose each subgoal
            for i, subgoal in enumerate(subgoals):
                subtasks = self.decompose(subgoal, depth + 1, max_depth)
                # Add dependencies between subgoals
                if i > 0 and subtasks:
                    for st in subtasks:
                        st.dependencies.append(subgoals[i-1].id)
                tasks.extend(subtasks)

        logger.debug("Decomposed goal '%s' into %d tasks", goal.name, len(tasks))
        return tasks

    def _identify_subgoals(self, goal: Goal) -> List[Goal]:
        """Identify subgoals from a goal."""
        # Simple heuristic: split by keywords
        subgoals = []

        # Check for explicit subgoals
        if goal.sub_goals:
            return []  # Already has subgoals

        # Simple decomposition heuristics
        name_lower = goal.name.lower()

        if " and " in name_lower:
            parts = goal.name.split(" and ")
            for part in parts:
                subgoals.append(Goal(name=part.strip(), parent_id=goal.id))
        elif ", then " in name_lower:
            parts = goal.name.split(", then ")
            for part in parts:
                subgoals.append(Goal(name=part.strip(), parent_id=goal.id))

        return subgoals
