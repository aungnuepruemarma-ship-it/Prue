"""Graph expansion - Expand abstract nodes into detailed subgraphs."""

from uuid import UUID

from ncp.graph.graph import Graph
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


def expand_node(graph: Graph, node_id: UUID,
                expansion: Graph) -> None:
    """Expand an abstract node into a detailed subgraph.

    Reverse of compression/merge operation.
    """
    node = graph.get_node(node_id)
    if not node:
        logger.warning("Node %s not found for expansion", node_id)
        return

    # Add expansion nodes
    for exp_node in expansion.nodes.values():
        graph.add_node(exp_node)

    # Add expansion edges
    for exp_edge in expansion.edges.values():
        graph.add_edge(exp_edge)

    # Rewire: connect expansion boundary nodes to original neighbors
    for edge in graph.get_edges_to(node_id):
        # Find closest match in expansion
        if expansion.nodes:
            first_exp = list(expansion.nodes.values())[0]
            edge.target_id = first_exp.id

    # Remove abstract node
    graph.remove_node(node_id)

    logger.info("Expanded node %s into %d nodes", node_id, len(expansion.nodes))
