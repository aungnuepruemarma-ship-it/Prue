"""Retrieval engine - Multi-scale search with broad-to-fine refinement.

Blueprint: start broad, then descend into subgraphs for top-down refinement.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from ncp.core.entities import Memory
from ncp.graph.graph import Graph
from ncp.graph.index import GraphIndex
from ncp.memory.ranking import MemoryRanker
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalEngine:
    """Multi-scale retrieval engine.

    Supports broad-to-fine search using graph + index + ranker.
    """
    graph: Optional[Graph] = None
    index: Optional[GraphIndex] = None
    ranker: MemoryRanker = field(default_factory=MemoryRanker)

    def retrieve(self, query: str, top_k: int = 10,
                 memory_type: str = None) -> List[Memory]:
        """Retrieve relevant memories by query.

        Multi-scale: start broad, then refine.
        """
        candidates = []

        # 1. Broad search from graph
        if self.graph:
            # Find nodes matching query
            for node in self.graph.nodes.values():
                if query.lower() in node.label.lower():
                    mem = Memory(
                        content=node.label,
                        memory_type="semantic",
                        confidence=node.confidence,
                    )
                    candidates.append(mem)

        # 2. Index lookup if available
        if self.index and not candidates:
            node_ids = self.index.lookup_by_label(query)
            if node_ids and self.graph:
                for nid in node_ids if isinstance(node_ids, list) else [node_ids]:
                    node = self.graph.get_node(nid)
                    if node:
                        candidates.append(Memory(
                            content=node.label,
                            memory_type="semantic",
                            confidence=node.confidence,
                        ))

        # 3. Rank results
        if candidates:
            ranked = self.ranker.rank(candidates, query, top_k)
            return ranked

        return []

    def retrieve_by_type(self, memory_type: str, top_k: int = 10) -> List[Memory]:
        """Retrieve memories by type."""
        if self.graph and self.index:
            node_ids = self.index.lookup_by_type(memory_type)
            results = []
            for nid in node_ids[:top_k]:
                node = self.graph.get_node(nid)
                if node:
                    results.append(Memory(
                        content=node.label,
                        memory_type=memory_type,
                        confidence=node.confidence,
                    ))
            return results
        return []
