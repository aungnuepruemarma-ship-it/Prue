"""Skill memory - Versioned skill objects."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID

from ncp.core.entities import Skill


@dataclass
class SkillMemory:
    """Stores skill objects with versioned metadata."""
    max_skills: int = 500
    min_confidence: float = 0.7

    skills: Dict[UUID, Skill] = field(default_factory=dict)
    trigger_index: Dict[str, List[UUID]] = field(default_factory=dict)

    def add_skill(self, skill: Skill) -> None:
        """Add a skill."""
        if not skill.is_active:
            return
        self.skills[skill.id] = skill

        # Index by trigger patterns
        for pattern in skill.trigger_patterns:
            if pattern not in self.trigger_index:
                self.trigger_index[pattern] = []
            self.trigger_index[pattern].append(skill.id)

    def find_by_trigger(self, context: str) -> List[Skill]:
        """Find skills triggered by context."""
        triggered = []
        for pattern, skill_ids in self.trigger_index.items():
            if pattern.lower() in context.lower():
                for skill_id in skill_ids:
                    skill = self.skills.get(skill_id)
                    if skill and skill.is_active:
                        triggered.append(skill)
        return triggered

    def get_best_skill(self, context: str) -> Optional[Skill]:
        """Get best matching skill."""
        candidates = self.find_by_trigger(context)
        if not candidates:
            return None
        return max(candidates, key=lambda s: s.success_rate * s.confidence)

    def promote_skill(self, skill_id: UUID) -> bool:
        """Promote a skill to higher confidence."""
        skill = self.skills.get(skill_id)
        if skill:
            skill.confidence = min(1.0, skill.confidence + 0.1)
            return True
        return False

    @property
    def active_skill_count(self) -> int:
        return sum(1 for s in self.skills.values() if s.is_active)
