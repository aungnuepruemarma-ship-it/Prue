from __future__ import annotations

from abc import ABC, abstractmethod

from ..core.transformations import TransformationCandidate
from ..core.universe import Universe


class Reasoner(ABC):
    @abstractmethod
    def propose(self, goal: str, universe: Universe, active_entity_ids: list[str]) -> list[TransformationCandidate]:
        raise NotImplementedError
