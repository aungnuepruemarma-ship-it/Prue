from ncp.core.activation import ActivationEngine
from ncp.core.runtime import build_default_universe
from ncp.routing.router import CapabilityRouter


def test_registry_selects_research_card_for_research_goal():
    router = CapabilityRouter()
    assert router.select_card("research the best approach").metadata["reasoner"] == "llm"


def test_registry_selects_engineering_card_for_build_goal():
    router = CapabilityRouter()
    assert router.select_card("build the indexing program").metadata["reasoner"] == "mythos"


def test_registry_falls_back_to_default_card():
    router = CapabilityRouter()
    assert router.select_card("hello world").name == "rule"


def test_task_hint_overrides_goal_keywords():
    router = CapabilityRouter()
    assert router.select_card("hello world", task_hint="research").metadata["reasoner"] == "llm"


def test_route_produces_candidates():
    router = CapabilityRouter()
    u = build_default_universe()
    active = ActivationEngine().score(u, "update the root").active_entity_ids
    candidates = router.route("update the root", u, active)
    assert candidates
    assert all(c.task_type for c in candidates)


def test_activation_threshold_and_fallback():
    engine = ActivationEngine()
    u = build_default_universe()
    matched = engine.score(u, "inspect the memory tier")
    assert "e_mem" in matched.active_entity_ids
    unmatched = engine.score(u, "zzz qqq")
    assert unmatched.active_entity_ids == ["e_root"], "fallback picks highest-confidence entity"
