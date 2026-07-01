from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class TaskRequest:
    task_id: str
    goal: str
    payload: dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskResponse:
    task_id: str
    status: str
    result: dict[str, Any] = field(default_factory=dict)
    explanation: str = ""
