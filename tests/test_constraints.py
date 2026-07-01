from ncp.constraints.finite_phi import FinitePhiChecker
from ncp.core.runtime import build_default_universe
from ncp.core.transformations import TransformationCandidate, make_add_relation, make_update_entity
from ncp.core.universe import Relation
from ncp.utils.config import Config


def valid_update():
    return TransformationCandidate(
        name="update_entity",
        task_type="update",
        params={"entity_id": "e_root"},
        execute=make_update_entity("e_root", {"x": 1}, {"y": 2}),
    )


def test_phi_accepts_valid_update():
    result = FinitePhiChecker().check(build_default_universe(), valid_update(), goal="update memory")
    assert result.admissible is True


def test_phi_rejects_unknown_task_type():
    cand = TransformationCandidate(name="weird", task_type="teleport")
    result = FinitePhiChecker().check(build_default_universe(), cand)
    assert not result.admissible
    assert any(v.startswith("unknown_task_type") for v in result.violations)


def test_phi_rejects_missing_name():
    cand = TransformationCandidate(name="", task_type="update")
    result = FinitePhiChecker().check(build_default_universe(), cand)
    assert "missing_candidate_name" in result.violations


def test_phi_rejects_missing_entity():
    cand = TransformationCandidate(
        name="update_entity", task_type="update",
        execute=make_update_entity("no_such_entity", {"x": 1}, {}),
    )
    result = FinitePhiChecker().check(build_default_universe(), cand)
    assert any(v.startswith("missing_entity") for v in result.violations)


def test_phi_rejects_dangling_relation():
    cand = TransformationCandidate(
        name="add_relation", task_type="relate",
        execute=make_add_relation("e_root", "ghost", "haunts"),
    )
    result = FinitePhiChecker().check(build_default_universe(), cand)
    assert any(v.startswith("dangling_relation_target") for v in result.violations)


def test_phi_rejects_forbidden_creation_policy():
    cand = TransformationCandidate(name="create_entity", task_type="create")
    result = FinitePhiChecker().check(build_default_universe(), cand, goal="this is forbidden territory")
    assert "policy_forbids_creation_for_this_goal" in result.violations


def test_phi_rejects_entity_limit():
    checker = FinitePhiChecker(config=Config(max_entities=1))
    result = checker.check(build_default_universe(), valid_update())
    assert "entity_limit_exceeded" in result.violations


def test_phi_pre_existing_dangling_relation_detected():
    u = build_default_universe()
    u.add_relation(Relation(source="e_root", target="ghost", relation_type="haunts"))
    result = FinitePhiChecker().check(u, valid_update())
    assert any(v.startswith("dangling_relation_target") for v in result.violations)
