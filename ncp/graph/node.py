"""Graph node - Base element of the knowledge graph."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class Node:
    """Graph node with metadata, provenance, confidence, and version.

    Each node represents a concept, fact, skill, or memory item.
    """
    id: UUID = field(default_factory=uuid4)
    label: str = ""
    node_type: str = "concept"  # concept, fact, skill, memory, task, goal
    metadata: Dict[str, Any] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    provenance_id: Optional[UUID] = None
    confidence: float = 1.0
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "label": self.label,
            "node_type": self.node_type,
            "metadata": self.metadata,
            "properties": self.properties,
            "provenance_id": str(self.provenance_id) if self.provenance_id else None,
            "confidence": self.confidence,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
        }

    def update_confidence(self, new_confidence: float) -> None:
        """Update node confidence."""
        self.confidence = max(0.0, min(1.0, new_confidence))
        self.updated_at = datetime.utcnow()
