from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from .entity import Entity


@dataclass
class Relation:
    source: str
    target: str
    relation_type: str
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type,
            "weight": self.weight,
            "metadata": self.metadata,
        }

@dataclass
class Universe:
    entities: dict[str, Entity] = field(default_factory=dict)
    relations: list[Relation] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    version: int = 1

    def clone(self) -> "Universe":
        # Must be a deep copy: constraint checking and objective scoring
        # trial-apply candidates on clones, and any shared nested dict would
        # let validation mutate live state.
        return copy.deepcopy(self)

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def add_relation(self, relation: Relation) -> None:
        self.relations.append(relation)

    def remove_entity(self, entity_id: str) -> None:
        self.entities.pop(entity_id, None)
        self.relations = [r for r in self.relations if r.source != entity_id and r.target != entity_id]

    def snapshot(self, note: str = "") -> dict[str, Any]:
        return {
            "version": self.version,
            "note": note,
            "entities": [e.to_dict() for e in self.entities.values()],
            "relations": [r.to_dict() for r in self.relations],
            "history": copy.deepcopy(self.history),
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "Universe":
        data = copy.deepcopy(data)
        u = cls(version=data.get("version", 1))
        for e in data.get("entities", []):
            u.add_entity(Entity(**e))
        for r in data.get("relations", []):
            u.add_relation(Relation(**r))
        u.history = data.get("history", [])
        return u

    def record_history(self, event: dict[str, Any]) -> None:
        self.history.append(event)
