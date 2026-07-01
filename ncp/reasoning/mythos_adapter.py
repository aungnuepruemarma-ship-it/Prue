from __future__ import annotations

import json
import shutil
import subprocess

from ..core.transformations import TransformationCandidate
from ..core.universe import Universe
from .base import Reasoner
from .llm_adapter import LLMAdapter
from .rule_based import RuleBasedReasoner


class MythosAdapter(Reasoner):
    """Delegates proposing to an external executable, if one is configured.

    The executable receives {"goal", "entities", "active"} as JSON on stdin
    and must print a JSON array of action objects (same schema as
    LLMAdapter). Without an executable, falls back to rule-based reasoning.
    """

    def __init__(self, executable: str | None = None):
        self.executable = executable
        self.fallback = RuleBasedReasoner()
        self._parser = LLMAdapter(adapter=None)

    def available(self) -> bool:
        return bool(self.executable and shutil.which(self.executable))

    def propose(self, goal: str, universe: Universe, active_entity_ids: list[str]) -> list[TransformationCandidate]:
        if not self.available():
            return self.fallback.propose(goal, universe, active_entity_ids)
        try:
            payload = json.dumps({
                "goal": goal,
                "entities": {eid: e.name for eid, e in universe.entities.items()},
                "active": active_entity_ids,
            })
            result = subprocess.run(
                [self.executable], input=payload, capture_output=True,
                text=True, timeout=30, check=True,
            )
            candidates = self._parser._parse_actions(result.stdout, universe)
            return candidates or self.fallback.propose(goal, universe, active_entity_ids)
        except Exception:
            return self.fallback.propose(goal, universe, active_entity_ids)
