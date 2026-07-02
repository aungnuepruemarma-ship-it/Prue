"""Constraint solver - Decide SAT/UNSAT with explanations.

Later can connect to Z3 or another SMT backend.
"""

from dataclasses import dataclass, field
from typing import Any, List

from ncp.constraints.dsl import ConstraintDSL
from ncp.constraints.policies import ConstraintPolicies
from ncp.core.entities import Task
from ncp.interfaces.constraints import ConstraintInterface
from ncp.utils.config import Config
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConstraintSolver(ConstraintInterface):
    """Validates tasks against constraints."""

    config: Config = None
    policies: ConstraintPolicies = field(default_factory=ConstraintPolicies)
    constraints: List[ConstraintDSL] = field(default_factory=list)

    def __post_init__(self):
        if self.config:
            self.policies.max_execution_time_ms = self.config.get(
                "constraints.max_execution_time_ms", 300000
            )
            self.policies.max_cost_per_task = self.config.get(
                "constraints.max_cost_per_task", 1.0
            )

    def validate(self, task: Task) -> bool:
        """Validate a task against all constraints."""
        # Check execution time
        if task.estimated_cost > self.policies.max_cost_per_task:
            logger.warning("Task %s exceeds cost limit: %.2f > %.2f",
                          task.name, task.estimated_cost,
                          self.policies.max_cost_per_task)
            return False

        # Check capability
        if task.capability_required:
            if not self.policies.is_capability_allowed(task.capability_required):
                logger.warning("Capability %s not allowed",
                             task.capability_required)
                return False

        # Check retries
        if task.retry_count > self.policies.max_retries:
            logger.warning("Task %s exceeded max retries", task.name)
            return False

        # Check custom constraints
        for constraint in self.constraints:
            if not self._check_constraint(task, constraint):
                return False

        return True

    def explain(self, task: Task) -> str:
        """Explain why a task fails validation."""
        if task.estimated_cost > self.policies.max_cost_per_task:
            return f"Cost {task.estimated_cost} exceeds limit {self.policies.max_cost_per_task}"
        if task.retry_count > self.policies.max_retries:
            return f"Retries {task.retry_count} exceed limit {self.policies.max_retries}"
        return "Task is valid"

    def add_constraint(self, constraint: Any) -> None:
        """Add a new constraint."""
        if isinstance(constraint, ConstraintDSL):
            self.constraints.append(constraint)
        else:
            self.constraints.append(ConstraintDSL(
                name="custom",
                expression=str(constraint),
            ))

    def _check_constraint(self, task: Task, constraint: ConstraintDSL) -> bool:
        """Check a single constraint."""
        # Simplified: always pass for now
        return True
