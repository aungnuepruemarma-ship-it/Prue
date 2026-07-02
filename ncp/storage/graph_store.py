"""Graph store - Persists graphs and subgraphs."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ncp.graph.graph import Graph


@dataclass
class GraphStore:
    """Stores graphs with hierarchy awareness."""

    graphs: Dict[str, Graph] = field(default_factory=dict)

    def save_graph(self, name: str, graph: Graph) -> None:
        self.graphs[name] = graph

    def load_graph(self, name: str) -> Optional[Graph]:
        return self.graphs.get(name)

    def list_graphs(self) -> List[str]:
        return list(self.graphs.keys())
