"""Crash recovery — find interrupted runs and decide what can resume."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ncp.recovery.checkpoint_manager import CheckpointManager


@dataclass
class CrashRecovery:
    checkpoints: CheckpointManager

    def interrupted_runs(self) -> list[str]:
        """Runs whose latest checkpointed DAG never reached a terminal state."""
        interrupted = []
        for run_id in self.checkpoints.store.list_runs():
            dag = self.checkpoints.load_dag(run_id)
            if dag is not None and not dag.is_complete:
                interrupted.append(run_id)
        return interrupted

    def diagnose(self, run_id: str) -> dict[str, Any] | None:
        dag = self.checkpoints.load_dag(run_id)
        if dag is None:
            return None
        by_status: dict[str, int] = {}
        for node in dag.nodes.values():
            by_status[node.status] = by_status.get(node.status, 0) + 1
        return {
            "run_id": run_id,
            "goal": dag.goal,
            "node_statuses": by_status,
            "resumable": not dag.is_complete,
        }
