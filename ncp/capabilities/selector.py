"""Provider selector — constraint filtering plus a pluggable scoring policy.

The default policy scores by reliability, availability, historical success,
and cost. The learning engine can supply a learned policy that overrides
the default ordering with observed outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ncp.capabilities.registry import ProviderRecord, ProviderRegistry

ScoreFn = Callable[[ProviderRecord, dict[str, Any]], float]


def default_score(record: ProviderRecord, requirements: dict[str, Any]) -> float:
    score = (
        2.0 * record.historical_success
        + record.reliability
        + record.availability
        - 0.5 * record.cost
        - 0.1 * record.latency
    )
    task_type = requirements.get("task_type")
    if task_type and task_type in record.preferred_tasks:
        score += 1.0
    return score


@dataclass
class ProviderSelector:
    registry: ProviderRegistry
    policy: ScoreFn | None = None
    history: list[dict[str, Any]] = field(default_factory=list)

    def select(self, requirements: dict[str, Any]) -> ProviderRecord | None:
        candidates = self.registry.find(
            capability=requirements.get("capability"),
            modality=requirements.get("modality"),
            min_context=requirements.get("min_context", 0),
        )
        if not candidates:
            candidates = self.registry.all()
        if not candidates:
            return None
        score = self.policy or default_score
        best = max(candidates, key=lambda r: score(r, requirements))
        self.history.append({"requirements": requirements, "selected": best.id})
        return best
