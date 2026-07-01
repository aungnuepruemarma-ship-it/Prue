from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class WorldModel:
    facts: dict[str, str] = field(default_factory=dict)
    goals: list[str] = field(default_factory=list)

    def update_fact(self, key: str, value: str) -> None:
        self.facts[key] = value
