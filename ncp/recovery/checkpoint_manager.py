"""Checkpoint manager — Task -> Checkpoint -> Save DAG/Variables/Memory -> Continue."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ncp.execution.dag import ExecutionDAG
from ncp.storage.checkpoint_store import CheckpointStore


@dataclass
class CheckpointManager:
    store: CheckpointStore
    saved: int = field(default=0)

    def checkpoint(self, dag: ExecutionDAG, variables: dict[str, Any] | None = None,
                   memory_refs: list[str] | None = None) -> str:
        checkpoint_id = self.store.save(dag.run_id, {
            "dag": dag.to_dict(),
            "variables": variables or {},
            "memory_refs": memory_refs or [],
        })
        self.saved += 1
        return checkpoint_id

    def latest(self, run_id: str) -> dict[str, Any] | None:
        return self.store.load_latest(run_id)

    def load_dag(self, run_id: str) -> ExecutionDAG | None:
        record = self.store.load_latest(run_id)
        if not record:
            return None
        return ExecutionDAG.from_dict(record["payload"]["dag"])
