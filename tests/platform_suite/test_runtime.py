"""Tests for runtime module."""


from ncp.events.bus import EventBus
from ncp.runtime.container import Container
from ncp.runtime.lifecycle import LifecycleManager
from ncp.runtime.runtime import Runtime
from ncp.runtime.scheduler import Scheduler
from ncp.runtime.state import RuntimeState, RuntimeStatus
from ncp.utils.config import Config


class TestRuntimeState:
    def test_initial_state(self):
        state = RuntimeState()
        assert state.status == RuntimeStatus.INITIALIZING
        assert state.tasks_processed == 0

    def test_state_dict(self):
        state = RuntimeState(status=RuntimeStatus.RUNNING, tasks_processed=5)
        d = state.to_dict()
        assert d["status"] == "RUNNING"
        assert d["tasks_processed"] == 5


class TestContainer:
    def test_container_build(self):
        config = Config()
        config.set("events.queue_size", 100)
        config.set("scheduler.workers", 2)

        container = Container(config=config).build()
        assert container.event_bus is not None
        assert container.planner is not None
        assert container.router is not None
        assert container.executor is not None
        assert container.memory is not None
        assert container.storage is not None
        assert container.constraints is not None
        assert container.simulator is not None

    def test_container_get_runtime(self):
        config = Config()
        container = Container(config=config).build()
        runtime = container.get_runtime()
        assert isinstance(runtime, Runtime)


class TestScheduler:
    def test_scheduler_lifecycle(self):
        bus = EventBus(queue_size=10)
        scheduler = Scheduler(event_bus=bus, max_workers=4)

        scheduler.start()
        assert scheduler.is_running is True
        assert scheduler.is_paused is False

        scheduler.pause()
        assert scheduler.is_paused is True

        scheduler.resume()
        assert scheduler.is_paused is False

        scheduler.stop()
        assert scheduler.is_running is False

    def test_task_submission(self):
        bus = EventBus(queue_size=10)
        scheduler = Scheduler(event_bus=bus)
        from ncp.core.entities import Task

        scheduler.start()
        task = Task(name="test")
        scheduler.submit(task)
        assert scheduler.queue_size == 1
        scheduler.stop()


class TestLifecycleManager:
    def test_lifecycle(self):
        bus = EventBus(queue_size=10)
        lm = LifecycleManager(event_bus=bus)

        lm.startup()
        assert lm.state.status == RuntimeStatus.RUNNING

        snapshot = lm.snapshot()
        assert "status" in snapshot

        lm.shutdown()
        assert lm.state.status == RuntimeStatus.STOPPED


class TestExecuteGoalDelegatesToKernel:
    def test_container_builds_kernel_sharing_subsystems(self, tmp_path):
        from ncp.kernel.kernel import Kernel

        config = Config()
        config.set("storage.root", str(tmp_path / "storage"))
        container = Container(config=config).build()
        kernel = container.kernel
        assert isinstance(kernel, Kernel)
        # shared instances, not copies — the whole point of the unification
        assert kernel.events is container.event_bus
        assert kernel.memory is container.memory
        assert kernel.platform_planner is container.planner
        assert kernel.platform_router is container.router
        assert kernel.platform_executor is container.executor
        assert kernel.platform_constraints is container.constraints
        assert kernel.platform_simulator is container.simulator
        assert kernel.research_manager is container.research
        kernel.shutdown()

    def test_execute_goal_runs_through_kernel(self, tmp_path):
        from ncp.core.entities import Goal

        config = Config()
        config.set("storage.root", str(tmp_path / "storage"))
        container = Container(config=config).build()
        runtime = container.get_runtime()
        runtime.initialize()
        try:
            jobs_before = len(container.kernel.world.jobs)
            results = runtime.execute_goal(Goal(name="update the index", description="update the index"))
            assert len(container.kernel.world.jobs) == jobs_before + 1
            assert results, "kernel node results mapped back to platform Results"
            assert all(r.status in {"success", "partial", "failure"} for r in results)
        finally:
            runtime.shutdown()
            container.kernel.shutdown()


class TestRuntime:
    def test_runtime_initialization(self):
        config = Config()
        container = Container(config=config).build()
        runtime = Runtime(container=container)

        runtime.initialize()
        assert runtime.is_initialized is True

        runtime.shutdown()
        assert runtime.is_initialized is False

    def test_runtime_state(self):
        config = Config()
        container = Container(config=config).build()
        runtime = Runtime(container=container)

        runtime.initialize()
        assert runtime.state.status == RuntimeStatus.RUNNING
        runtime.shutdown()
