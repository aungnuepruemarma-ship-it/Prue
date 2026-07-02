"""Routing policy - Select best candidate capability."""

from dataclasses import dataclass
from typing import Any, Dict, List

from ncp.core.entities import Task
from ncp.interfaces.capability import CapabilityCard
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RoutingPolicy:
    """Selects best candidate for a task.

    Supports rule-based selection.
    Later can be RL-based.
    """

    latency_weight: float = 0.3
    cost_weight: float = 0.3
    quality_weight: float = 0.4

    def select(self, task: Task, candidates: List[CapabilityCard],
               history: Dict[str, Any] = None) -> CapabilityCard:
        """Select best capability for a task."""
        if not candidates:
            raise ValueError("No candidates available")

        if len(candidates) == 1:
            return candidates[0]

        scored = []
        for cap in candidates:
            score = self._score_capability(cap, task, history or {})
            scored.append((cap, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        best = scored[0][0]

        logger.debug("Selected %s (score=%.3f)", best.name, scored[0][1])
        return best

    def _score_capability(self, cap: CapabilityCard, task: Task,
                          history: Dict[str, Any]) -> float:
        """Score a capability for a task."""
        # Latency score (lower is better)
        latency_score = 1.0 / (1.0 + cap.latency_ms / 1000.0)

        # Cost score (lower is better)
        cost_score = 1.0 / (1.0 + cap.cost_per_call)

        # Quality score (reliability)
        quality_score = cap.reliability

        # History bonus
        history_bonus = history.get(cap.name, {}).get("success_rate", 0.5)

        score = (
            self.latency_weight * latency_score +
            self.cost_weight * cost_score +
            self.quality_weight * quality_score
        ) * (0.8 + 0.2 * history_bonus)

        return score
