from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from .history import ngrams_from_events


def successful_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only events from successful traces.

    Runtime events carry a status; universe op-events (no status key) are only
    recorded when a transformation actually committed, so they count as
    successful too.
    """
    return [e for e in events if e.get("status", "accepted") == "accepted"]

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
        """Refresh support counts (and bump versions) for known skills."""
        grams = Counter(ngrams_from_events(successful_events(events)))
        for skill in self.skills.values():
            support = grams.get(skill.pattern, 0)
            if support > skill.metadata.get("support", 0):
                skill.metadata["support"] = support
                skill.version += 1

@dataclass
class SkillExtractor:
    threshold: int = 2

    def promote(self, library: SkillLibrary, events: list[dict[str, Any]]) -> None:
        grams = Counter(ngrams_from_events(successful_events(events)))
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
