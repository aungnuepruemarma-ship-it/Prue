"""Dependency tracking between facts, skills, and results."""

from dataclasses import dataclass, field
from typing import Dict, Set
from uuid import UUID


@dataclass
class DependencyTracker:
    """Tracks dependencies among facts, skills, and results."""

    dependencies: Dict[UUID, Set[UUID]] = field(default_factory=dict)

    def add_dependency(self, item_id: UUID, depends_on: UUID) -> None:
        """Record that item_id depends on depends_on."""
        if item_id not in self.dependencies:
            self.dependencies[item_id] = set()
        self.dependencies[item_id].add(depends_on)

    def get_dependencies(self, item_id: UUID) -> Set[UUID]:
        """Get all dependencies of an item."""
        return self.dependencies.get(item_id, set())

    def get_dependents(self, item_id: UUID) -> Set[UUID]:
        """Get all items that depend on this item."""
        dependents = set()
        for other_id, deps in self.dependencies.items():
            if item_id in deps:
                dependents.add(other_id)
        return dependents
