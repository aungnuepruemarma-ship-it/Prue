"""Skill registry - Stores skill metadata."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID

from ncp.core.entities import Skill


@dataclass
class SkillRegistry:
    """Stores skill metadata, versions, confidence, dependencies, status."""

    skills: Dict[UUID, Skill] = field(default_factory=dict)

    def register(self, skill: Skill) -> None:
        self.skills[skill.id] = skill

    def get(self, skill_id: UUID) -> Optional[Skill]:
        return self.skills.get(skill_id)

    def find_by_name(self, name: str) -> List[Skill]:
        return [s for s in self.skills.values() if name.lower() in s.name.lower()]

    def list_active(self) -> List[Skill]:
        return [s for s in self.skills.values() if s.is_active]

    @property
    def count(self) -> int:
        return len(self.skills)
