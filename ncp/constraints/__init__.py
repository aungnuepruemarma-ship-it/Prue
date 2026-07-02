"""NCP Constraints — the Φ admissibility gate plus the platform solver/DSL."""

from .dsl import ConstraintDSL
from .finite_phi import Constraint, ConstraintResult, FinitePhiChecker
from .policies import ConstraintPolicies
from .solver import ConstraintSolver

__all__ = [
    "FinitePhiChecker",
    "Constraint",
    "ConstraintResult",
    "ConstraintSolver",
    "ConstraintDSL",
    "ConstraintPolicies",
]
