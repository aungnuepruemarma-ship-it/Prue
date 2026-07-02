"""Episodic memory - Task episodes with timestamps, transitions, outputs."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ncp.core.entities import Result, Task
from ncp.utils.timeutils import utcnow


@dataclass
class Episode:
    """A single episode in memory."""
    id: UUID = field(default_factory=uuid4)
    task_name: str = ""
    task_id: Optional[UUID] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    transitions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=utcnow)
    duration_ms: float = 0.0
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EpisodicMemory:
    """Stores task episodes with full context.

    Preserves timestamps, transitions, and outputs.
    """
    max_episodes: int = 10000
    episodes: List[Episode] = field(default_factory=list)

    def add_episode(self, task: Task, result: Result,
                    transitions: List[str] = None) -> Episode:
        """Record a task execution episode."""
        episode = Episode(
            task_name=task.name,
            task_id=task.id,
            input_data=task.inputs,
            output_data=result.output if result else {},
            transitions=transitions or [],
            duration_ms=result.execution_time_ms if result else 0.0,
            success=result.status == "success" if result else False,
        )
        self.episodes.append(episode)

        # Enforce limit
        if len(self.episodes) > self.max_episodes:
            self.episodes = self.episodes[-self.max_episodes:]

        return episode

    def get_recent(self, n: int = 10) -> List[Episode]:
        """Get n most recent episodes."""
        return self.episodes[-n:]

    def get_by_task(self, task_id: UUID) -> List[Episode]:
        """Get episodes for a specific task."""
        return [e for e in self.episodes if e.task_id == task_id]

    def get_successful(self) -> List[Episode]:
        """Get successful episodes."""
        return [e for e in self.episodes if e.success]

    def search(self, query: str, top_k: int = 10) -> List[Episode]:
        """Search episodes by content."""
        scored = []
        for ep in self.episodes:
            score = 0.0
            text = f"{ep.task_name} {' '.join(ep.transitions)}"
            if query.lower() in text.lower():
                score += 1.0
            if score > 0:
                scored.append((ep, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [ep for ep, _ in scored[:top_k]]

    @property
    def episode_count(self) -> int:
        return len(self.episodes)

    @property
    def success_rate(self) -> float:
        if not self.episodes:
            return 0.0
        return sum(1 for e in self.episodes if e.success) / len(self.episodes)
