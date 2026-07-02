"""Session memory - Task-level traces before promotion to episodic."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ncp.core.entities import Memory, Result, Task


@dataclass
class SessionTrace:
    """A single trace in a session."""
    id: UUID = field(default_factory=uuid4)
    task: Optional[Task] = None
    result: Optional[Result] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionMemory:
    """Stores one task/session's working trace before promotion to episodic memory."""
    session_id: UUID = field(default_factory=uuid4)
    name: str = ""
    traces: List[SessionTrace] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_trace(self, task: Task, result: Result,
                  context: Dict[str, Any] = None) -> SessionTrace:
        """Add a task-result trace to the session."""
        trace = SessionTrace(
            task=task,
            result=result,
            context=context or {},
        )
        self.traces.append(trace)
        return trace

    def get_summary(self) -> str:
        """Get session summary."""
        success = sum(1 for t in self.traces if t.result and t.result.status == "success")
        total = len(self.traces)
        return f"Session {self.name}: {success}/{total} tasks succeeded"

    def to_memory_items(self) -> List[Memory]:
        """Convert session traces to memory items."""
        memories = []
        for trace in self.traces:
            content = f"Task: {trace.task.name if trace.task else 'unknown'}"
            if trace.result:
                content += f" -> {trace.result.status}"
            memories.append(Memory(
                content=content,
                memory_type="session",
                source_task_id=trace.task.id if trace.task else None,
            ))
        return memories

    @property
    def trace_count(self) -> int:
        return len(self.traces)

    @property
    def duration_seconds(self) -> float:
        if not self.traces:
            return 0.0
        start = self.created_at
        end = self.traces[-1].timestamp if self.traces else start
        return (end - start).total_seconds()
