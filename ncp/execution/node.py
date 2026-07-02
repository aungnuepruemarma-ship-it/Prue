"""Execution DAG node."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ncp.utils.ids import new_id


@dataclass
class DAGNode:
    name: str
    goal: str
    task_type: str = "plan"
    id: str = field(default_factory=lambda: new_id("node"))
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed, skipped
    result: dict[str, Any] = field(default_factory=dict)
    provider_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "goal": self.goal,
            "task_type": self.task_type,
            "depends_on": list(self.depends_on),
            "status": self.status,
            "result": self.result,
            "provider_id": self.provider_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DAGNode":
        return cls(
            name=data["name"],
            goal=data["goal"],
            task_type=data.get("task_type", "plan"),
            id=data["id"],
            depends_on=list(data.get("depends_on", [])),
            status=data.get("status", "pending"),
            result=dict(data.get("result", {})),
            provider_id=data.get("provider_id", ""),
            metadata=dict(data.get("metadata", {})),
        )
