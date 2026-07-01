from __future__ import annotations
from .base import Reasoner
from .rule_based import RuleBasedReasoner
from ..core.universe import Universe
from ..core.transformation import TransformationCandidate

class MythosAdapter(Reasoner):
    def __init__(self, executable: str | None = None):
        self.executable = executable
        self.fallback = RuleBasedReasoner()

    def propose(self, goal: str, universe: Universe, active_entity_ids: list[str]) -> list[TransformationCandidate]:
        return self.fallback.propose(goal, universe, active_entity_ids)
