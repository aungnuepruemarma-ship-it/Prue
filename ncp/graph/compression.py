"""Graph-specific compression hooks."""

from typing import Dict, List

from ncp.graph.graph import Graph
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


class GraphCompressor:
    """Compresses graph structure by removing redundancy.

    Connects graph structure to compression policy.
    """

    def __init__(self):
        self._compression_log: List[Dict] = []

    def compress(self, graph: Graph, target_ratio: float = 0.5) -> Graph:
        """Compress graph to target ratio.

        Uses node merging and edge pruning.
        """
        original_nodes = len(graph.nodes)

        # 1. Remove low-confidence nodes
        nodes_to_remove = [
            nid for nid, n in graph.nodes.items()
            if n.confidence < 0.3
        ]
        for nid in nodes_to_remove:
            graph.remove_node(nid)

        # 2. Remove low-weight edges
        edges_to_remove = [
            eid for eid, e in graph.edges.items()
            if e.weight < 0.2
        ]
        for eid in edges_to_remove:
            if eid in graph.edges:
                del graph.edges[eid]

        # Rebuild adjacency
        graph.adjacency.clear()
        for edge in graph.edges.values():
            graph.adjacency[edge.source_id].append(edge.target_id)

        new_nodes = len(graph.nodes)
        ratio = new_nodes / original_nodes if original_nodes > 0 else 1.0

        self._compression_log.append({
            "original_nodes": original_nodes,
            "new_nodes": new_nodes,
            "ratio": ratio,
        })

        logger.info("Compressed graph: %d -> %d nodes (ratio=%.2f)",
                     original_nodes, new_nodes, ratio)

        return graph

    def get_stats(self) -> List[Dict]:
        """Get compression history."""
        return self._compression_log
