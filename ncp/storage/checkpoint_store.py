"""Checkpoint store — per-run execution state that survives crashes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ncp.utils.timeutils import utcnow


class CheckpointStore:
    def __init__(self, root: str = "storage/checkpoints"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _run_dir(self, run_id: str) -> Path:
        directory = self.root / run_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def save(self, run_id: str, payload: dict[str, Any]) -> str:
        directory = self._run_dir(run_id)
        checkpoint_id = f"ckpt_{utcnow().strftime('%Y%m%dT%H%M%S_%f')}"
        record = {"checkpoint_id": checkpoint_id, "saved_at": utcnow().isoformat(), "payload": payload}
        (directory / f"{checkpoint_id}.json").write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
        return checkpoint_id

    def load_latest(self, run_id: str) -> dict[str, Any] | None:
        directory = self.root / run_id
        if not directory.exists():
            return None
        checkpoints = sorted(directory.glob("ckpt_*.json"))
        if not checkpoints:
            return None
        return json.loads(checkpoints[-1].read_text(encoding="utf-8"))

    def list_checkpoints(self, run_id: str) -> list[str]:
        directory = self.root / run_id
        if not directory.exists():
            return []
        return sorted(p.stem for p in directory.glob("ckpt_*.json"))

    def list_runs(self) -> list[str]:
        return sorted(p.name for p in self.root.iterdir() if p.is_dir())

    def delete_run(self, run_id: str) -> None:
        directory = self.root / run_id
        if directory.exists():
            for p in directory.glob("*.json"):
                p.unlink()
            directory.rmdir()
