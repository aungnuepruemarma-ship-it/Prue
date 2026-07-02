"""Executor Interface - Executes actions."""

from abc import ABC, abstractmethod

from ncp.core.entities import Result, Task


class ExecutorInterface(ABC):
    """Abstract interface for execution subsystem.

    Executes routed actions and returns results.
    """

    @abstractmethod
    def execute(self, task: Task) -> Result:
        """Execute a task.

        Args:
            task: The task to execute

        Returns:
            Execution result
        """
        ...

    @abstractmethod
    def can_execute(self, task: Task) -> bool:
        """Check if this executor can handle a task.

        Args:
            task: The task to check

        Returns:
            True if can execute
        """
        ...
