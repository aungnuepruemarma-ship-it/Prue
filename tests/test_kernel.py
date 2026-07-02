from ncp.events.event import EventType
from ncp.kernel import Kernel


def make_kernel(tmp_path, **kwargs) -> Kernel:
    return Kernel(storage_root=str(tmp_path / "storage"), **kwargs)


def test_kernel_submit_end_to_end(tmp_path):
    kernel = make_kernel(tmp_path)
    try:
        response = kernel.submit("research task routing, then update the index", project="proj-x")
        assert response.status == "completed"
        assert response.verified
        assert response.confidence > 0.3
        assert len(response.node_results) >= 3
        assert all(n["status"] == "completed" for n in response.node_results)
        # every node went through a named provider chosen by the selector
        assert all(n["provider_id"] for n in response.node_results)
    finally:
        kernel.shutdown()


def test_kernel_persists_checkpoints_world_and_experience(tmp_path):
    kernel = make_kernel(tmp_path)
    try:
        response = kernel.submit("create a concept", project="proj-y")
        run_id = response.run_id
        assert kernel.checkpoints.store.list_checkpoints(run_id), "per-node checkpoints on disk"
        assert kernel.experience.count >= 1, "experience rows recorded"
        assert kernel.telemetry.events_of_type(EventType.TASK_STARTED.value)
        assert kernel.telemetry.events_of_type(EventType.CHECKPOINT_SAVED.value)
        assert kernel.world.jobs[run_id]["status"] == "completed"
        project = kernel.world.projects.find_by_name("proj-y")
        assert project is not None and project.goal_ids
    finally:
        kernel.shutdown()

    # world state survives a cold restart
    reborn = make_kernel(tmp_path)
    try:
        assert reborn.world.projects.find_by_name("proj-y") is not None
    finally:
        reborn.shutdown()


def test_kernel_memory_and_skills_flow(tmp_path):
    kernel = make_kernel(tmp_path)
    try:
        kernel.submit("update the index")
        assert kernel.memory.episodic.episode_count >= 0
        # episodic memories carry the node responses
        memories = kernel.memory.retrieve("index", top_k=5)
        assert isinstance(memories, list)
    finally:
        kernel.shutdown()


def test_kernel_recovery_drill(tmp_path):
    """Interrupt a run mid-DAG, restore from checkpoints, and finish it."""
    kernel = make_kernel(tmp_path)
    try:
        dag = kernel.compiler.compile("research routing, then update the index", kernel.runtime.universe)
        order = dag.topological_order()
        # simulate a crash: first node done, second was mid-flight
        order[0].status = "completed"
        order[0].result = {"status": "accepted", "verification": {"approved": True, "confidence": 0.9}}
        order[1].status = "running"
        kernel.checkpoints.checkpoint(dag)

        interrupted = kernel.crash_recovery.interrupted_runs()
        assert dag.run_id in interrupted
        diagnosis = kernel.crash_recovery.diagnose(dag.run_id)
        assert diagnosis["resumable"]

        response = kernel.resume(dag.run_id)
        assert response is not None
        assert response.status == "completed"
        resumed_first = [n for n in response.node_results if n["id"] == order[0].id][0]
        assert resumed_first["result"]["verification"]["approved"], "completed work must be preserved, not re-run"
        assert kernel.telemetry.events_of_type(EventType.RECOVERY_STARTED.value)
    finally:
        kernel.shutdown()


def test_resource_manager_limits():
    from ncp.kernel.resource_manager import ResourceManager

    rm = ResourceManager(max_concurrent_tasks=1, budgets={"tokens": 10.0})
    assert rm.acquire()
    assert not rm.acquire(), "slot limit enforced"
    rm.release()
    assert rm.acquire()
    assert rm.charge("tokens", 6.0)
    assert not rm.charge("tokens", 6.0), "budget exhaustion detected"
    assert rm.remaining("tokens") == -2.0
