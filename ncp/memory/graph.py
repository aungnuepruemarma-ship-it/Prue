from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
from ..core.universe import Universe

@dataclass
class GraphNode:
    id: str
    label: str
    data: dict[str, Any] = field(default_factory=dict)

@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    data: dict[str, Any] = field(default_factory=dict)

@dataclass
class MemoryGraph:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    def ingest_universe(self, universe: Universe) -> None:
        self.nodes.clear()
        self.edges.clear()
        for eid, entity in universe.entities.items():
            self.nodes[eid] = GraphNode(id=eid, label=entity.name, data=entity.to_dict())
        for rel in universe.relations:
            self.edges.append(GraphEdge(source=rel.source, target=rel.target, relation=rel.relation_type, data=rel.to_dict()))

    def ingest_history(self, events: list[dict[str, Any]]) -> None:
        for idx, event in enumerate(events):
            nid = f"event_{idx}"
            self.nodes[nid] = GraphNode(id=nid, label=event.get("candidate", event.get("op", "event")), data=event)
