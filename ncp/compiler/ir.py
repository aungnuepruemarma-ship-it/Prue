from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class IRInstruction:
    op: str
    args: dict[str, Any] = field(default_factory=dict)

@dataclass
class IntermediateRepresentation:
    instructions: list[IRInstruction] = field(default_factory=list)
