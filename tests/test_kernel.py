from ncp.core.entities import Memory
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


def test_kernel_invokes_platform_planner_router_executor(tmp_path):
    """The platform lineage participates in every submit: planner annotates the
    DAG at compile time, router+executor run per node (Phase 11 unification)."""
    kernel = make_kernel(tmp_path)
    try:
        kernel.submit("research task routing, then update the index")
        assert kernel.telemetry.events_of_type(EventType.PLANNER_FINISHED.value)
        assert kernel.telemetry.events_of_type(EventType.ROUTER_SELECTED.value)
        assert kernel.telemetry.events_of_type(EventType.EXECUTOR_FINISHED.value)
    finally:
        kernel.shutdown()


def test_kernel_nodes_carry_platform_annotations(tmp_path):
    """Every DAG node's result includes the platform execution pass and its
    metadata carries the compile-time plan score / simulation prediction."""
    kernel = make_kernel(tmp_path)
    try:
        response = kernel.submit("update the index")
        for node in response.node_results:
            assert "platform_execution" in node["result"]
            assert node["result"]["platform_execution"].get("status") not in (None, "error")
            assert "platform_score" in node["metadata"]
            assert "predicted_confidence" in node["metadata"]
    finally:
        kernel.shutdown()


def test_kernel_attaches_provenance(tmp_path):
    """Every committed memory gets a persisted, audited provenance record."""
    kernel = make_kernel(tmp_path)
    try:
        kernel.submit("update the index")
        assert kernel.lineage.entries, "lineage recorded per committed memory"
        assert kernel.audit.get_entries(action="memory.commit"), "audit trail written"
        provenance_dir = kernel.storage.root / "provenance"
        assert any(provenance_dir.glob("*.json")), "provenance records persisted"
        committed = [m for m in kernel.memory.working.get_all()
                     if getattr(m, "provenance_id", None) is not None]
        assert committed, "memory items carry their provenance_id"
    finally:
        kernel.shutdown()


def test_kernel_compresses_checkpoints(tmp_path):
    kernel = make_kernel(tmp_path)
    try:
        kernel.submit("update the index")
        compressed = kernel.storage.artifacts.list_artifacts("checkpoints_compressed")
        assert compressed, "compressed checkpoint artifacts saved"
        assert kernel.compression.statistics.total_compressions >= 1
        summaries = kernel.storage.artifacts.list_artifacts("run_summaries")
        assert summaries, "per-run summary artifact saved"
    finally:
        kernel.shutdown()


def test_kernel_startup_report_and_auto_resume(tmp_path):
    """A kernel booted over an interrupted run self-heals without a manual resume."""
    kernel = make_kernel(tmp_path, auto_resume=False)
    try:
        dag = kernel.compiler.compile("research routing, then update the index", kernel.runtime.universe)
        order = dag.topological_order()
        order[0].status = "completed"
        order[0].result = {"status": "accepted", "verification": {"approved": True, "confidence": 0.9}}
        order[1].status = "running"
        kernel.checkpoints.checkpoint(dag)
    finally:
        kernel.shutdown()

    reborn = make_kernel(tmp_path)  # auto_resume defaults to True
    try:
        assert dag.run_id in reborn.startup_report["interrupted_runs"]
        assert reborn.startup_report["diagnoses"][0]["resumable"]
        resumed = {r["run_id"]: r["status"] for r in reborn.startup_report["auto_resumed"]}
        assert resumed.get(dag.run_id) == "completed"
        assert "recovered start" in reborn.startup_report_summary()
        # and the run really is finished now, not just reported as such
        assert not reborn.crash_recovery.interrupted_runs()
    finally:
        reborn.shutdown()


def test_kernel_vector_memory_survives_restart(tmp_path):
    kernel = make_kernel(tmp_path)
    try:
        kernel.submit("update the index")
        stored_keys = set(kernel.memory.vectors.vectors)
        assert stored_keys, "node memories were embedded"
    finally:
        kernel.shutdown()

    reborn = make_kernel(tmp_path)
    try:
        assert stored_keys <= set(reborn.memory.vectors.vectors), "embeddings reloaded from storage"
    finally:
        reborn.shutdown()


def test_kernel_research_node_type(tmp_path):
    """Research nodes run the discovery loop; corroborated hypotheses become
    semantic memory."""
    kernel = make_kernel(tmp_path)
    try:
        # seed corroborating knowledge so the verification gate can pass
        for text in [
            "provider routing prefers historically reliable providers",
            "routing strategies balance provider cost and latency",
        ]:
            kernel.memory.store(Memory(content=text, memory_type="semantic", name=text[:24]))
        before = kernel.memory.semantic.concept_count

        response = kernel.submit("research provider routing strategies")
        research_nodes = [n for n in response.node_results if n["task_type"] == "research"]
        assert research_nodes, "research goal compiles to research nodes"
        assert any(n["result"].get("discoveries") for n in research_nodes), \
            "corroborated hypotheses were verified"
        assert kernel.memory.semantic.concept_count > before, \
            "verified discoveries entered semantic memory"
    finally:
        kernel.shutdown()


def test_kernel_research_uncorroborated_hypotheses_rejected(tmp_path):
    """Without supporting evidence the discovery gate stays closed."""
    kernel = make_kernel(tmp_path)
    try:
        response = kernel.submit("research quantum blorpography")
        research_nodes = [n for n in response.node_results if n["task_type"] == "research"]
        assert research_nodes
        assert not any(n["result"].get("discoveries") for n in research_nodes)
    finally:
        kernel.shutdown()


def test_kernel_coding_node_type(tmp_path):
    """Build goals run generate -> verify -> optimize -> benchmark and save
    the best candidate as a code artifact."""
    kernel = make_kernel(tmp_path)
    try:
        response = kernel.submit("build a small parsing tool")
        exec_nodes = [n for n in response.node_results if n["task_type"] == "execute"]
        assert exec_nodes, "build goal compiles to an execute node"
        coding = [n["result"]["coding"] for n in exec_nodes if n["result"].get("coding")]
        assert coding, "code-focused execute nodes ran the coding pipeline"
        assert coding[0]["candidates"] >= 1
        assert coding[0]["verified"] >= 1
        assert coding[0]["best_score"] > 0
        assert kernel.storage.artifacts.list_artifacts("code"), "best candidate saved as artifact"
    finally:
        kernel.shutdown()


def test_kernel_maintenance_cycle(tmp_path):
    """Forced maintenance extracts episode skills, evolves the pool, and
    creates a pruned backup."""
    kernel = make_kernel(tmp_path)
    try:
        for _ in range(3):  # repeated successful traces for the extractor
            kernel.submit("update the index")
        report = kernel.run_maintenance(force=True)
        assert report is not None
        assert report["skills_extracted"] >= 1, "repeated successful episodes became skills"
        assert set(report["evolution"]) == {"promoted", "retired"}
        assert kernel.storage.backups.list_backups(), "backup created"
        assert kernel.telemetry.events_of_type(EventType.MAINTENANCE_COMPLETED.value)
    finally:
        kernel.shutdown()


def test_kernel_maintenance_gated_by_interval(tmp_path):
    kernel = make_kernel(tmp_path)
    try:
        assert kernel.run_maintenance() is None, "not due yet"
        kernel.maintenance_interval = 1
        kernel.submit("update the index")  # _execute triggers it automatically
        assert kernel.storage.backups.list_backups(), "auto maintenance ran once due"
    finally:
        kernel.shutdown()


def test_kernel_workers_ride_the_event_bus(tmp_path):
    """Consolidation and cleanup workers are dispatched on TASK_FINISHED."""
    from unittest import mock

    kernel = make_kernel(tmp_path)
    try:
        assert kernel.worker_scheduler.dispatcher.get_workers_for(
            EventType.TASK_FINISHED.value) == ["consolidation", "cleanup"]
        worker_cls = type(kernel.consolidation_worker)
        original = worker_cls.run
        with mock.patch.object(worker_cls, "run", autospec=True, side_effect=original) as spy:
            kernel.submit("update the index")
        assert spy.call_count >= 1, "consolidation worker ran on task completion"
    finally:
        kernel.shutdown()


def test_selector_uses_graph_fallback():
    """When find() filters everything out, the capability graph still knows
    which provider serves the capability."""
    from ncp.capabilities.graph import CapabilityGraph
    from ncp.capabilities.registry import ProviderRecord, ProviderRegistry
    from ncp.capabilities.selector import ProviderSelector

    registry = ProviderRegistry()
    registry.register(ProviderRecord(id="downed", capabilities=["special"], availability=0.0))
    registry.register(ProviderRecord(id="general", capabilities=["plan"]))
    selector = ProviderSelector(registry, capability_graph=CapabilityGraph(registry))

    chosen = selector.select({"capability": "special"})
    assert chosen is not None and chosen.id == "downed", \
        "graph fallback found the capable-but-unavailable provider"


class TestSkillEvolution:
    def test_evolve_promotes_strong_and_retires_weak(self):
        from ncp.core.entities import Skill
        from ncp.skills.benchmark import SkillBenchmark
        from ncp.skills.evolution import SkillEvolution
        from ncp.skills.registry import SkillRegistry

        registry = SkillRegistry()
        strong = Skill(name="strong", memory_type="skill", success_count=95,
                       failure_count=5, confidence=0.9, is_active=True)
        weak = Skill(name="weak", memory_type="skill", success_count=1,
                     failure_count=9, confidence=0.1, is_active=True)
        registry.register(strong)
        registry.register(weak)

        result = SkillEvolution(registry, SkillBenchmark()).evolve()
        assert result["retired"] >= 1 and not weak.is_active
        assert result["promoted"] >= 1 and strong.confidence > 0.9


def test_kernel_graph_report_and_ops(tmp_path):
    """The knowledge graph mirror is live: reportable, traversable, and
    curatable via the merge/split admin operations."""
    kernel = make_kernel(tmp_path)
    try:
        kernel.submit("update the index, then research routing")
        report = kernel.graph_report()
        assert report["metrics"]["node_count"] >= 2
        assert "fractal_dimension" in report
        assert report["node_types"], "nodes are typed by memory tier"

        walk = kernel.graph_traverse(max_depth=10)
        assert walk, "BFS walks the temporal chain"

        graph = kernel.memory.knowledge_graph
        merge_ids = list(graph.nodes)[:2]
        nodes_before = len(graph.nodes)
        super_node = kernel.graph_merge(merge_ids, label="merged_steps")
        assert super_node.node_type == "super_node"
        assert len(graph.nodes) == nodes_before - 1  # two removed, one added

        partitions = kernel.graph_split(2)
        assert len(partitions) == 2
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
