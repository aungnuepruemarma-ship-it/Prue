"""Graph query API."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from ncp.graph.edge import Edge
from ncp.graph.graph import Graph
from ncp.graph.node import Node
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


class QueryEngine:
    """Query API for graph data.

    Retrieves nodes, paths, motifs, and subgraphs.
    """

    def __init__(self, graph: Graph):
        self.graph = graph

    def get_node_by_label(self, label: str) -> Optional[Node]:
        """Find node by label."""
        for node in self.graph.nodes.values():
            if node.label == label:
                return node
        return None

    def get_nodes_by_type(self, node_type: str) -> List[Node]:
        """Get all nodes of a specific type."""
        return [n for n in self.graph.nodes.values() if n.node_type == node_type]

    def get_nodes_by_tag(self, tag: str) -> List[Node]:
        """Get all nodes with a specific tag."""
        return [n for n in self.graph.nodes.values() if tag in n.tags]

    def get_edges_by_type(self, edge_type: str) -> List[Edge]:
        """Get all edges of a specific type."""
        return [e for e in self.graph.edges.values() if e.edge_type == edge_type]

    def find_motif(self, pattern: Dict[str, Any]) -> List[List[UUID]]:
        """Find graph motifs matching a pattern."""
        # Simplified implementation - finds triangles
        results = []
        for node_id in self.graph.nodes:
            neighbors = self.graph.adjacency.get(node_id, [])
            for i, n1 in enumerate(neighbors):
                for n2 in neighbors[i+1:]:
                    if n2 in self.graph.adjacency.get(n1, []):
                        results.append([node_id, n1, n2])
        return results

    def get_subgraph(self, node_ids: List[UUID]) -> Graph:
        """Extract a subgraph containing specified nodes."""
        subgraph = Graph(name="subgraph")
        for nid in node_ids:
            if nid in self.graph.nodes:
                subgraph.add_node(self.graph.nodes[nid])
        for edge in self.graph.edges.values():
            if edge.source_id in node_ids and edge.target_id in node_ids:
                subgraph.add_edge(edge)
        return subgraph
