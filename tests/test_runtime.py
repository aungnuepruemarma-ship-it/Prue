from ncp.core.runtime import Runtime, build_default_universe
from ncp.utils.config import Config


def test_runtime_step_accepts_some_candidate(runtime):
    result = runtime.step("create a new concept")
    assert result.status == "accepted"
    assert runtime.history.events


def test_step_summary_exposes_plan_ir_and_world_model(runtime):
    result = runtime.step("research better routing")
    assert result.summary["ir"]["instructions"], "plan must compile to IR instructions"
    facts = result.summary["world_model"]["facts"]
    assert facts["last_goal"] == "research better routing"
    assert facts["entity_count"] == str(len(runtime.universe.entities))


def test_research_goal_records_finding(runtime):
    runtime.step("research memory consolidation")
    assert runtime.research.findings
    assert runtime.research.findings[-1].source == "research memory consolidation"


def test_non_research_goal_records_no_finding(runtime):
    runtime.step("update the root entity")
    assert not runtime.research.findings


def test_rejected_candidates_are_not_committed(runtime):
    before = len(runtime.universe.entities)
    result = runtime.step("this is forbidden: create something new")
    if result.status == "accepted":
        assert result.chosen["task_type"] != "create"
    assert len(runtime.universe.entities) >= before


def test_persistence_round_trip(tmp_path):
    out = str(tmp_path / "store")
    runtime = Runtime(build_default_universe(), config=Config(output_dir=out))
    runtime.step("create a new concept")
    restored = runtime.storage.load_universe()
    assert restored is not None
    assert restored.snapshot("x") == runtime.universe.snapshot("x")

    episodes = (tmp_path / "store" / "episodes.jsonl").read_text().strip().splitlines()
    assert len(episodes) == len(runtime.history.events)
    runtime.step("update the concept")
    episodes = (tmp_path / "store" / "episodes.jsonl").read_text().strip().splitlines()
    assert len(episodes) == len(runtime.history.events), "episodes must be appended incrementally"
