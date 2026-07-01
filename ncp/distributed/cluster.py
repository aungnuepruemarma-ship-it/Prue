from __future__ import annotations

from dataclasses import dataclass, field

from ..api.protocol import TaskRequest, TaskResponse, handle_request
from ..core.runtime import Runtime, build_default_universe
from ..utils.config import Config
from ..utils.ids import new_id


@dataclass
class Node:
    node_id: str
    runtime: Runtime
    status: str = "online"

@dataclass
class Cluster:
    """Round-robins goals across nodes, each owning its own runtime."""

    nodes: list[Node] = field(default_factory=list)
    _next: int = 0

    def add_node(self, node_id: str, runtime: Runtime | None = None, output_dir: str | None = None) -> Node:
        if runtime is None:
            config = Config(output_dir=output_dir) if output_dir else Config(output_dir=f"ncp_output/{node_id}")
            runtime = Runtime(build_default_universe(), config=config)
        node = Node(node_id=node_id, runtime=runtime)
        self.nodes.append(node)
        return node

    def online_nodes(self) -> list[Node]:
        return [n for n in self.nodes if n.status == "online"]

    def submit(self, goal: str) -> TaskResponse:
        nodes = self.online_nodes()
        if not nodes:
            return TaskResponse(task_id=new_id("t"), status="no_nodes", explanation="No online nodes in the cluster.")
        node = nodes[self._next % len(nodes)]
        self._next += 1
        request = TaskRequest(task_id=new_id("t"), goal=goal, payload={"node": node.node_id})
        response = handle_request(node.runtime, request)
        response.result["node"] = node.node_id
        return response
