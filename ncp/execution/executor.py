from __future__ import annotations
from ..core.universe import Universe
from ..core.transformation import TransformationCandidate

class Executor:
    def execute(self, universe: Universe, candidate: TransformationCandidate) -> Universe:
        if candidate.execute is None:
            return universe
        return candidate.apply(universe)
