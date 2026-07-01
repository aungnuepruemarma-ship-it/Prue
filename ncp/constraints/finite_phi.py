from __future__ import annotations
from dataclasses import dataclass
from ..core.universe import Universe
from ..core.transformation import TransformationCandidate
from ..utils.config import Config
from .explanation import explain_violations

@dataclass
class ConstraintResult:
    admissible: bool
    violations: list[str]
    explanation: str

class FinitePhiChecker:
    """
    SMT-style finite admissibility gate.
    """
    def __init__(self, config: Config | None = None):
        self.config = config or Config()

    def check(self, universe: Universe, candidate: TransformationCandidate, goal: str = "") -> ConstraintResult:
        violations: list[str] = []
        if len(universe.entities) > self.config.max_entities:
            violations.append("entity_limit_exceeded")
        if len(universe.relations) > self.config.max_relations:
            violations.append("relation_limit_exceeded")
        if not candidate.name:
            violations.append("missing_candidate_name")
        if candidate.task_type not in {"create", "update", "merge", "relate", "research", "plan", "skill", "query"}:
            violations.append(f"unknown_task_type:{candidate.task_type}")
        trial = universe.clone()
        try:
            if candidate.execute is not None:
                trial = candidate.apply(trial)
        except KeyError as e:
            violations.append(f"missing_entity:{e.args[0]}")
        except Exception as e:
            violations.append(f"execution_error:{type(e).__name__}")
        seen = set(trial.entities.keys())
        for rel in trial.relations:
            if rel.source not in seen:
                violations.append(f"dangling_relation_source:{rel.source}")
            if rel.target not in seen:
                violations.append(f"dangling_relation_target:{rel.target}")
        if goal and "forbidden" in goal.lower() and candidate.task_type == "create":
            violations.append("policy_forbids_creation_for_this_goal")
        explanation = explain_violations(violations)
        return ConstraintResult(admissible=(len(violations) == 0), violations=violations, explanation=explanation)
