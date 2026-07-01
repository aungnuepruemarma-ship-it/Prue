from __future__ import annotations

from dataclasses import dataclass, field

from ..core.universe import Universe


@dataclass
class WorldModel:
    facts: dict[str, str] = field(default_factory=dict)
    goals: list[str] = field(default_factory=list)

    def update_fact(self, key: str, value: str) -> None:
        self.facts[key] = value

    def observe(self, universe: Universe, goal: str, chosen: str) -> None:
        """Refresh the model's beliefs after a committed runtime step."""
        self.update_fact("entity_count", str(len(universe.entities)))
        self.update_fact("relation_count", str(len(universe.relations)))
        self.update_fact("universe_version", str(universe.version))
        self.update_fact("last_goal", goal)
        self.update_fact("last_action", chosen)
        if goal not in self.goals:
            self.goals.append(goal)

    def to_dict(self) -> dict:
        return {"facts": dict(self.facts), "goals": list(self.goals)}
