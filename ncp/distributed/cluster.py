from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..api.protocol import TaskRequest, TaskResponse, handle_kernel_request
from ..utils.ids import new_id

if TYPE_CHECKING:
    from ..kernel.kernel import Kernel


@dataclass
class Node:
    node_id: str
    kernel: "Kernel"
    status: str = "online"


@dataclass
class Cluster:
    """Round-robins goals across nodes, each owning its own kernel."""

    nodes: list[Node] = field(default_factory=list)
    _next: int = 0

    def add_node(self, node_id: str, kernel: "Kernel | None" = None, output_dir: str | None = None) -> Node:
        if kernel is None:
            from ..kernel.kernel import Kernel
            kernel = Kernel(storage_root=output_dir or f"ncp_output/{node_id}")
        node = Node(node_id=node_id, kernel=kernel)
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
        response = handle_kernel_request(node.kernel, request)
        response.result["node"] = node.node_id
        return response

    def shutdown(self) -> None:
        for node in self.nodes:
            node.kernel.shutdown()
