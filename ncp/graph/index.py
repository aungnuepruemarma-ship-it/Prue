"""Hierarchical graph index for multi-scale retrieval."""

from typing import Dict, List, Optional
from uuid import UUID

from ncp.graph.graph import Graph
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


class GraphIndex:
    """Hierarchical index for fast node/subgraph lookup.

    Supports multi-scale retrieval through vector search.
    """

    def __init__(self):
        self._embeddings: Dict[UUID, List[float]] = {}
        self._label_index: Dict[str, UUID] = {}
        self._type_index: Dict[str, List[UUID]] = {}
        self._tag_index: Dict[str, List[UUID]] = {}

    def add_node(self, node) -> None:
        """Index a single node (incremental build)."""
        self._label_index[node.label] = node.id
        if node.node_type not in self._type_index:
            self._type_index[node.node_type] = []
        if node.id not in self._type_index[node.node_type]:
            self._type_index[node.node_type].append(node.id)
        if node.embedding:
            self._embeddings[node.id] = node.embedding
        for tag in node.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            if node.id not in self._tag_index[tag]:
                self._tag_index[tag].append(node.id)

    def build(self, graph: Graph) -> None:
        """Build index from graph."""
        for node in graph.nodes.values():
            self.add_node(node)
        logger.info("Index built: %d nodes, %d embeddings",
                     len(self._label_index), len(self._embeddings))

    def search(self, query_embedding: List[float], top_k: int = 10) -> List[UUID]:
        """Search for similar nodes by embedding."""
        import math

        def cosine_similarity(a: List[float], b: List[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)

        scored = [
            (node_id, cosine_similarity(query_embedding, emb))
            for node_id, emb in self._embeddings.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [nid for nid, _ in scored[:top_k]]

    def lookup_by_label(self, label: str) -> Optional[UUID]:
        """Lookup node by label."""
        return self._label_index.get(label)

    def lookup_by_type(self, node_type: str) -> List[UUID]:
        """Lookup nodes by type."""
        return self._type_index.get(node_type, [])

    def lookup_by_tag(self, tag: str) -> List[UUID]:
        """Lookup nodes by tag."""
        return self._tag_index.get(tag, [])
