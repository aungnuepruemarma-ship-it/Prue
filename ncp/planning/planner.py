from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from ..core.universe import Universe

@dataclass
class PlanStep:
    name: str
    task_type: str
    details: dict[str, Any] = field(default_factory=dict)

@dataclass
class Plan:
    goal: str
    steps: list[PlanStep] = field(default_factory=list)

class Planner:
    def plan(self, goal: str, universe: Universe) -> Plan:
        goal_l = goal.lower()
        steps: list[PlanStep] = []
        if any(k in goal_l for k in ["build", "code", "implement"]):
            steps.append(PlanStep("draft_spec", "plan", {"focus": "architecture"}))
            steps.append(PlanStep("select_modules", "plan", {"focus": "modules"}))
            steps.append(PlanStep("execute_build", "execute", {"focus": "code"}))
        elif any(k in goal_l for k in ["research", "find", "compare"]):
            steps.append(PlanStep("collect_sources", "research", {"focus": "sources"}))
            steps.append(PlanStep("extract_patterns", "research", {"focus": "patterns"}))
        else:
            steps.append(PlanStep("analyze_goal", "plan", {"goal": goal}))
            steps.append(PlanStep("route_task", "plan", {"goal": goal}))
        return Plan(goal=goal, steps=steps)
