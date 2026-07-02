from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..core.runtime import Runtime

if TYPE_CHECKING:
    from ..kernel.kernel import Kernel


@dataclass
class TaskRequest:
    task_id: str
    goal: str
    payload: dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskResponse:
    task_id: str
    status: str
    result: dict[str, Any] = field(default_factory=dict)
    explanation: str = ""

def handle_request(runtime: Runtime, request: TaskRequest) -> TaskResponse:
    """Drive one runtime step from a protocol-level task request."""
    result = runtime.step(request.goal)
    return TaskResponse(
        task_id=request.task_id,
        status=result.status,
        result={
            "chosen": result.chosen,
            "entity_count": result.summary.get("entity_count"),
            "next_goal": result.summary.get("next_goal"),
        },
        explanation=result.explanation,
    )


def handle_kernel_request(kernel: "Kernel", request: TaskRequest) -> TaskResponse:
    """Drive a full kernel pipeline run from a protocol-level task request."""
    response = kernel.submit(request.goal, project=request.payload.get("project"))
    return TaskResponse(
        task_id=request.task_id,
        status=response.status,
        result={
            "run_id": response.run_id,
            "confidence": response.confidence,
            "verified": response.verified,
            "nodes": len(response.node_results),
        },
        explanation=response.response,
    )
