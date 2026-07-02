"""Graph - Base graph structure with node/edge storage and subgraph references."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ncp.graph.edge import Edge
from ncp.graph.node import Node


@dataclass
class Graph:
    """Base graph structure for knowledge representation.

    Supports hierarchical organization with subgraph references.
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    nodes: Dict[UUID, Node] = field(default_factory=dict)
    edges: Dict[UUID, Edge] = field(default_factory=dict)
    adjacency: Dict[UUID, List[UUID]] = field(default_factory=lambda: defaultdict(list))
    parent_id: Optional[UUID] = None
    subgraphs: List[UUID] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        self.edges[edge.id] = edge
        self.adjacency[edge.source_id].append(edge.target_id)
        if edge.bidirectional:
            self.adjacency[edge.target_id].append(edge.source_id)

    def get_node(self, node_id: UUID) -> Optional[Node]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: UUID) -> List[Node]:
        """Get neighboring nodes."""
        neighbor_ids = self.adjacency.get(node_id, [])
        return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]

    def get_edges_from(self, node_id: UUID) -> List[Edge]:
        """Get edges originating from a node."""
        return [e for e in self.edges.values() if e.source_id == node_id]

    def get_edges_to(self, node_id: UUID) -> List[Edge]:
        """Get edges targeting a node."""
        return [e for e in self.edges.values() if e.target_id == node_id]

    def remove_node(self, node_id: UUID) -> None:
        """Remove a node and its edges."""
        if node_id in self.nodes:
            del self.nodes[node_id]
        # Remove associated edges
        edges_to_remove = [
            eid for eid, e in self.edges.items()
            if e.source_id == node_id or e.target_id == node_id
        ]
        for eid in edges_to_remove:
            del self.edges[eid]
        # Update adjacency
        if node_id in self.adjacency:
            del self.adjacency[node_id]
        for adj_list in self.adjacency.values():
            if node_id in adj_list:
                adj_list.remove(node_id)

    def find_path(self, start_id: UUID, end_id: UUID,
                  max_depth: int = 10) -> List[UUID]:
        """Find path between two nodes using BFS."""
        if start_id == end_id:
            return [start_id]

        visited = {start_id}
        queue = [(start_id, [start_id])]

        while queue and len(queue[0][1]) <= max_depth:
            current, path = queue.pop(0)
            for neighbor_id in self.adjacency.get(current, []):
                if neighbor_id == end_id:
                    return path + [neighbor_id]
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return []

    def get_stats(self) -> Dict[str, int]:
        """Get graph statistics."""
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "subgraph_count": len(self.subgraphs),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges.values()],
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "subgraphs": [str(s) for s in self.subgraphs],
        }
