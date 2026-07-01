from ncp.core.runtime import Runtime
from ncp.objective.objective import ObjectiveFunction


def scores_for(runtime: Runtime, goal: str) -> dict[str, float]:
    candidates = runtime.propose_candidates(goal)
    obj = ObjectiveFunction()
    return {
        c.name: obj.score(runtime.universe, c, goal=goal, history=runtime.history.events)
        for c in candidates
    }


def test_novelty_is_zero_for_seen_candidates(runtime):
    goal = "update the root entity"
    candidates = runtime.propose_candidates(goal)
    cand = next(c for c in candidates if c.name == "update_entity")
    fresh = ObjectiveFunction().score(runtime.universe, cand, goal=goal, history=runtime.history.events)
    runtime.history.record({"goal": goal, "candidate": "update_entity", "status": "accepted"})
    seen = ObjectiveFunction().score(runtime.universe, cand, goal=goal, history=runtime.history.events)
    assert seen > fresh, "a previously tried candidate must lose its novelty bonus"


def test_create_goal_prefers_create_candidate(runtime):
    scores = scores_for(runtime, "create a new concept entity")
    assert scores["create_entity"] == min(scores.values()), scores


def test_runtime_step_chooses_goal_relevant_action(runtime):
    result = runtime.step("create a new concept entity")
    assert result.status == "accepted"
    assert result.chosen["name"] == "create_entity"


def test_noop_can_still_win_on_pure_recall_goal(runtime):
    scores = scores_for(runtime, "query memory")
    assert scores["query_memory"] == min(scores.values()), scores
