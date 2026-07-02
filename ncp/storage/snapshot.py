"""Snapshot store - Immutable state snapshots."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SnapshotStore:
    """Stores immutable state snapshots for restore/replay."""

    snapshots: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    timestamps: Dict[str, datetime] = field(default_factory=dict)

    def create(self, name: str, data: Dict[str, Any]) -> None:
        """Create snapshot."""
        import copy
        self.snapshots[name] = copy.deepcopy(data)
        self.timestamps[name] = datetime.utcnow()

    def restore(self, name: str) -> Optional[Dict[str, Any]]:
        """Restore snapshot."""
        import copy
        data = self.snapshots.get(name)
        return copy.deepcopy(data) if data else None

    def list_snapshots(self) -> List[str]:
        """List available snapshots."""
        return list(self.snapshots.keys())

    def delete(self, name: str) -> None:
        """Delete snapshot."""
        if name in self.snapshots:
            del self.snapshots[name]
            del self.timestamps[name]
