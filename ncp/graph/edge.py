"""Graph edge - Relations between nodes."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict
from uuid import UUID, uuid4

from ncp.utils.timeutils import utcnow


class EdgeType(Enum):
    """Types of relationships between nodes."""
    CAUSAL = "causal"           # A causes B
    TEMPORAL = "temporal"       # A before B
    ABSTRACTION = "abstraction" # A abstracts B
    DEPENDENCY = "dependency"   # A depends on B
    SIMILARITY = "similarity"   # A similar to B
    PARENT = "parent"           # A is parent of B
    COMPOSITION = "composition" # A composed of B
    REFERENCE = "reference"     # A references B


@dataclass
class Edge:
    """Edge between two graph nodes.

    Types: causal, temporal, abstraction, dependency, similarity, parent, composition, reference
    """
    id: UUID = field(default_factory=uuid4)
    source_id: UUID = field(default_factory=uuid4)
    target_id: UUID = field(default_factory=uuid4)
    edge_type: str = EdgeType.SIMILARITY.value
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    bidirectional: bool = False
    created_at: datetime = field(default_factory=utcnow)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "source_id": str(self.source_id),
            "target_id": str(self.target_id),
            "edge_type": self.edge_type,
            "weight": self.weight,
            "metadata": self.metadata,
            "bidirectional": self.bidirectional,
            "created_at": self.created_at.isoformat(),
            "confidence": self.confidence,
        }
