"""DAG compiler — lowers goals through the planner into an execution DAG.

Compound goals split into parallel branches (" and ") or sequential chains
(", then "); each sub-goal's plan steps become dependent nodes, so a request
compiles into a graph instead of a linear chain.

When platform planner/simulator instances are supplied, each sub-goal is
additionally planned and simulated by the platform lineage, and the
resulting score / outcome prediction rides on every node's metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ncp.compiler.ir import compile_plan
from ncp.core.universe import Universe
from ncp.execution.dag import ExecutionDAG
from ncp.execution.node import DAGNode
from ncp.planning.planner import Planner

if TYPE_CHECKING:
    from ncp.planner.planner import Planner as PlatformPlanner
    from ncp.simulator.simulator import Simulator


def split_goal(goal: str) -> list[tuple[str, list[int]]]:
    """Split a compound goal into (sub_goal, depends_on_indices) pairs.

    ", then " chains sequentially; " and " branches in parallel.
    """
    sequential = [part.strip() for part in goal.split(", then ") if part.strip()]
    out: list[tuple[str, list[int]]] = []
    previous_layer: list[int] = []
    for segment in sequential:
        parallel = [p.strip() for p in segment.split(" and ") if p.strip()] or [segment]
        layer: list[int] = []
        for sub_goal in parallel:
            out.append((sub_goal, list(previous_layer)))
            layer.append(len(out) - 1)
        previous_layer = layer
    return out


class DAGCompiler:
    def __init__(
        self,
        planner: Planner | None = None,
        platform_planner: "PlatformPlanner | None" = None,
        platform_simulator: "Simulator | None" = None,
    ):
        self.planner = planner or Planner()
        self.platform_planner = platform_planner
        self.platform_simulator = platform_simulator

    def _platform_augment(self, sub_goal: str) -> dict[str, Any]:
        """Plan and simulate the sub-goal on the platform lineage."""
        if self.platform_planner is None:
            return {}
        from ncp.core.entities import Goal as PlatformGoal

        tasks = self.platform_planner.plan(PlatformGoal(name=sub_goal, description=sub_goal))
        meta: dict[str, Any] = {"platform_score": self.platform_planner.score(tasks)}
        if self.platform_simulator is not None and tasks:
            prediction = self.platform_simulator.simulate(tasks[0])
            meta["predicted_status"] = prediction.status
            meta["predicted_confidence"] = prediction.confidence
            meta["predicted_cost_ms"] = prediction.execution_time_ms
        return meta

    def compile(self, goal: str, universe: Universe | None = None) -> ExecutionDAG:
        universe = universe or Universe()
        dag = ExecutionDAG(goal=goal)
        index_to_tail: dict[int, str] = {}
        parts = split_goal(goal)
        for index, (sub_goal, depends_on) in enumerate(parts):
            plan = self.planner.plan(sub_goal, universe)
            ir = compile_plan(plan)
            platform_meta = self._platform_augment(sub_goal)
            previous_node_id: str | None = None
            for instruction in ir.instructions:
                node = dag.add_node(DAGNode(
                    name=instruction.op,
                    goal=sub_goal,
                    task_type=instruction.args.get("task_type", "plan"),
                    metadata=dict(platform_meta) | {"focus": instruction.args.get("focus", "")},
                ))
                if previous_node_id is not None:
                    dag.add_dependency(node.id, previous_node_id)
                else:
                    for dep_index in depends_on:
                        dag.add_dependency(node.id, index_to_tail[dep_index])
                previous_node_id = node.id
            index_to_tail[index] = previous_node_id
        return dag
