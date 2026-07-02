"""Fractal graph structure - Self-similar multi-scale graphs.

Based on Laplacian Renormalization Group ideas and scale-invariant graph structure.
"""

from typing import List
from uuid import UUID

from ncp.graph.graph import Graph
from ncp.graph.hierarchy import GraphHierarchy
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


class FractalAnalyzer:
    """Analyzes and validates fractal/self-similar structure in graphs."""

    def __init__(self, hierarchy: GraphHierarchy):
        self.hierarchy = hierarchy

    def compute_fractal_dimension(self, graph: Graph,
                                   box_sizes: List[int] = None) -> float:
        """Estimate fractal dimension using box counting.

        Uses the scaling relation N(r) ~ r^(-df) where N is the number of
        boxes needed to cover the graph and r is the box size.
        """
        import math

        if not graph.nodes:
            return 0.0

        if box_sizes is None:
            n = len(graph.nodes)
            box_sizes = [2, 4, 8, 16, 32, 64]
            box_sizes = [b for b in box_sizes if b <= n]

        counts = []
        for size in box_sizes:
            count = self._box_count(graph, size)
            if count > 0:
                counts.append((math.log(size), math.log(count)))

        if len(counts) < 2:
            return 0.0

        # Linear regression to find slope
        n = len(counts)
        sum_x = sum(x for x, _ in counts)
        sum_y = sum(y for _, y in counts)
        sum_xy = sum(x * y for x, y in counts)
        sum_x2 = sum(x * x for x, _ in counts)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return -slope

    def _box_count(self, graph: Graph, box_size: int) -> int:
        """Count boxes of given size needed to cover graph."""
        import random

        if not graph.nodes:
            return 0

        uncovered = set(graph.nodes.keys())
        count = 0

        while uncovered:
            # Pick random uncovered node as box center
            center = random.choice(list(uncovered))
            # Find all nodes within box_size hops
            in_box = self._nodes_within_distance(graph, center, box_size)
            uncovered -= in_box
            count += 1

        return count

    def _nodes_within_distance(self, graph: Graph, start: UUID,
                                max_distance: int) -> set:
        """Get all nodes within max_distance hops."""
        visited = {start}
        current_level = {start}

        for _ in range(max_distance):
            next_level = set()
            for node in current_level:
                for neighbor in graph.adjacency.get(node, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_level.add(neighbor)
            current_level = next_level
            if not current_level:
                break

        return visited

    def is_self_similar(self, graph: Graph, tolerance: float = 0.1) -> bool:
        """Check if graph exhibits self-similar structure."""
        df = self.compute_fractal_dimension(graph)
        return 1.0 <= df <= 3.0  # Typical range for self-similar graphs

    def get_scale_invariance_score(self, graph: Graph) -> float:
        """Score how scale-invariant the graph structure is."""
        if not graph.nodes or len(graph.nodes) < 10:
            return 0.0

        df = self.compute_fractal_dimension(graph)
        # Ideal fractal dimension for knowledge graphs is around 2
        score = max(0.0, 1.0 - abs(df - 2.0))
        return score
