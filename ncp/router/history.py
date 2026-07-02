"""Routing history - Past routing decisions and outcomes."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID


@dataclass
class RoutingDecision:
    """A single routing decision record."""
    task_id: UUID = None
    capability_name: str = ""
    success: bool = True
    latency_ms: float = 0.0
    cost: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingHistory:
    """Stores past routing choices with success/failure history."""

    decisions: List[RoutingDecision] = field(default_factory=list)
    max_history: int = 10000

    def record(self, decision: RoutingDecision) -> None:
        """Record a routing decision."""
        self.decisions.append(decision)
        if len(self.decisions) > self.max_history:
            self.decisions = self.decisions[-self.max_history:]

    def get_success_rate(self, capability_name: str) -> float:
        """Get success rate for a capability."""
        relevant = [d for d in self.decisions
                    if d.capability_name == capability_name]
        if not relevant:
            return 0.5  # Unknown: neutral
        successes = sum(1 for d in relevant if d.success)
        return successes / len(relevant)

    def get_average_latency(self, capability_name: str) -> float:
        """Get average latency for a capability."""
        relevant = [d for d in self.decisions
                    if d.capability_name == capability_name]
        if not relevant:
            return 0.0
        return sum(d.latency_ms for d in relevant) / len(relevant)

    def get_recent(self, n: int = 10) -> List[RoutingDecision]:
        """Get recent decisions."""
        return self.decisions[-n:]
