from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
from typing import Any

@dataclass
class Skill:
    name: str
    pattern: tuple[str, ...]
    description: str
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class SkillLibrary:
    skills: dict[str, Skill] = field(default_factory=dict)

    def add_skill(self, skill: Skill) -> None:
        self.skills[skill.name] = skill

    def to_dict(self) -> dict[str, Any]:
        return {name: {
            "name": skill.name,
            "pattern": list(skill.pattern),
            "description": skill.description,
            "version": skill.version,
            "metadata": skill.metadata,
        } for name, skill in self.skills.items()}

    def update_from_history(self, events: list[dict[str, Any]]) -> None:
        pass

@dataclass
class SkillExtractor:
    threshold: int = 2

    def promote(self, library: SkillLibrary, events: list[dict[str, Any]]) -> None:
        ops = [e.get("candidate") or e.get("op") for e in events if (e.get("candidate") or e.get("op"))]
        if len(ops) < 2:
            return
        grams = Counter(tuple(ops[i:i+2]) for i in range(len(ops)-1))
        for pattern, count in grams.items():
            if count >= self.threshold:
                name = "skill_" + "_".join(pattern)
                if name not in library.skills:
                    library.add_skill(Skill(
                        name=name,
                        pattern=pattern,
                        description=f"Reusable pattern detected: {pattern[0]} -> {pattern[1]}",
                        metadata={"support": count},
                    ))
