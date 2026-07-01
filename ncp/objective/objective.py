from __future__ import annotations
from dataclasses import dataclass
from ..core.universe import Universe
from ..core.transformation import TransformationCandidate
from ..utils.metrics import approximate_cost, normalized_entropy

@dataclass
class ObjectiveFunction:
    energy_weight: float = 1.0
    entropy_weight: float = 1.2
    cost_weight: float = 1.0
    novelty_weight: float = 0.2

    def score(self, universe: Universe, candidate: TransformationCandidate, goal: str = "") -> float:
        trial = universe.clone()
        if candidate.execute is not None:
            trial = candidate.apply(trial)
        entity_names = [e.name for e in trial.entities.values()]
        relation_types = [r.relation_type for r in trial.relations]
        ent = normalized_entropy(entity_names + relation_types)
        cost = approximate_cost(len(trial.entities), len(trial.relations), num_active=max(1, len(universe.entities)))
        novelty = 1.0 if candidate.name not in [h.get("candidate") for h in universe.history if "candidate" in h] else 0.0
        return self.energy_weight * (0.05 * len(trial.entities)) + self.entropy_weight * ent + self.cost_weight * cost - self.novelty_weight * novelty
