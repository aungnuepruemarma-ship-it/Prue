from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Entity:
    id: str
    type: str
    name: str
    state: dict[str, Any] = field(default_factory=dict)
    knowledge: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    cost: float = 1.0
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "state": self.state,
            "knowledge": self.knowledge,
            "confidence": self.confidence,
            "cost": self.cost,
            "version": self.version,
            "metadata": self.metadata,
        }
