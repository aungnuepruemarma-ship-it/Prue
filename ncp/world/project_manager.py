"""Projects — the durable unit of work the world state tracks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ncp.utils.ids import new_id
from ncp.utils.timeutils import utcnow


@dataclass
class Project:
    name: str
    id: str = field(default_factory=lambda: new_id("proj"))
    description: str = ""
    status: str = "active"  # active, paused, completed, archived
    goal_ids: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    repositories: list[str] = field(default_factory=list)
    deadline: str | None = None
    budget: float | None = None
    created_at: str = field(default_factory=lambda: utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "status": self.status, "goal_ids": list(self.goal_ids),
            "files": list(self.files), "repositories": list(self.repositories),
            "deadline": self.deadline, "budget": self.budget, "created_at": self.created_at,
        }


@dataclass
class ProjectManager:
    projects: dict[str, Project] = field(default_factory=dict)

    def create(self, name: str, **kwargs: Any) -> Project:
        project = Project(name=name, **kwargs)
        self.projects[project.id] = project
        return project

    def get(self, project_id: str) -> Project | None:
        return self.projects.get(project_id)

    def find_by_name(self, name: str) -> Project | None:
        return next((p for p in self.projects.values() if p.name == name), None)

    def attach_goal(self, project_id: str, goal_id: str) -> None:
        project = self.projects[project_id]
        if goal_id not in project.goal_ids:
            project.goal_ids.append(goal_id)

    def active(self) -> list[Project]:
        return [p for p in self.projects.values() if p.status == "active"]

    def to_dict(self) -> dict[str, Any]:
        return {pid: p.to_dict() for pid, p in self.projects.items()}

    def load_dict(self, data: dict[str, Any]) -> None:
        self.projects = {}
        for pid, pdata in data.items():
            pdata = dict(pdata)
            self.projects[pid] = Project(**pdata)
