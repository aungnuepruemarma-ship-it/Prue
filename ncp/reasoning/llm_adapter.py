from __future__ import annotations
from .base import Reasoner
from .rule_based import RuleBasedReasoner
from ..core.universe import Universe
from ..core.transformation import TransformationCandidate

class LLMAdapter(Reasoner):
    def __init__(self, endpoint: str | None = None):
        self.endpoint = endpoint
        self.fallback = RuleBasedReasoner()

    def propose(self, goal: str, universe: Universe, active_entity_ids: list[str]) -> list[TransformationCandidate]:
        return self.fallback.propose(goal, universe, active_entity_ids)
