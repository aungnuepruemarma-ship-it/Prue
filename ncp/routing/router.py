from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from ..core.universe import Universe
from ..core.transformation import TransformationCandidate
from ..reasoning.rule_based import RuleBasedReasoner
from ..reasoning.llm_adapter import LLMAdapter
from ..reasoning.mythos_adapter import MythosAdapter

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
    def __init__(self):
        self.reasoners = {
            "rule": RuleBasedReasoner(),
            "llm": LLMAdapter(),
            "mythos": MythosAdapter(),
        }
        self.registry = {
            "reasoning": CapabilityCard("rule", "reasoner", ["planning", "updates", "retrieval"], ["goal"], ["candidate"]),
            "formal": CapabilityCard("smt", "solver", ["validity", "admissibility"], ["constraints"], ["sat_model"]),
            "memory": CapabilityCard("memory_graph", "store", ["retrieval", "compression"], ["entities"], ["context"]),
        }

    def route(self, goal: str, universe: Universe, active_entity_ids: list[str]) -> list[TransformationCandidate]:
        goal_l = goal.lower()
        if any(k in goal_l for k in ["verify", "valid", "constraint", "proof"]):
            reasoner = self.reasoners["rule"]
        elif any(k in goal_l for k in ["code", "program", "build"]):
            reasoner = self.reasoners["mythos"]
        elif any(k in goal_l for k in ["research", "find", "search"]):
            reasoner = self.reasoners["llm"]
        else:
            reasoner = self.reasoners["rule"]
        return reasoner.propose(goal, universe, active_entity_ids)
