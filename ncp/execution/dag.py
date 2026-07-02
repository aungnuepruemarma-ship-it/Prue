"""Execution DAG — requests compile into graphs, not linear chains."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ncp.execution.node import DAGNode
from ncp.utils.ids import new_id


@dataclass
class ExecutionDAG:
    goal: str = ""
    run_id: str = field(default_factory=lambda: new_id("run"))
    nodes: dict[str, DAGNode] = field(default_factory=dict)

    def add_node(self, node: DAGNode) -> DAGNode:
        self.nodes[node.id] = node
        return node

    def add_dependency(self, node_id: str, depends_on: str) -> None:
        if depends_on not in self.nodes[node_id].depends_on:
            self.nodes[node_id].depends_on.append(depends_on)

    def topological_order(self) -> list[DAGNode]:
        order: list[DAGNode] = []
        resolved: set[str] = set()
        pending = dict(self.nodes)
        while pending:
            progress = False
            for node_id, node in list(pending.items()):
                if all(dep in resolved for dep in node.depends_on):
                    order.append(node)
                    resolved.add(node_id)
                    del pending[node_id]
                    progress = True
            if not progress:
                raise ValueError(f"cycle detected among nodes: {sorted(pending)}")
        return order

    def ready_nodes(self) -> list[DAGNode]:
        completed = {n.id for n in self.nodes.values() if n.status == "completed"}
        return [
            n for n in self.nodes.values()
            if n.status == "pending" and all(dep in completed for dep in n.depends_on)
        ]

    @property
    def is_complete(self) -> bool:
        return all(n.status in {"completed", "failed", "skipped"} for n in self.nodes.values())

    @property
    def succeeded(self) -> bool:
        return all(n.status == "completed" for n in self.nodes.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "run_id": self.run_id,
            "nodes": [n.to_dict() for n in self.topological_order()],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionDAG":
        dag = cls(goal=data.get("goal", ""), run_id=data.get("run_id", new_id("run")))
        for node_data in data.get("nodes", []):
            dag.add_node(DAGNode.from_dict(node_data))
        return dag
