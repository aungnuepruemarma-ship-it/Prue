"""Snapshot manager — full-system state snapshots for cold restarts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ncp.storage.storage_manager import StorageManager
from ncp.utils.timeutils import utcnow


@dataclass
class SnapshotManager:
    storage: StorageManager

    def snapshot(self, name: str, state: dict[str, Any]) -> str:
        snapshot_id = f"{name}_{utcnow().strftime('%Y%m%dT%H%M%S')}"
        self.storage.snapshots.create(snapshot_id, state)
        self.storage.save_document("world_state", "latest_snapshot", {"snapshot_id": snapshot_id})
        return snapshot_id

    def restore(self, snapshot_id: str) -> dict[str, Any] | None:
        return self.storage.snapshots.restore(snapshot_id)

    def restore_latest(self) -> dict[str, Any] | None:
        pointer = self.storage.load_document("world_state", "latest_snapshot")
        if not pointer:
            return None
        return self.restore(pointer["snapshot_id"])

    def list_snapshots(self) -> list[str]:
        return self.storage.snapshots.list_snapshots()
