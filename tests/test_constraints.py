from ncp.core.runtime import build_default_universe
from ncp.constraints.finite_phi import FinitePhiChecker
from ncp.core.transformations import make_update_entity
from ncp.core.transformation import TransformationCandidate

def test_phi_accepts_valid_update():
    u = build_default_universe()
    checker = FinitePhiChecker()
    cand = TransformationCandidate(
        name="update_entity",
        task_type="update",
        params={"entity_id": "e_root"},
        execute=make_update_entity("e_root", {"x": 1}, {"y": 2}),
    )
    result = checker.check(u, cand, goal="update memory")
    assert result.admissible is True
