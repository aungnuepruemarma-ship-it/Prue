from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..core.transformations import TransformationCandidate
from ..core.universe import Universe
from ..utils.runtime_config import Config
from .explanation import explain_violations

KNOWN_TASK_TYPES = {"create", "update", "merge", "relate", "research", "plan", "skill", "query"}

@dataclass
class ConstraintResult:
    admissible: bool
    violations: list[str]
    explanation: str

@dataclass
class ConstraintContext:
    universe: Universe
    candidate: TransformationCandidate
    goal: str
    trial: Universe | None = None

# A constraint is a named predicate over the check context that returns
# violation strings. Pre-constraints see trial=None; post-constraints run
# after the candidate has been applied to a trial clone.
@dataclass
class Constraint:
    name: str
    check: Callable[[ConstraintContext], list[str]]
    phase: str = "pre"  # "pre" or "post"

def _size_limits(config: Config) -> Constraint:
    def check(ctx: ConstraintContext) -> list[str]:
        violations = []
        if len(ctx.universe.entities) > config.max_entities:
            violations.append("entity_limit_exceeded")
        if len(ctx.universe.relations) > config.max_relations:
            violations.append("relation_limit_exceeded")
        return violations
    return Constraint("size_limits", check)

def _well_formed() -> Constraint:
    def check(ctx: ConstraintContext) -> list[str]:
        violations = []
        if not ctx.candidate.name:
            violations.append("missing_candidate_name")
        if ctx.candidate.task_type not in KNOWN_TASK_TYPES:
            violations.append(f"unknown_task_type:{ctx.candidate.task_type}")
        return violations
    return Constraint("well_formed", check)

def _no_dangling_relations() -> Constraint:
    def check(ctx: ConstraintContext) -> list[str]:
        violations = []
        trial = ctx.trial if ctx.trial is not None else ctx.universe
        seen = set(trial.entities.keys())
        for rel in trial.relations:
            if rel.source not in seen:
                violations.append(f"dangling_relation_source:{rel.source}")
            if rel.target not in seen:
                violations.append(f"dangling_relation_target:{rel.target}")
        return violations
    return Constraint("no_dangling_relations", check, phase="post")

def _forbidden_creation_policy() -> Constraint:
    def check(ctx: ConstraintContext) -> list[str]:
        if ctx.goal and "forbidden" in ctx.goal.lower() and ctx.candidate.task_type == "create":
            return ["policy_forbids_creation_for_this_goal"]
        return []
    return Constraint("policy_forbidden_creation", check)

def default_constraints(config: Config) -> list[Constraint]:
    return [
        _size_limits(config),
        _well_formed(),
        _forbidden_creation_policy(),
        _no_dangling_relations(),
    ]

class FinitePhiChecker:
    """Finite admissibility gate Phi.

    Constraints are data: a list of named predicates evaluated before and
    after trial-applying the candidate to a deep clone of the universe, so
    checking never mutates live state.
    """

    def __init__(self, config: Config | None = None, constraints: list[Constraint] | None = None):
        self.config = config or Config()
        self.constraints = constraints if constraints is not None else default_constraints(self.config)

    def add_constraint(self, constraint: Constraint) -> None:
        self.constraints.append(constraint)

    def check(self, universe: Universe, candidate: TransformationCandidate, goal: str = "") -> ConstraintResult:
        ctx = ConstraintContext(universe=universe, candidate=candidate, goal=goal)
        violations: list[str] = []
        for constraint in self.constraints:
            if constraint.phase == "pre":
                violations.extend(constraint.check(ctx))
        trial = universe.clone()
        try:
            if candidate.execute is not None:
                trial = candidate.apply(trial)
        except KeyError as e:
            violations.append(f"missing_entity:{e.args[0]}")
        except Exception as e:
            violations.append(f"execution_error:{type(e).__name__}")
        ctx.trial = trial
        for constraint in self.constraints:
            if constraint.phase == "post":
                violations.extend(constraint.check(ctx))
        explanation = explain_violations(violations)
        return ConstraintResult(admissible=(len(violations) == 0), violations=violations, explanation=explanation)
