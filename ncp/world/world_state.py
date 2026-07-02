"""World state — NCP remembers projects, goals, and jobs, not chats.

Persistent via the storage manager's ``world_state`` area; absorbs the
reference runtime's world-model facts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ncp.storage.storage_manager import StorageManager
from ncp.utils.timeutils import utcnow
from ncp.world.environment import Environment
from ncp.world.goal_manager import GoalManager
from ncp.world.project_manager import ProjectManager
from ncp.world.session_state import SessionState


@dataclass
class WorldState:
    storage: StorageManager | None = None
    facts: dict[str, str] = field(default_factory=dict)
    jobs: dict[str, dict[str, Any]] = field(default_factory=dict)
    projects: ProjectManager = field(default_factory=ProjectManager)
    goals: GoalManager = field(default_factory=GoalManager)
    session: SessionState = field(default_factory=SessionState)
    environment: Environment = field(default_factory=Environment)

    def update_fact(self, key: str, value: Any) -> None:
        self.facts[key] = str(value)

    def observe_universe(self, universe) -> None:
        self.update_fact("entity_count", len(universe.entities))
        self.update_fact("relation_count", len(universe.relations))
        self.update_fact("universe_version", universe.version)

    def start_job(self, run_id: str, goal: str) -> None:
        self.jobs[run_id] = {"goal": goal, "status": "running", "started_at": utcnow().isoformat()}
        self.session.current_execution = run_id

    def finish_job(self, run_id: str, status: str) -> None:
        if run_id in self.jobs:
            self.jobs[run_id]["status"] = status
            self.jobs[run_id]["finished_at"] = utcnow().isoformat()
        if self.session.current_execution == run_id:
            self.session.current_execution = None

    def running_jobs(self) -> list[str]:
        return [rid for rid, job in self.jobs.items() if job["status"] == "running"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "facts": dict(self.facts),
            "jobs": dict(self.jobs),
            "projects": self.projects.to_dict(),
            "goals": self.goals.to_dict(),
            "session": self.session.to_dict(),
            "environment": self.environment.to_dict(),
        }

    def save(self) -> None:
        if self.storage is not None:
            self.storage.save_document("world_state", "world", self.to_dict())

    def load(self) -> bool:
        if self.storage is None:
            return False
        data = self.storage.load_document("world_state", "world")
        if not data:
            return False
        self.facts = dict(data.get("facts", {}))
        self.jobs = dict(data.get("jobs", {}))
        self.projects.load_dict(data.get("projects", {}))
        self.goals.load_dict(data.get("goals", {}))
        self.session.load_dict(data.get("session", {}))
        return True
