from __future__ import annotations
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
        return Universe(
            entities={k: Entity(**v.to_dict()) for k, v in self.entities.items()},
            relations=[Relation(**r.to_dict()) for r in self.relations],
            history=[dict(item) for item in self.history],
            version=self.version,
        )

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
        }

    def record_history(self, event: dict[str, Any]) -> None:
        self.history.append(event)
