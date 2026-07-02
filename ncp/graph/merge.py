"""Graph merge - Collapse repeated structure into super-nodes."""

from typing import List
from uuid import UUID

from ncp.graph.graph import Graph
from ncp.graph.node import Node
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


def merge_nodes(graph: Graph, node_ids: List[UUID],
                super_node_label: str = "") -> Node:
    """Merge multiple nodes into a super-node.

    Collapses repeated structure into higher-level super-nodes.
    """
    if not node_ids:
        raise ValueError("No nodes to merge")

    nodes = [graph.get_node(nid) for nid in node_ids if nid in graph.nodes]
    if not nodes:
        raise ValueError("No valid nodes found")

    # Create super-node
    label = super_node_label or f"merged_{len(nodes)}_nodes"
    super_node = Node(
        label=label,
        node_type="super_node",
        properties={
            "merged_count": len(nodes),
            "merged_ids": [str(n.id) for n in nodes],
        },
        tags=list(set(tag for n in nodes for tag in n.tags)),
    )

    graph.add_node(super_node)

    # Rewire edges to point to super-node
    for nid in node_ids:
        for edge in graph.get_edges_to(nid):
            edge.target_id = super_node.id
        for edge in graph.get_edges_from(nid):
            edge.source_id = super_node.id

    # Remove old nodes
    for nid in node_ids:
        graph.remove_node(nid)

    logger.info("Merged %d nodes into super-node %s", len(nodes), super_node.id)
    return super_node
