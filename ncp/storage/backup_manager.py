"""Backup manager — zip snapshots of the whole storage root."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from ncp.utils.timeutils import utcnow


class BackupManager:
    def __init__(self, storage_root: str = "storage", backup_dir: str = "storage/backups"):
        self.storage_root = Path(storage_root)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, label: str = "") -> Path:
        stamp = utcnow().strftime("%Y%m%dT%H%M%S")
        name = f"backup_{stamp}{('_' + label) if label else ''}.zip"
        target = self.backup_dir / name
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in self.storage_root.rglob("*"):
                if path.is_file() and self.backup_dir not in path.parents:
                    zf.write(path, path.relative_to(self.storage_root))
        return target

    def list_backups(self) -> list[str]:
        return sorted(p.name for p in self.backup_dir.glob("backup_*.zip"))

    def restore(self, backup_name: str, target_root: str | None = None) -> Path:
        source = self.backup_dir / backup_name
        if not source.exists():
            raise FileNotFoundError(backup_name)
        destination = Path(target_root) if target_root else self.storage_root
        destination.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source) as zf:
            zf.extractall(destination)
        return destination

    def prune(self, keep: int = 5) -> int:
        backups = self.list_backups()
        removed = 0
        for name in backups[:-keep] if keep else backups:
            (self.backup_dir / name).unlink()
            removed += 1
        return removed

    def delete_all(self) -> None:
        shutil.rmtree(self.backup_dir, ignore_errors=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
