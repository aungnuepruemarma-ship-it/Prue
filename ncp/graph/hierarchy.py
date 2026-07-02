"""Graph hierarchy - Organizes graphs into levels with parent/child relations."""

from typing import Dict, List, Optional
from uuid import UUID

from ncp.graph.graph import Graph
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


class GraphHierarchy:
    """Organizes graphs into hierarchical levels.

    Supports scale-aware traversal on pooled/coarsened graphs.
    Blueprint: coarse-to-fine search with semantic hierarchy trees.
    """

    def __init__(self):
        self._levels: Dict[int, List[Graph]] = {}
        self._graph_levels: Dict[UUID, int] = {}
        self._parents: Dict[UUID, UUID] = {}
        self._children: Dict[UUID, List[UUID]] = {}

    def add_graph(self, graph: Graph, level: int = 0,
                  parent_id: Optional[UUID] = None) -> None:
        """Add a graph at a hierarchy level."""
        if level not in self._levels:
            self._levels[level] = []
        self._levels[level].append(graph)
        self._graph_levels[graph.id] = level

        if parent_id:
            self._parents[graph.id] = parent_id
            if parent_id not in self._children:
                self._children[parent_id] = []
            self._children[parent_id].append(graph.id)

    def get_level(self, level: int) -> List[Graph]:
        """Get all graphs at a hierarchy level."""
        return self._levels.get(level, [])

    def get_parent(self, graph_id: UUID) -> Optional[UUID]:
        """Get parent graph ID."""
        return self._parents.get(graph_id)

    def get_children(self, graph_id: UUID) -> List[UUID]:
        """Get child graph IDs."""
        return self._children.get(graph_id, [])

    def get_ancestors(self, graph_id: UUID) -> List[UUID]:
        """Get all ancestor graph IDs."""
        ancestors = []
        current = self._parents.get(graph_id)
        while current:
            ancestors.append(current)
            current = self._parents.get(current)
        return ancestors

    def num_levels(self) -> int:
        """Get number of hierarchy levels."""
        return len(self._levels)

    def get_stats(self) -> Dict[str, int]:
        """Get hierarchy statistics."""
        return {
            "num_levels": self.num_levels(),
            "total_graphs": len(self._graph_levels),
        }
