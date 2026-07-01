from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Graph:
    nodes: dict[str, dict] = field(default_factory=dict)
    edges: list[tuple[str, str, str]] = field(default_factory=list)

    def add_node(self, node_id: str, data: dict) -> None:
        self.nodes[node_id] = data
