"""Delta compression - Store only changes."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from ncp.utils.timeutils import utcnow


@dataclass
class DeltaEntry:
    """A delta entry recording changes."""
    timestamp: datetime = field(default_factory=utcnow)
    path: str = ""
    old_value: Any = None
    new_value: Any = None


class DeltaCompressor:
    """Stores only changes relative to prior state."""

    def __init__(self):
        self.baseline: Dict[str, Any] = {}
        self.deltas: list = []

    def set_baseline(self, data: Dict[str, Any]) -> None:
        """Set baseline state."""
        self.baseline = data.copy()

    def compute_delta(self, new_state: Dict[str, Any]) -> List[DeltaEntry]:
        """Compute delta from baseline to new state."""
        deltas = []
        for key, new_val in new_state.items():
            old_val = self.baseline.get(key)
            if old_val != new_val:
                deltas.append(DeltaEntry(
                    path=key,
                    old_value=old_val,
                    new_value=new_val,
                ))
        return deltas
