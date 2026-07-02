"""Graph traversal - Coarse-to-fine navigation strategies."""

from collections import deque
from typing import Callable, List, Optional
from uuid import UUID

from ncp.graph.graph import Graph
from ncp.graph.index import GraphIndex
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


class TraversalEngine:
    """Multi-scale graph traversal.

    Supports coarse-to-fine retrieval navigation.
    """

    def __init__(self, graph: Graph, index: Optional[GraphIndex] = None):
        self.graph = graph
        self.index = index

    def bfs(self, start_id: UUID, max_depth: int = 5,
            filter_fn: Optional[Callable] = None) -> List[UUID]:
        """Breadth-first search."""
        visited = {start_id}
        result = [start_id]
        queue = deque([(start_id, 0)])

        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor_id in self.graph.adjacency.get(current, []):
                if neighbor_id not in visited:
                    if filter_fn is None or filter_fn(neighbor_id):
                        visited.add(neighbor_id)
                        result.append(neighbor_id)
                        queue.append((neighbor_id, depth + 1))

        return result

    def dfs(self, start_id: UUID, max_depth: int = 5,
            filter_fn: Optional[Callable] = None) -> List[UUID]:
        """Depth-first search."""
        visited = set()
        result = []

        def _dfs(current: UUID, depth: int):
            if depth > max_depth or current in visited:
                return
            visited.add(current)
            if filter_fn is None or filter_fn(current):
                result.append(current)
            for neighbor_id in self.graph.adjacency.get(current, []):
                _dfs(neighbor_id, depth + 1)

        _dfs(start_id, 0)
        return result

    def find_similar(self, query_embedding: List[float], top_k: int = 10) -> List[UUID]:
        """Find similar nodes using index."""
        if self.index:
            return self.index.search(query_embedding, top_k)
        return []
