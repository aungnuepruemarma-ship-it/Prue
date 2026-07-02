"""Lineage tracking - Parent/child provenance chains."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class LineageEntry:
    """A single entry in a lineage chain."""
    id: UUID = field(default_factory=uuid4)
    parent_id: Optional[UUID] = None
    child_ids: List[UUID] = field(default_factory=list)
    operation: str = ""  # "created", "modified", "derived", "merged"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    description: str = ""


@dataclass
class LineageTracker:
    """Tracks parent/child provenance chains."""

    entries: Dict[UUID, LineageEntry] = field(default_factory=dict)

    def record(self, item_id: UUID, parent_id: UUID = None,
               operation: str = "created", description: str = "") -> LineageEntry:
        """Record a lineage entry."""
        entry = LineageEntry(
            parent_id=parent_id,
            operation=operation,
            description=description,
        )
        self.entries[item_id] = entry
        return entry

    def get_lineage(self, item_id: UUID) -> List[UUID]:
        """Get ancestor chain for an item."""
        chain = []
        current = item_id
        while current in self.entries:
            entry = self.entries[current]
            chain.append(current)
            current = entry.parent_id
            if current is None:
                break
        return list(reversed(chain))
