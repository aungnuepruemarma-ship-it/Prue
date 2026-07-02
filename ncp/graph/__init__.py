"""NCP Graph — UUID-keyed knowledge graph plus the string-keyed simple graph.

Includes the previously-unexported analysis modules (fractal, merge, split,
expansion, compression) so no graph capability is an orphan.
"""

from .compression import GraphCompressor
from .edge import Edge, EdgeType
from .expansion import expand_node
from .fractal import FractalAnalyzer
from .graph import Graph
from .hierarchy import GraphHierarchy
from .index import GraphIndex
from .merge import merge_nodes
from .metrics import GraphMetrics
from .node import Node
from .query import QueryEngine
from .simple import SimpleGraph
from .split import split_by_clustering
from .traversal import TraversalEngine

__all__ = [
    "Graph",
    "SimpleGraph",
    "Node",
    "Edge",
    "EdgeType",
    "GraphHierarchy",
    "TraversalEngine",
    "QueryEngine",
    "GraphIndex",
    "GraphMetrics",
    "FractalAnalyzer",
    "GraphCompressor",
    "merge_nodes",
    "split_by_clustering",
    "expand_node",
]
