from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Graph:
    """Generic directed graph used as the backing store for memory graphs."""

    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[tuple[str, str, str]] = field(default_factory=list)

    def add_node(self, node_id: str, data: dict[str, Any] | None = None) -> None:
        self.nodes[node_id] = data or {}

    def add_edge(self, source: str, target: str, label: str = "") -> None:
        if source not in self.nodes:
            self.add_node(source)
        if target not in self.nodes:
            self.add_node(target)
        self.edges.append((source, target, label))

    def neighbors(self, node_id: str) -> list[str]:
        out = [t for s, t, _ in self.edges if s == node_id]
        out.extend(s for s, t, _ in self.edges if t == node_id)
        return out

    def degree(self, node_id: str) -> int:
        return len(self.neighbors(node_id))

    def clear(self) -> None:
        self.nodes.clear()
        self.edges.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [{"id": nid, "data": data} for nid, data in self.nodes.items()],
            "edges": [{"source": s, "target": t, "label": label} for s, t, label in self.edges],
        }
