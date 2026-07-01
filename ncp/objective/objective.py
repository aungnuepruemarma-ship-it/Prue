from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.transformations import TransformationCandidate
from ..core.universe import Universe
from ..utils.metrics import approximate_cost, candidate_text, normalized_entropy, token_overlap


@dataclass
class ObjectiveFunction:
    """Scores the post-state of a candidate; the runtime minimizes this.

    Structural terms (energy, entropy, cost) penalize growth; relevance and
    novelty reward candidates that match the goal and haven't been tried,
    so the goal's own action isn't structurally penalized into losing.
    """

    energy_weight: float = 1.0
    entropy_weight: float = 1.2
    cost_weight: float = 1.0
    novelty_weight: float = 0.2
    relevance_weight: float = 0.8

    def score(
        self,
        universe: Universe,
        candidate: TransformationCandidate,
        goal: str = "",
        history: list[dict[str, Any]] | None = None,
    ) -> float:
        trial = universe.clone()
        if candidate.execute is not None:
            trial = candidate.apply(trial)
        entity_names = [e.name for e in trial.entities.values()]
        relation_types = [r.relation_type for r in trial.relations]
        ent = normalized_entropy(entity_names + relation_types)
        cost = approximate_cost(len(trial.entities), len(trial.relations), num_active=max(1, len(universe.entities)))
        events = history if history is not None else universe.history
        seen = {e.get("candidate") or e.get("op") for e in events}
        novelty = 0.0 if candidate.name in seen else 1.0
        relevance = token_overlap(goal, candidate_text(candidate)) if goal else 0.0
        return (
            self.energy_weight * (0.05 * len(trial.entities))
            + self.entropy_weight * ent
            + self.cost_weight * cost
            - self.novelty_weight * novelty
            - self.relevance_weight * relevance
        )
