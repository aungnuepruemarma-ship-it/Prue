from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Callable

from ..utils.ids import new_id
from .entity import Entity
from .universe import Relation, Universe


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

def make_create_entity(name: str, type_: str, state: dict[str, Any] | None = None, knowledge: dict[str, Any] | None = None):
    def _exec(universe: Universe) -> Universe:
        uid = new_id("e")
        universe.add_entity(Entity(
            id=uid,
            type=type_,
            name=name,
            state=copy.deepcopy(state) if state else {},
            knowledge=copy.deepcopy(knowledge) if knowledge else {},
            confidence=0.5,
            cost=1.0,
        ))
        universe.version += 1
        universe.record_history({"op": "create_entity", "id": uid, "name": name, "type": type_})
        return universe
    return _exec

def make_update_entity(entity_id: str, state_patch: dict[str, Any] | None = None, knowledge_patch: dict[str, Any] | None = None):
    def _exec(universe: Universe) -> Universe:
        entity = universe.entities[entity_id]
        entity.state.update(state_patch or {})
        entity.knowledge.update(knowledge_patch or {})
        entity.version += 1
        universe.version += 1
        universe.record_history({"op": "update_entity", "id": entity_id,
                                 "state_patch": state_patch or {}, "knowledge_patch": knowledge_patch or {}})
        return universe
    return _exec

def make_merge_entities(source_id: str, target_id: str, merged_name: str):
    def _exec(universe: Universe) -> Universe:
        s = universe.entities[source_id]
        t = universe.entities[target_id]
        uid = new_id("m")
        merged_state = copy.deepcopy({**s.state, **t.state})
        merged_knowledge = copy.deepcopy({**s.knowledge, **t.knowledge})
        universe.add_entity(Entity(
            id=uid,
            type=f"merged:{s.type}+{t.type}",
            name=merged_name,
            state=merged_state,
            knowledge=merged_knowledge,
            confidence=max(s.confidence, t.confidence),
            cost=s.cost + t.cost,
        ))
        universe.add_relation(Relation(source=source_id, target=uid, relation_type="merged_into"))
        universe.add_relation(Relation(source=target_id, target=uid, relation_type="merged_into"))
        universe.version += 1
        universe.record_history({"op": "merge_entities", "sources": [source_id, target_id], "result": uid})
        return universe
    return _exec

def make_add_relation(source_id: str, target_id: str, relation_type: str):
    def _exec(universe: Universe) -> Universe:
        universe.add_relation(Relation(source=source_id, target=target_id, relation_type=relation_type))
        universe.version += 1
        universe.record_history({"op": "add_relation", "source": source_id, "target": target_id, "relation_type": relation_type})
        return universe
    return _exec

def make_sequence(steps: list[Callable[[Universe], Universe]]):
    def _exec(universe: Universe) -> Universe:
        for step in steps:
            universe = step(universe)
        return universe
    return _exec
