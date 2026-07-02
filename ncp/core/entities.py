"""Entity hierarchy - Everything derives from Entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ncp.utils.timeutils import utcnow


@dataclass
class Entity:
    """Base entity. Everything derives from this.

    Hierarchy:
        Entity -> Goal -> Task -> Memory -> Skill -> Tool -> Result
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    version: str = "1.0"
    provenance_id: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
            "provenance_id": str(self.provenance_id) if self.provenance_id else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        """Deserialize from dictionary."""
        data = data.copy()
        data["id"] = UUID(data["id"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("provenance_id"):
            data["provenance_id"] = UUID(data["provenance_id"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Goal(Entity):
    """A high-level goal to achieve."""
    priority: int = 0
    deadline: Optional[datetime] = None
    parent_id: Optional[UUID] = None
    sub_goals: List[UUID] = field(default_factory=list)
    status: str = "pending"  # pending, active, completed, failed
    constraints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "priority": self.priority,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "sub_goals": [str(g) for g in self.sub_goals],
            "status": self.status,
            "constraints": self.constraints,
        })
        return data


@dataclass
class Task(Goal):
    """An executable task derived from a goal."""
    capability_required: str = ""
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[UUID] = field(default_factory=list)
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    execution_time_ms: float = 0.0
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "capability_required": self.capability_required,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "dependencies": [str(d) for d in self.dependencies],
            "estimated_cost": self.estimated_cost,
            "actual_cost": self.actual_cost,
            "execution_time_ms": self.execution_time_ms,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        })
        return data


@dataclass
class Memory(Entity):
    """A memory item stored in the system."""
    content: str = ""
    memory_type: str = "episodic"  # working, session, episodic, semantic, procedural, skill, archive
    confidence: float = 1.0
    importance: float = 0.5
    recency: float = 1.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    embeddings: Optional[List[float]] = None
    tags: List[str] = field(default_factory=list)
    source_task_id: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "content": self.content,
            "memory_type": self.memory_type,
            "confidence": self.confidence,
            "importance": self.importance,
            "recency": self.recency,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "embeddings": self.embeddings,
            "tags": self.tags,
            "source_task_id": str(self.source_task_id) if self.source_task_id else None,
        })
        return data

    def score_relevance(self, query: str) -> float:
        """Score relevance to a query. Simple implementation."""
        query_lower = query.lower()
        content_lower = self.content.lower()
        score = 0.0
        if query_lower in content_lower:
            score += 0.5
        words = query_lower.split()
        matches = sum(1 for w in words if w in content_lower)
        score += 0.5 * (matches / max(len(words), 1))
        return score * self.importance * self.confidence * self.recency


@dataclass
class Skill(Memory):
    """A reusable skill extracted from successful traces."""
    trigger_patterns: List[str] = field(default_factory=list)
    workflow: Dict[str, Any] = field(default_factory=dict)
    success_count: int = 0
    failure_count: int = 0
    average_execution_time_ms: float = 0.0
    lineage: List[UUID] = field(default_factory=list)
    is_active: bool = True

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "trigger_patterns": self.trigger_patterns,
            "workflow": self.workflow,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "average_execution_time_ms": self.average_execution_time_ms,
            "lineage": [str(l) for l in self.lineage],
            "is_active": self.is_active,
        })
        return data


@dataclass
class Tool(Skill):
    """An external tool integration."""
    tool_type: str = ""  # "api", "function", "model", "solver"
    endpoint: str = ""
    parameters_schema: Dict[str, Any] = field(default_factory=dict)
    auth_required: bool = False
    rate_limit: int = 0  # calls per minute

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "tool_type": self.tool_type,
            "endpoint": self.endpoint,
            "parameters_schema": self.parameters_schema,
            "auth_required": self.auth_required,
            "rate_limit": self.rate_limit,
        })
        return data


@dataclass
class Result(Entity):
    """Result of task execution."""
    task_id: UUID = field(default_factory=uuid4)
    status: str = "pending"  # pending, success, failure, partial
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    cost: float = 0.0
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "task_id": str(self.task_id),
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "cost": self.cost,
            "confidence": self.confidence,
        })
        return data


# Supporting classes
@dataclass
class State:
    """System state representation."""
    name: str = ""
    variables: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "variables": self.variables,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Universe:
    """Represents the problem universe/domain."""
    name: str = ""
    entities: List[Entity] = field(default_factory=list)
    constraints: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Transformation:
    """A state transformation."""
    name: str = ""
    preconditions: Dict[str, Any] = field(default_factory=dict)
    postconditions: Dict[str, Any] = field(default_factory=dict)
    cost: float = 0.0


@dataclass
class Metadata:
    """Structured metadata."""
    key: str = ""
    value: Any = None
    category: str = "general"
    source: str = ""


@dataclass
class Objective:
    """Planning objective function."""
    name: str = ""
    weight: float = 1.0
    maximize: bool = True


@dataclass
class Version:
    """Version information."""
    major: int = 0
    minor: int = 1
    patch: int = 0
    label: str = ""

    def __str__(self) -> str:
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.label:
            v += f"-{self.label}"
        return v
