"""Active session state — what the system is doing right now."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ncp.utils.ids import new_id
from ncp.utils.timeutils import utcnow


@dataclass
class SessionState:
    session_id: str = field(default_factory=lambda: new_id("sess"))
    started_at: str = field(default_factory=lambda: utcnow().isoformat())
    current_execution: str | None = None
    recent_runs: list[str] = field(default_factory=list)
    notes: dict[str, Any] = field(default_factory=dict)

    def record_run(self, run_id: str, keep: int = 50) -> None:
        self.recent_runs.append(run_id)
        del self.recent_runs[:-keep]

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "current_execution": self.current_execution,
            "recent_runs": list(self.recent_runs),
            "notes": dict(self.notes),
        }

    def load_dict(self, data: dict[str, Any]) -> None:
        self.session_id = data.get("session_id", self.session_id)
        self.started_at = data.get("started_at", self.started_at)
        self.current_execution = data.get("current_execution")
        self.recent_runs = list(data.get("recent_runs", []))
        self.notes = dict(data.get("notes", {}))
