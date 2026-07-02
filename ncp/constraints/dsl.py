"""Constraint DSL - Human-readable constraint language."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ConstraintDSL:
    """Human-readable constraint definitions."""
    name: str = ""
    constraint_type: str = ""  # "resource", "logic", "policy", "causality"
    expression: str = ""  # Human-readable expression
    parameters: Dict[str, Any] = field(default_factory=dict)
    severity: str = "error"  # "error", "warning", "info"
