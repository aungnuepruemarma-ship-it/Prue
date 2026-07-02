"""Simulator - Predicts outcomes of actions.

Estimates side effects and returns predicted state.
"""

from dataclasses import dataclass

from ncp.core.entities import Result, Task
from ncp.interfaces.constraints import ConstraintInterface
from ncp.interfaces.simulator import SimulatorInterface
from ncp.utils.config import Config
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Simulator(SimulatorInterface):
    """Simulates candidate actions and estimates side effects."""

    constraints: ConstraintInterface
    config: Config = None

    def simulate(self, task: Task) -> Result:
        """Simulate a task execution.

        Returns predicted result with estimated confidence.
        """
        logger.debug("Simulating task: %s", task.name)

        # Validate constraints
        is_valid = self.constraints.validate(task)

        if not is_valid:
            return Result(
                task_id=task.id,
                status="predicted_failure",
                confidence=0.1,
                output="Constraint validation failed",
            )

        # Estimate success probability based on task properties
        success_prob = self._estimate_success(task)

        # Predict execution time
        predicted_time = self.estimate_cost(task)

        status = "predicted_success" if success_prob > 0.5 else "predicted_failure"

        return Result(
            task_id=task.id,
            status=status,
            confidence=success_prob,
            execution_time_ms=predicted_time,
            output=f"Simulation: {status} (confidence={success_prob:.2f})",
        )

    def estimate_cost(self, task: Task) -> float:
        """Estimate execution cost in milliseconds."""
        base_time = 100.0  # Base 100ms

        # Scale by task complexity (estimated from inputs)
        complexity = len(str(task.inputs))
        scaled = base_time * (1 + complexity / 1000)

        return scaled

    def _estimate_success(self, task: Task) -> float:
        """Estimate probability of success."""
        # Base probability
        prob = 0.8

        # Adjust by retry count
        prob *= (0.9 ** task.retry_count)

        # Adjust by estimated cost
        if task.estimated_cost > 0.5:
            prob *= 0.9

        return max(0.0, min(1.0, prob))
