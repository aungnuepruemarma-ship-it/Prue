"""Constraint Interface - Validation engine."""

from abc import ABC, abstractmethod
from typing import Any

from ncp.core.entities import Task


class ConstraintInterface(ABC):
    """Abstract interface for constraint validation.

    Validates tasks against defined constraints using SMT/symbolic solving.
    """

    @abstractmethod
    def validate(self, task: Task) -> bool:
        """Validate a task against constraints.

        Args:
            task: Task to validate

        Returns:
            True if valid
        """
        ...

    @abstractmethod
    def explain(self, task: Task) -> str:
        """Explain why a task fails validation.

        Args:
            task: Task to explain

        Returns:
            Explanation string
        """
        ...

    @abstractmethod
    def add_constraint(self, constraint: Any) -> None:
        """Add a new constraint.

        Args:
            constraint: Constraint definition
        """
        ...
