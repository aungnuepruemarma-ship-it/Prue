from __future__ import annotations

from dataclasses import dataclass

from ..utils.metrics import tokenize
from .universe import Universe


@dataclass
class ActivationResult:
    active_entity_ids: list[str]
    scores: dict[str, float]

class ActivationEngine:
    """Scores entities against a goal: token overlap + confidence + recency."""

    def __init__(self, threshold: float = 0.35, recency_window: int = 5):
        self.threshold = threshold
        self.recency_window = recency_window

    def _recent_entity_ids(self, universe: Universe) -> set[str]:
        recent: set[str] = set()
        for event in universe.history[-self.recency_window:]:
            for key in ("id", "source", "target", "result"):
                value = event.get(key)
                if isinstance(value, str):
                    recent.add(value)
        return recent

    def score(self, universe: Universe, goal: str) -> ActivationResult:
        goal_terms = tokenize(goal)
        recent = self._recent_entity_ids(universe)
        scores: dict[str, float] = {}
        active: list[str] = []
        for eid, entity in universe.entities.items():
            tokens = set()
            tokens.add(entity.type.lower())
            tokens.add(entity.name.lower())
            tokens |= {str(k).lower() for k in entity.knowledge.keys()}
            tokens |= {str(v).lower() for v in entity.state.values() if isinstance(v, str)}
            match = len(goal_terms & tokens)
            recency = 0.1 if eid in recent else 0.0
            base = 0.25 * match + 0.2 * entity.confidence + recency
            scores[eid] = min(1.0, base)
            if scores[eid] >= self.threshold:
                active.append(eid)
        if not active and universe.entities:
            active = [max(universe.entities.values(), key=lambda e: e.confidence).id]
            scores[active[0]] = max(scores.get(active[0], 0.0), 0.5)
        active.sort(key=lambda eid: scores[eid], reverse=True)
        return ActivationResult(active_entity_ids=active, scores=scores)
