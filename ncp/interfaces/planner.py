"""Planner Interface - Converts goals into executable plans."""

from abc import ABC, abstractmethod
from typing import List

from ncp.core.entities import Goal, Task


class PlannerInterface(ABC):
    """Abstract interface for planning subsystem.

    Converts goals into executable plans through decomposition and search.
    Nothing in the repository depends directly on implementations.
    """

    @abstractmethod
    def plan(self, goal: Goal) -> List[Task]:
        """Convert a goal into an executable plan.

        Args:
            goal: The goal to plan for

        Returns:
            Ordered list of tasks forming the plan
        """
        ...

    @abstractmethod
    def decompose(self, goal: Goal) -> List[Goal]:
        """Decompose a goal into sub-goals.

        Args:
            goal: The goal to decompose

        Returns:
            List of sub-goals
        """
        ...

    @abstractmethod
    def validate(self, plan: List[Task]) -> bool:
        """Validate a plan against constraints.

        Args:
            plan: The plan to validate

        Returns:
            True if plan is valid
        """
        ...

    @abstractmethod
    def score(self, plan: List[Task]) -> float:
        """Score a plan's quality.

        Args:
            plan: The plan to score

        Returns:
            Quality score (higher is better)
        """
        ...
