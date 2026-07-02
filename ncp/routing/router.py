from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.transformations import TransformationCandidate
from ..core.universe import Universe
from ..reasoning.base import Reasoner
from ..reasoning.llm_adapter import LLMAdapter
from ..reasoning.mythos_adapter import MythosAdapter
from ..reasoning.rule_based import RuleBasedReasoner
from ..utils.metrics import tokenize


@dataclass
class CapabilityCard:
    name: str
    type: str
    strengths: list[str]
    input_types: list[str]
    output_types: list[str]
    cost: str = "medium"
    latency: str = "medium"
    safety: str = "standard"
    metadata: dict[str, Any] = field(default_factory=dict)

class CapabilityRouter:
    """Routes goals to reasoners by consulting the capability registry.

    Each card advertises strength keywords and names its reasoner in
    metadata; routing matches the plan-step task hint (or goal tokens)
    against those strengths instead of hardcoded branches.
    """

    def __init__(self, extra_reasoners: dict[str, Reasoner] | None = None):
        self.reasoners: dict[str, Reasoner] = {
            "rule": RuleBasedReasoner(),
            "llm": LLMAdapter(),
            "mythos": MythosAdapter(),
        }
        if extra_reasoners:
            self.reasoners.update(extra_reasoners)
        self.registry: dict[str, CapabilityCard] = {
            "reasoning": CapabilityCard(
                "rule", "reasoner",
                ["plan", "create", "update", "merge", "relate", "query", "retrieval"],
                ["goal"], ["candidate"], cost="low", latency="low",
                metadata={"reasoner": "rule"},
            ),
            "research": CapabilityCard(
                "llm", "reasoner",
                ["research", "find", "search", "compare", "summarize"],
                ["goal"], ["candidate"], cost="high", latency="high",
                metadata={"reasoner": "llm"},
            ),
            "engineering": CapabilityCard(
                "mythos", "reasoner",
                ["code", "program", "build", "implement", "execute"],
                ["goal"], ["candidate"], cost="high", latency="medium",
                metadata={"reasoner": "mythos"},
            ),
        }
        self.default_card = "reasoning"

    def select_card(self, goal: str, task_hint: str | None = None) -> CapabilityCard:
        terms = {task_hint.lower()} if task_hint else set()
        terms |= tokenize(goal)
        best, best_matches = None, 0
        for card in self.registry.values():
            matches = len(terms & set(card.strengths))
            if matches > best_matches:
                best, best_matches = card, matches
        return best or self.registry[self.default_card]

    def route(
        self,
        goal: str,
        universe: Universe,
        active_entity_ids: list[str],
        task_hint: str | None = None,
    ) -> list[TransformationCandidate]:
        card = self.select_card(goal, task_hint)
        return self.route_via(card.metadata.get("reasoner", "rule"), goal, universe, active_entity_ids)

    def route_via(
        self,
        reasoner_key: str,
        goal: str,
        universe: Universe,
        active_entity_ids: list[str],
    ) -> list[TransformationCandidate]:
        """Route through an explicitly chosen reasoner (kernel provider selection)."""
        reasoner = self.reasoners.get(reasoner_key, self.reasoners["rule"])
        return reasoner.propose(goal, universe, active_entity_ids)
