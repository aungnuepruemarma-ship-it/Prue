from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..compiler.ir import compile_plan
from ..constraints.finite_phi import FinitePhiChecker
from ..curiosity.engine import CuriosityEngine
from ..execution.executor import Executor
from ..memory.graph import MemoryGraph
from ..memory.history import HistoryLog
from ..memory.skills import Skill, SkillExtractor, SkillLibrary
from ..monitoring.diagnostics import Diagnostics
from ..objective.objective import ObjectiveFunction
from ..planning.planner import Planner
from ..research.engine import ResearchEngine
from ..routing.router import CapabilityRouter
from ..storage.json_store import JsonStore
from ..utils.runtime_config import Config
from ..world_model.model import WorldModel
from .activation import ActivationEngine
from .transformations import (
    TransformationCandidate,
    make_add_relation,
    make_create_entity,
    make_sequence,
    make_update_entity,
)
from .universe import Universe


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
        self.world_model = WorldModel()
        self.research = ResearchEngine()
        self._persisted_events = 0

    def propose_candidates(
        self,
        goal: str,
        task_hints: list[str] | None = None,
        reasoner: str | None = None,
    ) -> list[TransformationCandidate]:
        active = self.activation.score(self.universe, goal)
        candidates: list[TransformationCandidate] = []
        seen_names: set[str] = set()
        for hint in task_hints or [None]:
            if reasoner is not None:
                routed = self.router.route_via(reasoner, goal, self.universe, active.active_entity_ids)
            else:
                routed = self.router.route(goal=goal, universe=self.universe, active_entity_ids=active.active_entity_ids, task_hint=hint)
            for candidate in routed:
                if candidate.name not in seen_names:
                    seen_names.add(candidate.name)
                    candidates.append(candidate)
        for candidate in self._skill_candidates(goal, active.active_entity_ids):
            if candidate.name not in seen_names:
                seen_names.add(candidate.name)
                candidates.append(candidate)
        return candidates

    def _skill_candidates(self, goal: str, active_entity_ids: list[str]) -> list[TransformationCandidate]:
        """Turn learned skills whose ops are executable primitives into composite candidates."""
        if not active_entity_ids:
            return []
        target = active_entity_ids[0]
        factories = {
            "create_entity": lambda: make_create_entity("generated_item", "concept", {"source_goal": goal}, {"goal": goal}),
            "update_entity": lambda: make_update_entity(target, {"last_goal": goal}, {"goal": goal}),
            "add_relation": lambda: make_add_relation(target, target, "self_reference"),
            "query_memory": lambda: (lambda u: u),
        }
        out: list[TransformationCandidate] = []
        for skill in self.skills.skills.values():
            if not all(op in factories for op in skill.pattern):
                continue
            steps = [factories[op]() for op in skill.pattern]
            out.append(TransformationCandidate(
                name=f"skill:{skill.name}",
                task_type="skill",
                params={"pattern": list(skill.pattern)},
                cost=0.4 * len(skill.pattern),
                description=f"Replay learned skill {' then '.join(skill.pattern)}",
                execute=make_sequence(steps),
            ))
        return out

    def step(self, goal: str, reasoner: str | None = None) -> RuntimeResult:
        self.diagnostics.increment("steps")
        plan = self.planner.plan(goal, self.universe)
        ir = compile_plan(plan)
        candidates = self.propose_candidates(goal, task_hints=ir.task_hints(), reasoner=reasoner)
        if not candidates:
            return RuntimeResult(status="no_candidates", chosen=None, explanation="No candidates were produced.",
                                 summary={"plan": plan, "ir": ir.to_dict()})
        scored = []
        for candidate in candidates:
            check = self.constraints.check(self.universe, candidate, goal=goal)
            if not check.admissible:
                self.diagnostics.increment("rejected")
                self.history.record({"goal": goal, "candidate": candidate.name, "status": "rejected", "explanation": check.explanation})
                continue
            score = self.objective.score(self.universe, candidate, goal=goal, history=self.history.events)
            scored.append((score, candidate, check.explanation))
        if not scored:
            return RuntimeResult(status="rejected", chosen=None, explanation="All candidates were rejected by Φ.",
                                 summary={"plan": plan, "ir": ir.to_dict()})
        scored.sort(key=lambda x: x[0])
        score, chosen, explanation = scored[0]
        self.executor.execute(self.universe, chosen)
        self.history.record({"goal": goal, "candidate": chosen.name, "status": "accepted", "score": score, "explanation": explanation})
        self.graph.ingest_universe(self.universe)
        self.graph.ingest_history(self.history.events)
        self.skills.update_from_history(self.history.events)
        self.skill_extractor.promote(self.skills, self.history.events)
        self.world_model.observe(self.universe, goal, chosen.name)
        self.research.record_step(goal, chosen.name, explanation)
        suggestion = self.curiosity.suggest_next_goal(self.universe, self.history.events, findings=self.research.findings)
        self.save()
        return RuntimeResult(
            status="accepted",
            chosen={"name": chosen.name, "task_type": chosen.task_type, "params": chosen.params, "score": score},
            explanation=explanation,
            summary={
                "plan": plan,
                "ir": ir.to_dict(),
                "next_goal": suggestion,
                "metrics": self.diagnostics.summary(),
                "history_count": len(self.history.events),
                "entity_count": len(self.universe.entities),
                "relation_count": len(self.universe.relations),
                "world_model": self.world_model.to_dict(),
                "research_findings": len(self.research.findings),
                "skills": sorted(self.skills.skills),
            },
        )

    def learn_skill(self, skill: Skill) -> None:
        self.skills.add_skill(skill)

    def save(self) -> None:
        self.storage.save_universe(self.universe)
        if self._persisted_events == 0:
            self.storage.save_history(self.history.events)
        else:
            self.storage.append_history(self.history.events[self._persisted_events:])
        self._persisted_events = len(self.history.events)
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
