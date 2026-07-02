"""Provenance record - Aggregates all provenance information."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ncp.provenance.confidence import ConfidenceModel
from ncp.provenance.evidence import Evidence
from ncp.provenance.lineage import LineageEntry
from ncp.provenance.source import Source


@dataclass
class ProvenanceRecord:
    """Aggregates source, evidence, confidence, lineage, version."""

    id: UUID = field(default_factory=uuid4)
    source: Optional[Source] = None
    evidence: List[Evidence] = field(default_factory=list)
    confidence: ConfidenceModel = field(default_factory=ConfidenceModel)
    lineage: Optional[LineageEntry] = None
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_evidence(self, evidence: Evidence) -> None:
        """Add evidence to the record."""
        self.evidence.append(evidence)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "source_type": self.source.type if self.source else None,
            "evidence_count": len(self.evidence),
            "confidence": self.confidence.compute(),
            "version": self.version,
            "created_at": self.created_at.isoformat(),
        }
