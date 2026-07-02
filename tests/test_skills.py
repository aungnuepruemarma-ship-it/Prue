from ncp.memory.skills import SkillExtractor, SkillLibrary


def test_skill_extraction_promotes_repeated_pattern():
    lib = SkillLibrary()
    extractor = SkillExtractor(threshold=2)
    events = [
        {"candidate": "update_entity", "status": "accepted"},
        {"candidate": "query_memory", "status": "accepted"},
        {"candidate": "update_entity", "status": "accepted"},
        {"candidate": "query_memory", "status": "accepted"},
    ]
    extractor.promote(lib, events)
    assert "skill_update_entity_query_memory" in lib.skills


def test_rejected_events_do_not_promote_skills():
    lib = SkillLibrary()
    extractor = SkillExtractor(threshold=2)
    events = [
        {"candidate": "update_entity", "status": "rejected"},
        {"candidate": "query_memory", "status": "rejected"},
    ] * 3
    extractor.promote(lib, events)
    assert not lib.skills, "skills must only be promoted from successful traces"


def test_update_from_history_refreshes_support():
    lib = SkillLibrary()
    extractor = SkillExtractor(threshold=2)
    events = [
        {"candidate": "update_entity", "status": "accepted"},
        {"candidate": "query_memory", "status": "accepted"},
    ] * 2
    extractor.promote(lib, events)
    skill = lib.skills["skill_update_entity_query_memory"]
    assert skill.metadata["support"] == 2
    events *= 2
    lib.update_from_history(events)
    assert skill.metadata["support"] > 2
    assert skill.version > 1


def test_learned_skills_become_candidates(runtime):
    from ncp.memory.skills import Skill

    runtime.learn_skill(Skill(
        name="skill_update_entity_query_memory",
        pattern=("update_entity", "query_memory"),
        description="update then recall",
    ))
    goal = "update the active memory"
    candidates = runtime.propose_candidates(goal)
    skill_candidates = [c for c in candidates if c.name.startswith("skill:")]
    assert skill_candidates, [c.name for c in candidates]
    assert skill_candidates[0].task_type == "skill"

    result = runtime.step(goal)
    assert result.status == "accepted"


def test_skill_candidate_is_admissible_and_executable(runtime):
    from ncp.constraints.finite_phi import FinitePhiChecker
    from ncp.memory.skills import Skill

    runtime.learn_skill(Skill(
        name="skill_update_entity_query_memory",
        pattern=("update_entity", "query_memory"),
        description="update then recall",
    ))
    cand = next(c for c in runtime.propose_candidates("update memory") if c.name.startswith("skill:"))
    check = FinitePhiChecker().check(runtime.universe, cand, goal="update memory")
    assert check.admissible, check.violations
    version_before = runtime.universe.version
    cand.apply(runtime.universe)
    assert runtime.universe.version > version_before


def test_pattern_skills_bridge_to_platform_registry(runtime):
    from ncp.memory.skills import Skill
    from ncp.skills.bridge import sync_library_to_registry
    from ncp.skills.registry import SkillRegistry

    runtime.learn_skill(Skill(
        name="skill_update_entity_query_memory",
        pattern=("update_entity", "query_memory"),
        description="update then recall",
        metadata={"support": 3},
    ))
    registry = SkillRegistry()
    added = sync_library_to_registry(runtime.skills, registry)
    assert added == 1
    platform_skill = registry.find_by_name("skill_update_entity_query_memory")[0]
    assert platform_skill.trigger_patterns == ["update_entity", "query_memory"]
    assert platform_skill.success_count == 3
    assert sync_library_to_registry(runtime.skills, registry) == 0, "idempotent"
