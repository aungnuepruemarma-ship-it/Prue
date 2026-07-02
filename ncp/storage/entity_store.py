"""Entity store - Stores entities with versioning."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class EntityStore:
    """Stores entities with version tracking."""

    entities: Dict[str, Any] = field(default_factory=dict)
    versions: Dict[str, int] = field(default_factory=dict)

    def store(self, key: str, entity: Any) -> None:
        """Store an entity."""
        self.entities[key] = entity
        self.versions[key] = self.versions.get(key, 0) + 1

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve an entity."""
        return self.entities.get(key)

    def get_version(self, key: str) -> int:
        """Get entity version."""
        return self.versions.get(key, 0)
