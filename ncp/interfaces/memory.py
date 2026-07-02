"""Memory Interface - Hierarchical memory management."""

from abc import ABC, abstractmethod
from typing import List, Union

from ncp.core.entities import Entity, Memory, Result, Task


class MemoryInterface(ABC):
    """Abstract interface for memory subsystem.

    Manages hierarchical memory tiers and retrieval.
    """

    @abstractmethod
    def store(self, item: Union[Entity, Task, Result, Memory]) -> None:
        """Store an item in memory.

        Args:
            item: Item to store
        """
        ...

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 10) -> List[Memory]:
        """Retrieve relevant memories.

        Args:
            query: Search query
            top_k: Maximum results

        Returns:
            List of relevant memories
        """
        ...

    @abstractmethod
    def update(self, item: Memory) -> None:
        """Update an existing memory.

        Args:
            item: Memory to update
        """
        ...

    @abstractmethod
    def consolidate(self) -> None:
        """Trigger memory consolidation."""
        ...

    @abstractmethod
    def working_memory(self) -> List[Entity]:
        """Get current working memory contents.

        Returns:
            Working memory items
        """
        ...
