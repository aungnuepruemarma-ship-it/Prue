from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .universe import Universe
from .activation import ActivationEngine
from .transformation import TransformationCandidate
from .transformations import make_create_entity, make_update_entity, make_add_relation, make_merge_entities
from ..constraints.finite_phi import FinitePhiChecker
from ..objective.objective import ObjectiveFunction
from ..memory.history import HistoryLog
from ..memory.graph import MemoryGraph
from ..memory.skills import SkillLibrary, SkillExtractor
from ..routing.router import CapabilityRouter
from ..planning.planner import Planner
from ..execution.executor import Executor
from ..storage.json_store import JsonStore
from ..monitoring.diagnostics import Diagnostics
from ..curiosity.engine import CuriosityEngine
from ..utils.config import Config

@dataclass
class RuntimeResult:
    status: str
    chosen: dict[str, Any] | None
    explanation: str
    summary: dict[str, Any] = field(default_factory=dict)

class Runtime:
    def __init__(self, universe: Universe, config: Config | None = None):
        self.universe = universe
        self.config = config or Config()
        self.activation = ActivationEngine(self.config.active_threshold)
        self.constraints = FinitePhiChecker(config=self.config)
        self.objective = ObjectiveFunction()
        self.history = HistoryLog()
        self.graph = MemoryGraph()
        self.skills = SkillLibrary()
        self.skill_extractor = SkillExtractor(threshold=self.config.skill_threshold)
        self.router = CapabilityRouter()
        self.planner = Planner()
        self.executor = Executor()
        self.storage = JsonStore(self.config.output_dir)
        self.diagnostics = Diagnostics()
        self.curiosity = CuriosityEngine()

    def propose_candidates(self, goal: str) -> list[TransformationCandidate]:
        active = self.activation.score(self.universe, goal)
        return self.router.route(goal=goal, universe=self.universe, active_entity_ids=active.active_entity_ids)

    def step(self, goal: str) -> RuntimeResult:
        self.diagnostics.increment("steps")
        plan = self.planner.plan(goal, self.universe)
        candidates = self.propose_candidates(goal)
        if not candidates:
            return RuntimeResult(status="no_candidates", chosen=None, explanation="No candidates were produced.", summary={"plan": plan})
        scored = []
        for candidate in candidates:
            check = self.constraints.check(self.universe, candidate, goal=goal)
            if not check.admissible:
                self.diagnostics.increment("rejected")
                self.history.record({"goal": goal, "candidate": candidate.name, "status": "rejected", "explanation": check.explanation})
                continue
            score = self.objective.score(self.universe, candidate, goal=goal)
            scored.append((score, candidate, check.explanation))
        if not scored:
            return RuntimeResult(status="rejected", chosen=None, explanation="All candidates were rejected by Φ.", summary={"plan": plan})
        scored.sort(key=lambda x: x[0])
        score, chosen, explanation = scored[0]
        committed = self.executor.execute(self.universe, chosen)
        self.history.record({"goal": goal, "candidate": chosen.name, "status": "accepted", "score": score, "explanation": explanation})
        self.graph.ingest_universe(self.universe)
        self.graph.ingest_history(self.history.events)
        self.skills.update_from_history(self.history.events)
        self.skill_extractor.promote(self.skills, self.history.events)
        suggestion = self.curiosity.suggest_next_goal(self.universe, self.history.events)
        self.save()
        return RuntimeResult(
            status="accepted",
            chosen={"name": chosen.name, "task_type": chosen.task_type, "params": chosen.params, "score": score},
            explanation=explanation,
            summary={
                "plan": plan,
                "next_goal": suggestion,
                "metrics": self.diagnostics.summary(),
                "history_count": len(self.history.events),
                "entity_count": len(self.universe.entities),
                "relation_count": len(self.universe.relations),
            },
        )

    def save(self) -> None:
        self.storage.save_universe(self.universe)
        self.storage.save_history(self.history.events)
        self.storage.save_graph(self.graph)
        self.storage.save_skills(self.skills)

def build_default_universe() -> Universe:
    from .entity import Entity
    from .universe import Relation
    u = Universe()
    u.add_entity(Entity(id="e_root", type="goal", name="root", state={"status": "seed"}, knowledge={"seed": True}, confidence=0.9))
    u.add_entity(Entity(id="e_mem", type="memory", name="short_term", state={"tier": "working"}, knowledge={"entries": 1}, confidence=0.7))
    u.add_relation(Relation(source="e_root", target="e_mem", relation_type="activates"))
    return u
