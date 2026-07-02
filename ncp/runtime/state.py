"""Runtime state management."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, Optional


class RuntimeStatus(Enum):
    """Runtime lifecycle states."""
    INITIALIZING = auto()
    CONFIGURING = auto()
    LOADING = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    SHUTTING_DOWN = auto()
    STOPPED = auto()
    ERROR = auto()


@dataclass
class RuntimeState:
    """Immutable snapshot of runtime state."""
    status: RuntimeStatus = RuntimeStatus.INITIALIZING
    start_time: Optional[datetime] = None
    uptime_seconds: float = 0.0
    tasks_processed: int = 0
    tasks_failed: int = 0
    events_published: int = 0
    memory_usage_mb: float = 0.0
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": self.uptime_seconds,
            "tasks_processed": self.tasks_processed,
            "tasks_failed": self.tasks_failed,
            "events_published": self.events_published,
            "memory_usage_mb": self.memory_usage_mb,
        }
