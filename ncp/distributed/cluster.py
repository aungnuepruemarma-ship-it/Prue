from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Node:
    node_id: str
    status: str = "online"

@dataclass
class Cluster:
    nodes: list[Node] = field(default_factory=list)

    def add_node(self, node_id: str) -> None:
        self.nodes.append(Node(node_id=node_id))
