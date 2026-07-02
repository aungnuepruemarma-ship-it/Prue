"""Bridge between the two skill lineages.

The reference runtime learns lightweight bigram skills
(:class:`ncp.memory.skills.Skill`); the platform manages rich skill
entities (:class:`ncp.core.entities.Skill`) in a :class:`SkillRegistry`.
This bridge promotes the former into the latter so learned patterns become
platform-visible capabilities.
"""

from __future__ import annotations

from ncp.core.entities import Skill as PlatformSkill
from ncp.memory.skills import Skill as PatternSkill
from ncp.memory.skills import SkillLibrary
from ncp.skills.registry import SkillRegistry


def to_platform_skill(pattern_skill: PatternSkill) -> PlatformSkill:
    """Convert a learned bigram skill into a platform skill entity."""
    return PlatformSkill(
        name=pattern_skill.name,
        description=pattern_skill.description,
        content=" -> ".join(pattern_skill.pattern),
        memory_type="skill",
        trigger_patterns=list(pattern_skill.pattern),
        workflow={"ops": list(pattern_skill.pattern)},
        success_count=pattern_skill.metadata.get("support", 0),
        metadata=dict(pattern_skill.metadata),
    )


def sync_library_to_registry(library: SkillLibrary, registry: SkillRegistry) -> int:
    """Register every learned pattern skill not yet present in the registry.

    Returns the number of skills newly registered.
    """
    known = {s.name for s in registry.skills.values()}
    added = 0
    for pattern_skill in library.skills.values():
        if pattern_skill.name not in known:
            registry.register(to_platform_skill(pattern_skill))
            added += 1
    return added
