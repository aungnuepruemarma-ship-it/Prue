from ncp.capabilities.registry import ProviderRecord, ProviderRegistry
from ncp.capabilities.selector import ProviderSelector
from ncp.learning.experience_db import ExperienceDB
from ncp.learning.reward_engine import RewardEngine
from ncp.learning.routing_optimizer import RoutingOptimizer
from ncp.storage.relational_store import RelationalStore
from ncp.storage.storage_manager import StorageManager
from ncp.world.world_state import WorldState


def test_world_state_round_trips_through_storage(tmp_path):
    storage = StorageManager(str(tmp_path / "storage"))
    world = WorldState(storage=storage)
    project = world.projects.create("apollo", description="moonshot")
    goal = world.goals.add("land on the moon", project_id=project.id)
    world.projects.attach_goal(project.id, goal.id)
    world.start_job("run_1", goal.text)
    world.finish_job("run_1", "completed")
    world.update_fact("entity_count", 7)
    world.save()

    reborn = WorldState(storage=StorageManager(str(tmp_path / "storage")))
    assert reborn.load()
    assert reborn.projects.find_by_name("apollo").description == "moonshot"
    assert reborn.goals.by_status("pending")[0].text == "land on the moon"
    assert reborn.jobs["run_1"]["status"] == "completed"
    assert reborn.facts["entity_count"] == "7"


def test_reward_engine_signs():
    rewards = RewardEngine()
    good = rewards.compute({"status": "accepted", "confidence": 0.9}, {"approved": True, "confidence": 0.9})
    bad = rewards.compute({"status": "failed"}, {"approved": False, "confidence": 0.1})
    assert good > 0 > bad


def seeded_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(ProviderRecord(id="veteran", backend="rule", capabilities=["research"],
                                     cost=1.0, latency=2.0, reliability=0.7, historical_success=0.5))
    registry.register(ProviderRecord(id="shiny", backend="llm", capabilities=["research"],
                                     cost=0.0, latency=0.1, reliability=1.0, historical_success=0.5))
    return registry


def test_learned_policy_overrides_keyword_default(tmp_path):
    """After observed episodes, the historically-successful provider wins even
    though the default (prior-based) policy prefers the other one."""
    registry = seeded_registry()
    selector = ProviderSelector(registry)
    requirements = {"capability": "research", "task_type": "research"}
    assert selector.select(requirements).id == "shiny", "default policy prefers cheap+reliable"

    experience = ExperienceDB(RelationalStore(str(tmp_path / "exp.db")))
    for _ in range(5):
        experience.record(run_id="r", goal="g", task_type="research", provider_id="veteran",
                          success=True, reward=1.5)
        experience.record(run_id="r", goal="g", task_type="research", provider_id="shiny",
                          success=False, reward=-1.0)
    optimizer = RoutingOptimizer(experience)
    optimizer.refresh()
    selector.policy = optimizer.learned_policy
    assert selector.select(requirements).id == "veteran", "learned policy must override the prior"
    assert optimizer.best_provider("research") == "veteran"


def test_registry_outcome_updates_historical_success():
    registry = seeded_registry()
    before = registry.get("shiny").historical_success
    registry.record_outcome("shiny", success=False)
    assert registry.get("shiny").historical_success < before
