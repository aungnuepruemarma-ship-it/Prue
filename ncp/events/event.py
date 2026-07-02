"""Event model - Core event types for the system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from ncp.utils.timeutils import utcnow


class EventType(Enum):
    """Standard event types."""
    # Planning
    PLANNER_STARTED = "planner.started"
    PLANNER_FINISHED = "planner.finished"
    PLANNER_FAILED = "planner.failed"

    # Routing
    ROUTER_SELECTED = "router.selected"
    ROUTER_FAILED = "router.failed"

    # Execution
    EXECUTOR_STARTED = "executor.started"
    EXECUTOR_FINISHED = "executor.finished"
    EXECUTOR_FAILED = "executor.failed"

    # Memory
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"
    MEMORY_CONSOLIDATED = "memory.consolidated"
    MEMORY_FORGOTTEN = "memory.forgotten"

    # Graph
    GRAPH_UPDATED = "graph.updated"
    GRAPH_COMPRESSED = "graph.compressed"

    # Constraint
    CONSTRAINT_PASSED = "constraint.passed"
    CONSTRAINT_VIOLATED = "constraint.violated"

    # Simulation
    SIMULATION_STARTED = "simulation.started"
    SIMULATION_FINISHED = "simulation.finished"

    # System
    SYSTEM_STARTED = "system.started"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"

    # Skill
    SKILL_CREATED = "skill.created"
    SKILL_UPDATED = "skill.updated"
    SKILL_PROMOTED = "skill.promoted"

    # Research
    RESEARCH_HYPOTHESIS = "research.hypothesis"
    RESEARCH_VERIFIED = "research.verified"
    RESEARCH_PUBLISHED = "research.published"


@dataclass
class Event:
    """Core event model.

    Event flow: Planner -> EventBus -> Memory -> Monitoring -> Research -> Workers
    No module directly calls another. Everything emits events.
    """
    id: UUID = field(default_factory=uuid4)
    type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    priority: int = 0
    timestamp: datetime = field(default_factory=utcnow)
    correlation_id: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "type": self.type,
            "payload": self.payload,
            "source": self.source,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": str(self.correlation_id) if self.correlation_id else None,
        }

    @classmethod
    def create(cls, event_type: EventType, payload: Dict[str, Any],
               source: str = "", priority: int = 0,
               correlation_id: Optional[UUID] = None) -> "Event":
        """Factory method for creating events."""
        return cls(
            type=event_type.value,
            payload=payload,
            source=source,
            priority=priority,
            correlation_id=correlation_id,
        )
