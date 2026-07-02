from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.universe import Universe
from ..graph.simple import SimpleGraph as Graph


@dataclass
class MemoryGraph:
    """Semantic view of the universe plus episodic events, backed by Graph."""

    graph: Graph = field(default_factory=Graph)

    @property
    def nodes(self) -> dict[str, dict[str, Any]]:
        return self.graph.nodes

    @property
    def edges(self) -> list[tuple[str, str, str]]:
        return self.graph.edges

    def ingest_universe(self, universe: Universe) -> None:
        events = [(nid, data) for nid, data in self.graph.nodes.items() if nid.startswith("event_")]
        self.graph.clear()
        for eid, entity in universe.entities.items():
            self.graph.add_node(eid, {"label": entity.name, "entity": entity.to_dict()})
        for rel in universe.relations:
            self.graph.add_edge(rel.source, rel.target, rel.relation_type)
        for nid, data in events:
            self.graph.add_node(nid, data)

    def ingest_history(self, events: list[dict[str, Any]]) -> None:
        for idx, event in enumerate(events):
            nid = f"event_{idx}"
            label = event.get("candidate", event.get("op", "event"))
            self.graph.add_node(nid, {"label": label, "event": event})

    def related_entities(self, entity_id: str) -> list[str]:
        return [n for n in self.graph.neighbors(entity_id) if not n.startswith("event_")]

    def to_dict(self) -> dict[str, Any]:
        return self.graph.to_dict()
