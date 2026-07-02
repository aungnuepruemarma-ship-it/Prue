"""Experiment model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4


@dataclass
class Experiment:
    """Structured experiment with inputs, outputs, metrics."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed
    started_at: datetime = None
    completed_at: datetime = None
    hypothesis_id: UUID = None
