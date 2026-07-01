from __future__ import annotations

from ..core.transformations import TransformationCandidate
from ..core.universe import Universe


class Executor:
    def execute(self, universe: Universe, candidate: TransformationCandidate) -> Universe:
        if candidate.execute is None:
            return universe
        return candidate.apply(universe)
