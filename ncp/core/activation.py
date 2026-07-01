from __future__ import annotations
from dataclasses import dataclass
from .universe import Universe

@dataclass
class ActivationResult:
    active_entity_ids: list[str]
    scores: dict[str, float]

class ActivationEngine:
    def __init__(self, threshold: float = 0.35):
        self.threshold = threshold

    def score(self, universe: Universe, goal: str) -> ActivationResult:
        goal_terms = {t.lower() for t in goal.split() if t.strip()}
        scores: dict[str, float] = {}
        active: list[str] = []
        for eid, entity in universe.entities.items():
            tokens = set()
            tokens.add(entity.type.lower())
            tokens.add(entity.name.lower())
            tokens |= {str(k).lower() for k in entity.knowledge.keys()}
            tokens |= {str(v).lower() for v in entity.state.values() if isinstance(v, str)}
            match = len(goal_terms & tokens)
            base = 0.2 * match + 0.2 * entity.confidence
            scores[eid] = min(1.0, base)
            if scores[eid] >= self.threshold:
                active.append(eid)
        if not active and universe.entities:
            active = [max(universe.entities.values(), key=lambda e: e.confidence).id]
            scores[active[0]] = max(scores.get(active[0], 0.0), 0.5)
        return ActivationResult(active_entity_ids=active, scores=scores)
