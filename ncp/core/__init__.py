"""NCP Core — operational universe types plus the platform entity hierarchy.

``Entity``/``Universe`` here are the *operational* types the reference
runtime mutates. The platform's entity hierarchy (Goal -> Task -> Memory ->
Skill -> Tool -> Result) lives in :mod:`ncp.core.entities`.
"""

from .entities import (
    Goal,
    Metadata,
    Objective,
    Result,
    Task,
    Tool,
    Version,
)
from .entity import Entity
from .runtime import Runtime, build_default_universe
from .transformations import TransformationCandidate
from .universe import Relation, Universe

__all__ = [
    "Entity",
    "Universe",
    "Relation",
    "TransformationCandidate",
    "Runtime",
    "build_default_universe",
    "Goal",
    "Task",
    "Tool",
    "Result",
    "Metadata",
    "Objective",
    "Version",
]
