"""Hypothesis model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID, uuid4


@dataclass
class Hypothesis:
    """A proposed new idea, algorithm, or workflow."""

    id: UUID = field(default_factory=uuid4)
    statement: str = ""
    confidence: float = 0.5
    evidence: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, testing, verified, rejected
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
