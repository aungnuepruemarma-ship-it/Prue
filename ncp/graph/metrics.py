"""Graph metrics for quality and performance analysis."""

from dataclasses import dataclass
from typing import Any, Dict

from ncp.graph.graph import Graph


@dataclass
class GraphMetrics:
    """Metrics for graph quality analysis."""

    # Basic stats
    node_count: int = 0
    edge_count: int = 0

    # Connectivity
    avg_degree: float = 0.0
    max_degree: int = 0
    density: float = 0.0

    # Structure
    clustering_coefficient: float = 0.0
    diameter_estimate: int = 0
    connected_components: int = 0

    # Scale metrics
    compression_ratio: float = 1.0

    # Traversal
    avg_shortest_path: float = 0.0

    @classmethod
    def compute(cls, graph: Graph) -> "GraphMetrics":
        """Compute all metrics for a graph."""
        m = cls()
        m.node_count = len(graph.nodes)
        m.edge_count = len(graph.edges)

        if m.node_count == 0:
            return m

        # Degree stats
        degrees = [len(graph.adjacency.get(nid, [])) for nid in graph.nodes]
        m.avg_degree = sum(degrees) / len(degrees) if degrees else 0
        m.max_degree = max(degrees) if degrees else 0

        # Density
        max_edges = m.node_count * (m.node_count - 1)
        m.density = m.edge_count / max_edges if max_edges > 0 else 0

        # Simple clustering estimate
        triangles = 0
        triplets = 0
        for nid in graph.nodes:
            neighbors = graph.adjacency.get(nid, [])
            k = len(neighbors)
            if k >= 2:
                triplets += k * (k - 1) // 2
                for i in range(k):
                    for j in range(i + 1, k):
                        if neighbors[j] in graph.adjacency.get(neighbors[i], []):
                            triangles += 1
        m.clustering_coefficient = triangles / triplets if triplets > 0 else 0

        return m

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "avg_degree": round(self.avg_degree, 2),
            "max_degree": self.max_degree,
            "density": round(self.density, 4),
            "clustering_coefficient": round(self.clustering_coefficient, 4),
            "diameter_estimate": self.diameter_estimate,
            "connected_components": self.connected_components,
            "compression_ratio": round(self.compression_ratio, 4),
        }
