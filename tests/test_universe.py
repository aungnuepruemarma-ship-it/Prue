from ncp.constraints.finite_phi import FinitePhiChecker
from ncp.core.runtime import build_default_universe
from ncp.core.transformations import TransformationCandidate, make_update_entity
from ncp.objective.objective import ObjectiveFunction


def update_candidate(entity_id="e_root", patch=None):
    return TransformationCandidate(
        name="update_entity",
        task_type="update",
        params={"entity_id": entity_id},
        execute=make_update_entity(entity_id, patch or {"x": 1}, {"y": 2}),
    )


def test_clone_is_deep():
    u = build_default_universe()
    trial = u.clone()
    trial.entities["e_root"].state["mutated"] = True
    trial.relations[0].metadata["mutated"] = True
    assert "mutated" not in u.entities["e_root"].state
    assert "mutated" not in u.relations[0].metadata


def test_phi_check_does_not_mutate_live_universe():
    u = build_default_universe()
    before = dict(u.entities["e_root"].state)
    result = FinitePhiChecker().check(u, update_candidate(patch={"tainted": True}), goal="anything")
    assert result.admissible
    assert dict(u.entities["e_root"].state) == before


def test_objective_scoring_does_not_mutate_live_universe():
    u = build_default_universe()
    before = dict(u.entities["e_root"].state)
    ObjectiveFunction().score(u, update_candidate(patch={"tainted": True}), goal="update")
    assert dict(u.entities["e_root"].state) == before


def test_snapshot_includes_history_and_round_trips():
    from ncp.core.universe import Universe

    u = build_default_universe()
    update_candidate().apply(u)
    snap = u.snapshot("test")
    assert snap["history"], "op-level provenance must be persisted"
    restored = Universe.from_snapshot(snap)
    assert restored.snapshot("test") == snap
