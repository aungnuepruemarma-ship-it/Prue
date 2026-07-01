from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import json
from typing import Any
from ..core.universe import Universe
from ..memory.graph import MemoryGraph
from ..memory.skills import SkillLibrary

class JsonStore:
    def __init__(self, root: str = "ncp_output"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_universe(self, universe: Universe) -> None:
        path = self.root / "universe.json"
        path.write_text(json.dumps(universe.snapshot("saved"), indent=2), encoding="utf-8")

    def save_history(self, events: list[dict[str, Any]]) -> None:
        path = self.root / "episodes.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")

    def save_graph(self, graph: MemoryGraph) -> None:
        path = self.root / "memory_graph.json"
        data = {
            "nodes": [asdict(n) for n in graph.nodes.values()],
            "edges": [asdict(e) for e in graph.edges],
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def save_skills(self, skills: SkillLibrary) -> None:
        path = self.root / "skills.json"
        path.write_text(json.dumps(skills.to_dict(), indent=2), encoding="utf-8")
