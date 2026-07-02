"""Graph split - Partition a graph into subgraphs."""

from typing import List

from ncp.graph.graph import Graph
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


def split_by_clustering(graph: Graph, num_partitions: int = 2) -> List[Graph]:
    """Partition graph into subgraphs using simple spectral-like approach.

    Uses a greedy balanced partition algorithm.
    """
    if not graph.nodes:
        return []

    node_list = list(graph.nodes.keys())

    if num_partitions > len(node_list):
        num_partitions = len(node_list)

    # Simple round-robin partitioning
    partitions = [[] for _ in range(num_partitions)]
    for i, node_id in enumerate(node_list):
        partitions[i % num_partitions].append(node_id)

    subgraphs = []
    for i, partition_nodes in enumerate(partitions):
        if partition_nodes:
            subgraph = graph.get_subgraph(partition_nodes)
            subgraph.name = f"partition_{i}"
            subgraphs.append(subgraph)

    logger.info("Split graph into %d partitions", len(subgraphs))
    return subgraphs
