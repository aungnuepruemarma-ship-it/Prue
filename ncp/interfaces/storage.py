"""Storage Interface - Persistence layer."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional


class StorageInterface(ABC):
    """Abstract interface for storage subsystem.

    Unified persistence API for entities, graphs, embeddings, objects.
    """

    @abstractmethod
    def save(self, key: str, data: Any) -> None:
        """Save data.

        Args:
            key: Storage key
            data: Data to save
        """
        ...

    @abstractmethod
    def load(self, key: str) -> Optional[Any]:
        """Load data.

        Args:
            key: Storage key

        Returns:
            Loaded data or None
        """
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete data.

        Args:
            key: Storage key
        """
        ...

    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """List storage keys.

        Args:
            prefix: Key prefix filter

        Returns:
            List of keys
        """
        ...

    @abstractmethod
    def snapshot(self, name: str) -> None:
        """Create a snapshot.

        Args:
            name: Snapshot name
        """
        ...
