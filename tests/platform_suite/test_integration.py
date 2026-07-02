"""End-to-end integration tests for the platform goal-execution path.

The 144 original unit tests never drove Runtime.execute_goal, which is why
a systemic EventBus API mismatch went unnoticed. These tests pin the whole
spine: goal -> planner -> router -> constraints -> executor -> memory.
"""

from ncp.core.entities import Goal
from ncp.events.bus import EventBus
from ncp.events.event import Event
from ncp.runtime.container import Container


def build_runtime():
    container = Container().build()
    runtime = container.get_runtime()
    runtime.initialize()
    return runtime


def test_execute_goal_end_to_end():
    runtime = build_runtime()
    try:
        results = runtime.execute_goal(Goal(name="integration_goal", description="verify the spine"))
        assert results, "goal execution must produce results"
        assert all(r.status == "success" for r in results), [r.status for r in results]
    finally:
        runtime.shutdown()


def test_execute_goal_stores_memories_and_emits_events():
    runtime = build_runtime()
    bus = runtime.container.event_bus
    memory = runtime.container.memory
    seen: list[str] = []
    bus.subscribe_all(lambda e: seen.append(e.type))
    try:
        runtime.execute_goal(Goal(name="observable_goal", description="check events and memory"))
        bus.flush()
        assert any(t.startswith("planner.") for t in seen), seen
        assert any(t.startswith("executor.") for t in seen), seen
        assert memory.episodic.episode_count >= 1
    finally:
        runtime.shutdown()


def test_compound_goal_decomposes_into_multiple_tasks():
    runtime = build_runtime()
    try:
        results = runtime.execute_goal(Goal(name="research the data and build the report"))
        assert len(results) >= 2, "compound goals must decompose into multiple tasks"
    finally:
        runtime.shutdown()


def test_event_bus_kwargs_and_object_styles_are_equivalent():
    bus = EventBus(auto_dispatch=True)
    bus.start()
    seen = []
    bus.subscribe("demo.type", lambda e: seen.append((e.type, e.payload)))
    bus.publish(Event(type="demo.type", payload={"n": 1}))
    bus.publish(type="demo.type", payload={"n": 2})
    assert seen == [("demo.type", {"n": 1}), ("demo.type", {"n": 2})]


def test_timestamps_are_timezone_aware():
    from ncp.core.entities import Entity
    from ncp.events.event import Event as Ev
    from ncp.graph.node import Node

    for obj in (Entity(), Ev(), Node()):
        ts = obj.created_at if hasattr(obj, "created_at") else obj.timestamp
        assert ts.tzinfo is not None, f"{type(obj).__name__} timestamp must be timezone-aware"
