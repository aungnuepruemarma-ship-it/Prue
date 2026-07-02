"""DAG executor — runs execution graphs with per-node checkpoints.

Node execution is injected (the kernel supplies a provider-backed runner),
so this module stays independent of any particular model or runtime. A
checkpoint hook fires after every node, and ``run`` accepts a previously
checkpointed DAG whose completed nodes are skipped — the recovery path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ncp.execution.dag import ExecutionDAG
from ncp.execution.node import DAGNode

NodeRunner = Callable[[DAGNode], dict[str, Any]]
CheckpointHook = Callable[[ExecutionDAG], None]


@dataclass
class DAGExecutor:
    node_runner: NodeRunner
    checkpoint_hook: CheckpointHook | None = None

    def run(self, dag: ExecutionDAG) -> ExecutionDAG:
        while not dag.is_complete:
            ready = dag.ready_nodes()
            if not ready:
                # blocked: remaining pending nodes depend on failed ones
                for node in dag.nodes.values():
                    if node.status == "pending":
                        node.status = "skipped"
                        node.result = {"error": "dependency_failed"}
                break
            for node in ready:
                node.status = "running"
                try:
                    node.result = self.node_runner(node)
                    node.status = "completed" if node.result.get("status", "success") in {"success", "accepted"} else "failed"
                except Exception as exc:  # a node failure must not kill the run
                    node.result = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
                    node.status = "failed"
                if self.checkpoint_hook is not None:
                    self.checkpoint_hook(dag)
        return dag
