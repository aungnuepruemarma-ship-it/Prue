"""Artifact store — filesystem persistence for produced artifacts.

Reports, code, images, notebooks: anything a run produces that outlives it.
"""

from __future__ import annotations

from pathlib import Path

from ncp.utils.timeutils import utcnow


class ArtifactStore:
    def __init__(self, root: str = "storage/artifacts"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, content: bytes | str, category: str = "general") -> Path:
        directory = self.root / category
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            path.write_bytes(content)
        return path

    def load(self, name: str, category: str = "general") -> bytes | None:
        path = self.root / category / name
        if not path.exists():
            return None
        return path.read_bytes()

    def list_artifacts(self, category: str | None = None) -> list[str]:
        base = self.root / category if category else self.root
        if not base.exists():
            return []
        return sorted(str(p.relative_to(self.root)) for p in base.rglob("*") if p.is_file())

    def timestamped_name(self, stem: str, suffix: str) -> str:
        return f"{stem}_{utcnow().strftime('%Y%m%dT%H%M%S')}{suffix}"
