"""Audit trail - Trace changes over time."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AuditEntry:
    """A single audit log entry."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    action: str = ""
    actor: str = ""
    target: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    result: str = ""


@dataclass
class AuditTrail:
    """Audit trail for tracking all system changes.

    Supports replay and review.
    """

    entries: List[AuditEntry] = field(default_factory=list)
    max_entries: int = 100000

    def log(self, action: str, actor: str = "", target: str = "",
            details: Dict[str, Any] = None, result: str = "") -> None:
        """Log an audit entry."""
        entry = AuditEntry(
            action=action,
            actor=actor,
            target=target,
            details=details or {},
            result=result,
        )
        self.entries.append(entry)

        # Enforce limit
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

    def get_entries(self, action: str = None, actor: str = None,
                    limit: int = 100) -> List[AuditEntry]:
        """Get filtered audit entries."""
        results = self.entries
        if action:
            results = [e for e in results if e.action == action]
        if actor:
            results = [e for e in results if e.actor == actor]
        return results[-limit:]

    def get_recent(self, n: int = 50) -> List[AuditEntry]:
        """Get recent entries."""
        return self.entries[-n:]

    @property
    def entry_count(self) -> int:
        return len(self.entries)
