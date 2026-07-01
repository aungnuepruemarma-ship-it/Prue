from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..planning.planner import Plan


@dataclass
class IRInstruction:
    op: str
    args: dict[str, Any] = field(default_factory=dict)

@dataclass
class IntermediateRepresentation:
    instructions: list[IRInstruction] = field(default_factory=list)

    def task_hints(self) -> list[str]:
        return [inst.args.get("task_type", inst.op) for inst in self.instructions]

    def to_dict(self) -> dict[str, Any]:
        return {"instructions": [{"op": i.op, "args": i.args} for i in self.instructions]}

def compile_plan(plan: Plan) -> IntermediateRepresentation:
    """Lower a Plan into IR instructions the runtime routes on."""
    instructions = [
        IRInstruction(op=step.name, args={"task_type": step.task_type, **step.details})
        for step in plan.steps
    ]
    return IntermediateRepresentation(instructions=instructions)
