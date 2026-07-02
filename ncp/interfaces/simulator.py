"""Simulator Interface - Outcome prediction."""

from abc import ABC, abstractmethod

from ncp.core.entities import Result, Task


class SimulatorInterface(ABC):
    """Abstract interface for simulation subsystem.

    Simulates candidate actions and estimates side effects.
    """

    @abstractmethod
    def simulate(self, task: Task) -> Result:
        """Simulate a task execution.

        Args:
            task: Task to simulate

        Returns:
            Predicted result
        """
        ...

    @abstractmethod
    def estimate_cost(self, task: Task) -> float:
        """Estimate execution cost.

        Args:
            task: Task to estimate

        Returns:
            Estimated cost
        """
        ...
