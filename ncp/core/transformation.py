from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from .universe import Universe

@dataclass
class TransformationCandidate:
    name: str
    task_type: str
    params: dict[str, Any] = field(default_factory=dict)
    cost: float = 1.0
    description: str = ""
    execute: Callable[[Universe], Universe] | None = None

    def apply(self, universe: Universe) -> Universe:
        if self.execute is None:
            return universe
        return self.execute(universe)
