"""Router Interface - Selects best capability for each task."""

from abc import ABC, abstractmethod
from typing import List

from ncp.core.entities import Task
from ncp.interfaces.capability import CapabilityCard


class RouterInterface(ABC):
    """Abstract interface for routing subsystem.

    Chooses model/tool/solver for each task based on capability cards.
    """

    @abstractmethod
    def route(self, task: Task) -> CapabilityCard:
        """Select best capability for a task.

        Args:
            task: The task to route

        Returns:
            Selected capability card
        """
        ...

    @abstractmethod
    def register(self, capability: CapabilityCard) -> None:
        """Register a new capability.

        Args:
            capability: Capability to register
        """
        ...

    @abstractmethod
    def list_capabilities(self) -> List[CapabilityCard]:
        """List all available capabilities.

        Returns:
            List of capability cards
        """
        ...
