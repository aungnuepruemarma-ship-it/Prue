"""Objective function for plan scoring."""

from dataclasses import dataclass
from typing import List

from ncp.core.entities import Task


@dataclass
class ObjectiveFunction:
    """Scores candidate plans by cost, confidence, latency, success estimate."""

    cost_weight: float = 0.25
    confidence_weight: float = 0.25
    latency_weight: float = 0.25
    success_weight: float = 0.25

    def score(self, plan: List[Task]) -> float:
        """Score a plan.

        Higher score = better plan.
        """
        if not plan:
            return 0.0

        total_cost = sum(t.estimated_cost for t in plan)
        avg_confidence = sum(getattr(t, "confidence", 0.5) for t in plan) / len(plan)
        total_latency = sum(t.estimated_cost for t in plan) * 100  # proxy
        success_prob = self._estimate_success(plan)

        # Normalize
        cost_score = 1.0 / (1.0 + total_cost)
        latency_score = 1.0 / (1.0 + total_latency)

        score = (
            self.cost_weight * cost_score +
            self.confidence_weight * avg_confidence +
            self.latency_weight * latency_score +
            self.success_weight * success_prob
        )

        return score

    def _estimate_success(self, plan: List[Task]) -> float:
        """Estimate probability of plan success."""
        if not plan:
            return 0.0
        # Simple: assume each step has 90% success rate
        prob = 0.9 ** len(plan)
        return prob

    def compare(self, plan_a: List[Task], plan_b: List[Task]) -> int:
        """Compare two plans. Returns -1 if a < b, 0 if equal, 1 if a > b."""
        score_a = self.score(plan_a)
        score_b = self.score(plan_b)

        if score_a < score_b:
            return -1
        elif score_a > score_b:
            return 1
        return 0
