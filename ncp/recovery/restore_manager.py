"""Restore manager — Restart -> Load Snapshot -> Restore State -> Continue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ncp.execution.dag import ExecutionDAG
from ncp.recovery.checkpoint_manager import CheckpointManager


@dataclass
class RestoreManager:
    checkpoints: CheckpointManager

    def restore_run(self, run_id: str) -> tuple[ExecutionDAG, dict[str, Any]] | None:
        """Rebuild a run's DAG and variables from its latest checkpoint.

        Nodes left mid-flight ("running") are reset to pending so they
        re-execute; completed work is preserved and will be skipped.
        """
        record = self.checkpoints.latest(run_id)
        if not record:
            return None
        dag = ExecutionDAG.from_dict(record["payload"]["dag"])
        for node in dag.nodes.values():
            if node.status == "running":
                node.status = "pending"
        return dag, dict(record["payload"].get("variables", {}))
