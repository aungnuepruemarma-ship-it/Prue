"""NCP — Nexus Computing Platform.

A unified AI orchestration system merging two lineages:

- the reference runtime (goal -> activation -> routing -> constraint gate
  -> objective -> execution -> memory/skills), exported as ``Runtime``;
- the Neural Capability Platform (interfaces, event bus, DI container,
  hierarchical memory, knowledge graph), exported as ``PlatformRuntime``
  and ``Container``.
"""

__version__ = "0.2.0"

from .api.protocol import TaskRequest, TaskResponse, handle_request
from .core.entities import Goal, Result, Task, Tool
from .core.runtime import Runtime, build_default_universe
from .core.transformations import TransformationCandidate
from .core.universe import Entity, Relation, Universe
from .distributed.cluster import Cluster, Node
from .runtime.container import Container
from .runtime.runtime import Runtime as PlatformRuntime

__all__ = [
    "Runtime",
    "PlatformRuntime",
    "Container",
    "build_default_universe",
    "Universe",
    "Entity",
    "Relation",
    "TransformationCandidate",
    "Goal",
    "Task",
    "Tool",
    "Result",
    "TaskRequest",
    "TaskResponse",
    "handle_request",
    "Cluster",
    "Node",
]
