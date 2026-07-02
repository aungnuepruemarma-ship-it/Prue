"""Goal lifecycle tracking inside the world state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ncp.utils.ids import new_id
from ncp.utils.timeutils import utcnow


@dataclass
class GoalRecord:
    text: str
    id: str = field(default_factory=lambda: new_id("goal"))
    status: str = "pending"  # pending, active, completed, failed
    project_id: str | None = None
    run_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "text": self.text, "status": self.status,
            "project_id": self.project_id, "run_ids": list(self.run_ids),
            "created_at": self.created_at,
        }


@dataclass
class GoalManager:
    goals: dict[str, GoalRecord] = field(default_factory=dict)

    def add(self, text: str, project_id: str | None = None) -> GoalRecord:
        record = GoalRecord(text=text, project_id=project_id)
        self.goals[record.id] = record
        return record

    def set_status(self, goal_id: str, status: str) -> None:
        self.goals[goal_id].status = status

    def attach_run(self, goal_id: str, run_id: str) -> None:
        self.goals[goal_id].run_ids.append(run_id)

    def by_status(self, status: str) -> list[GoalRecord]:
        return [g for g in self.goals.values() if g.status == status]

    def to_dict(self) -> dict[str, Any]:
        return {gid: g.to_dict() for gid, g in self.goals.items()}

    def load_dict(self, data: dict[str, Any]) -> None:
        self.goals = {gid: GoalRecord(**dict(gdata)) for gid, gdata in data.items()}
