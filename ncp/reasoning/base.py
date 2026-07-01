from __future__ import annotations
from abc import ABC, abstractmethod
from ..core.universe import Universe
from ..core.transformation import TransformationCandidate

class Reasoner(ABC):
    @abstractmethod
    def propose(self, goal: str, universe: Universe, active_entity_ids: list[str]) -> list[TransformationCandidate]:
        raise NotImplementedError
