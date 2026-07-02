"""Procedural memory - Reusable workflows and methods."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class Workflow:
    """A reusable workflow."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    success_count: int = 0
    failure_count: int = 0
    avg_execution_time_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)


@dataclass
class ProceduralMemory:
    """Stores reusable workflows and methods."""
    max_workflows: int = 1000

    workflows: Dict[UUID, Workflow] = field(default_factory=dict)
    name_index: Dict[str, UUID] = field(default_factory=dict)

    def add_workflow(self, name: str, steps: List[Dict[str, Any]],
                     description: str = "",
                     parameters: Dict[str, Any] = None) -> Workflow:
        """Add a workflow."""
        workflow = Workflow(
            name=name,
            description=description,
            steps=steps,
            parameters=parameters or {},
        )
        self.workflows[workflow.id] = workflow
        self.name_index[name] = workflow.id
        return workflow

    def get_workflow(self, name: str) -> Optional[Workflow]:
        """Get workflow by name."""
        workflow_id = self.name_index.get(name)
        if workflow_id:
            return self.workflows.get(workflow_id)
        return None

    def find_by_tags(self, tags: List[str]) -> List[Workflow]:
        """Find workflows matching tags."""
        results = []
        for workflow in self.workflows.values():
            if any(tag in workflow.tags for tag in tags):
                results.append(workflow)
        return results

    @property
    def workflow_count(self) -> int:
        return len(self.workflows)
