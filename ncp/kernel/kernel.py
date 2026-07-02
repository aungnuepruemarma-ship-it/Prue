"""The NCP kernel — the single entry point of the AI operating system.

    User -> Kernel -> Planner -> Scheduler -> Execution DAG
         -> Capability Providers -> Verifier -> Memory -> Response

Everything communicates through the kernel and its event bus; nothing
talks to a model directly. Providers are selected by constraints and
learned policy, every node output passes verification before commit,
every node is checkpointed for recovery, and every outcome feeds the
experience database.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ncp.coding import CodeBenchmark, CodeGenerator, CodeOptimizer, CodeVerifier
from ncp.compression.manager import CompressionManager
from ncp.constraints.solver import ConstraintSolver
from ncp.core.entities import Memory as MemoryEntity
from ncp.core.entities import Task as PlatformTask
from ncp.core.runtime import Runtime, build_default_universe
from ncp.events.bus import EventBus
from ncp.events.event import EventType
from ncp.events.priority import EventPriority
from ncp.events.publisher import EventPublisher
from ncp.execution.compiler import DAGCompiler
from ncp.execution.dag import ExecutionDAG
from ncp.execution.dag_executor import DAGExecutor
from ncp.execution.node import DAGNode
from ncp.graph.compression import GraphCompressor
from ncp.graph.expansion import expand_node
from ncp.graph.fractal import FractalAnalyzer
from ncp.graph.graph import Graph
from ncp.graph.hierarchy import GraphHierarchy
from ncp.graph.merge import merge_nodes
from ncp.graph.metrics import GraphMetrics
from ncp.graph.query import QueryEngine
from ncp.graph.split import split_by_clustering
from ncp.graph.traversal import TraversalEngine
from ncp.kernel.capability_registry import CapabilityGraph, ProviderSelector, build_default_registry
from ncp.kernel.resource_manager import ResourceManager
from ncp.learning.experience_db import ExperienceDB
from ncp.learning.planner_optimizer import PlannerOptimizer
from ncp.learning.reward_engine import RewardEngine
from ncp.learning.routing_optimizer import RoutingOptimizer
from ncp.learning.telemetry_engine import TelemetryEngine
from ncp.memory.manager import MemoryManager
from ncp.planner.planner import Planner as PlatformPlanner
from ncp.provenance import (
    AuditTrail,
    ConfidenceModel,
    Evidence,
    LineageTracker,
    ProvenanceRecord,
    Source,
)
from ncp.recovery.checkpoint_manager import CheckpointManager
from ncp.recovery.crash_recovery import CrashRecovery
from ncp.recovery.restore_manager import RestoreManager
from ncp.recovery.snapshot_manager import SnapshotManager
from ncp.research.manager import ResearchManager
from ncp.router.router import Router as PlatformRouter
from ncp.runtime.executor import Executor as PlatformExecutor
from ncp.simulator.simulator import Simulator
from ncp.skills.benchmark import SkillBenchmark
from ncp.skills.bridge import sync_library_to_registry
from ncp.skills.evolution import SkillEvolution
from ncp.skills.extractor import SkillExtractor as EpisodeSkillExtractor
from ncp.skills.library import SkillLibrary
from ncp.skills.registry import SkillRegistry
from ncp.storage.relational_store import RelationalStore
from ncp.storage.storage import Storage as PlatformStorage
from ncp.storage.storage_manager import StorageManager
from ncp.utils.config import Config as SystemConfig
from ncp.utils.runtime_config import RuntimeConfig
from ncp.verification.verifier import Verifier
from ncp.workers.cleanup import CleanupWorker
from ncp.workers.consolidation import ConsolidationWorker
from ncp.workers.scheduler import WorkerScheduler
from ncp.world.world_state import WorldState


@dataclass
class KernelResponse:
    run_id: str
    goal: str
    status: str  # completed, partial, failed
    response: str
    confidence: float
    node_results: list[dict[str, Any]] = field(default_factory=list)
    verified: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "goal": self.goal,
            "status": self.status,
            "response": self.response,
            "confidence": self.confidence,
            "node_results": self.node_results,
            "verified": self.verified,
        }


class Kernel:
    """Owns the full pipeline; `submit(goal)` is the one public entry point."""

    def __init__(
        self,
        storage_root: str = "storage",
        learning_enabled: bool = True,
        auto_resume: bool = True,
        event_bus: EventBus | None = None,
        memory: MemoryManager | None = None,
        planner: PlatformPlanner | None = None,
        router: PlatformRouter | None = None,
        constraints: ConstraintSolver | None = None,
        simulator: Simulator | None = None,
        research: ResearchManager | None = None,
        executor: PlatformExecutor | None = None,
    ):
        self.storage = StorageManager(storage_root)
        self.events = event_bus or EventBus(auto_dispatch=True)
        self.events.start()

        self.registry = build_default_registry()
        self.capability_graph = CapabilityGraph(self.registry)
        self.selector = ProviderSelector(self.registry, capability_graph=self.capability_graph)
        self.resources = ResourceManager()
        self.publisher = EventPublisher(self.events, source="kernel")

        # execution service: the reference runtime performs the actual
        # state transformations (activation -> Phi gate -> objective -> commit)
        self.runtime = Runtime(
            build_default_universe(),
            config=RuntimeConfig(output_dir=str(self.storage.root / "world_state" / "runtime")),
        )
        config = SystemConfig()
        self.memory = memory or MemoryManager(storage=PlatformStorage(config=config), event_bus=self.events, config=config)
        # the platform lineage participates in every node: its planner and
        # simulator annotate the DAG at compile time, its router/executor run
        # per node, and its constraint solver is a verification stage
        self.platform_constraints = constraints or ConstraintSolver(config=config)
        self.platform_router = router or PlatformRouter(memory=self.memory, event_bus=self.events, config=config)
        self.platform_simulator = simulator or Simulator(constraints=self.platform_constraints, config=config)
        self.platform_executor = executor or PlatformExecutor(router=self.platform_router, event_bus=self.events, config=config)
        self.platform_planner = planner or PlatformPlanner(
            router=self.platform_router,
            memory=self.memory,
            constraints=self.platform_constraints,
            simulator=self.platform_simulator,
            event_bus=self.events,
            config=config,
        )
        self.research_manager = research or ResearchManager(memory=self.memory, event_bus=self.events, config=config)

        self.compiler = DAGCompiler(platform_planner=self.platform_planner, platform_simulator=self.platform_simulator)
        self.verifier = Verifier(extra_stages={"platform_constraints": self._platform_constraint_stage})
        self.skill_registry = SkillRegistry()
        self.skill_library = SkillLibrary(self.skill_registry)
        # episode-based extraction is a second signal alongside the reference
        # runtime's bigram extractor; both feed the same registry
        self.skill_extractor = EpisodeSkillExtractor(self.skill_registry)
        self.skill_benchmark = SkillBenchmark()
        self.skill_evolution = SkillEvolution(self.skill_registry, self.skill_benchmark)

        # background workers ride the event bus: memory consolidation and
        # cleanup run automatically whenever a task finishes
        self.worker_scheduler = WorkerScheduler(event_bus=self.events)
        self.consolidation_worker = ConsolidationWorker(self.memory)
        self.cleanup_worker = CleanupWorker(self.memory)
        self.worker_scheduler.register_worker(
            "consolidation", lambda event: self.consolidation_worker.run(),
            [EventType.TASK_FINISHED.value],
        )
        self.worker_scheduler.register_worker(
            "cleanup", lambda event: self.cleanup_worker.run(),
            [EventType.TASK_FINISHED.value],
        )
        self.worker_scheduler.start_all()

        self.maintenance_interval = 10
        self._runs_since_maintenance = 0
        self.graph_compressor = GraphCompressor()

        # provenance: every committed memory carries an audited lineage record
        self.lineage = LineageTracker()
        self.audit = AuditTrail()
        self.compression = CompressionManager()

        # coding pipeline: build-focused execute nodes generate, verify,
        # optimize, and benchmark code candidates
        self.code_generator = CodeGenerator()
        self.code_verifier = CodeVerifier()
        self.code_optimizer = CodeOptimizer()
        self.code_benchmark = CodeBenchmark()

        # vector memory survives restarts via the storage vectors/ slot
        persisted_vectors = self.storage.load_document("vectors", "memory_embeddings")
        if persisted_vectors:
            self.memory.vectors.vectors.update(persisted_vectors.get("vectors", {}))
            self.memory.vector_texts.update(persisted_vectors.get("texts", {}))

        self.world = WorldState(storage=self.storage)
        self.world.load()

        telemetry_store = RelationalStore(str(self.storage.root / "telemetry" / "telemetry.db"))
        self.telemetry = TelemetryEngine(telemetry_store)
        self.telemetry.attach(self.events)
        self.experience = ExperienceDB(telemetry_store)
        self.rewards = RewardEngine()
        self.routing_optimizer = RoutingOptimizer(self.experience)
        self.planner_optimizer = PlannerOptimizer(self.experience)
        self.learning_enabled = learning_enabled
        if learning_enabled:
            self.routing_optimizer.refresh()
            self.selector.policy = self.routing_optimizer.learned_policy

        self.checkpoints = CheckpointManager(self.storage.checkpoints)
        self.snapshots = SnapshotManager(self.storage)
        self.crash_recovery = CrashRecovery(self.checkpoints)
        self.restore_manager = RestoreManager(self.checkpoints)

        # crash recovery is automatic: diagnose interrupted runs on boot and,
        # unless told otherwise, finish them before accepting new work
        interrupted = self.crash_recovery.interrupted_runs()
        self.startup_report: dict[str, Any] = {
            "interrupted_runs": list(interrupted),
            "diagnoses": [self.crash_recovery.diagnose(run_id) for run_id in interrupted],
            "auto_resumed": [],
        }
        if auto_resume:
            for run_id in interrupted:
                response = self.resume(run_id)
                if response is not None:
                    self.startup_report["auto_resumed"].append(
                        {"run_id": run_id, "status": response.status}
                    )

    def startup_report_summary(self) -> str:
        report = self.startup_report
        if not report["interrupted_runs"]:
            return "clean start: no interrupted runs"
        resumed = ", ".join(f"{r['run_id']}={r['status']}" for r in report["auto_resumed"]) or "none"
        return (
            f"recovered start: {len(report['interrupted_runs'])} interrupted run(s), "
            f"auto-resumed: {resumed}"
        )

    # -- pipeline ----------------------------------------------------------
    def submit(self, goal: str, project: str | None = None) -> KernelResponse:
        dag = self.compiler.compile(goal, self.runtime.universe)
        return self._execute(dag, goal, project)

    def resume(self, run_id: str) -> KernelResponse | None:
        """Restart -> load snapshot -> restore state -> continue."""
        restored = self.restore_manager.restore_run(run_id)
        if restored is None:
            return None
        dag, _variables = restored
        self.publisher.publish(EventType.RECOVERY_STARTED, {"run_id": run_id}, priority=EventPriority.HIGH)
        response = self._execute(dag, dag.goal, project=None)
        self.publisher.publish(EventType.RECOVERY_COMPLETED, {"run_id": run_id})
        return response

    def _execute(self, dag: ExecutionDAG, goal: str, project: str | None) -> KernelResponse:
        goal_record = self.world.goals.add(goal)
        if project:
            record = self.world.projects.find_by_name(project) or self.world.projects.create(project)
            self.world.projects.attach_goal(record.id, goal_record.id)
            goal_record.project_id = record.id
        self.world.goals.attach_run(goal_record.id, dag.run_id)
        self.world.goals.set_status(goal_record.id, "active")
        self.world.start_job(dag.run_id, goal)
        self.world.session.record_run(dag.run_id)
        self.publisher.publish(EventType.TASK_STARTED, {"run_id": dag.run_id, "goal": goal})

        executor = DAGExecutor(node_runner=self._run_node, checkpoint_hook=self._checkpoint)
        executor.run(dag)

        status = "completed" if dag.succeeded else ("partial" if any(n.status == "completed" for n in dag.nodes.values()) else "failed")
        self.world.goals.set_status(goal_record.id, "completed" if status == "completed" else "failed")
        self.world.finish_job(dag.run_id, status)
        self.world.observe_universe(self.runtime.universe)
        self.world.save()
        self._learn_plan(dag)
        self.publisher.publish(
            EventType.TASK_FINISHED if status == "completed" else EventType.TASK_FAILED,
            {"run_id": dag.run_id, "status": status},
            priority=EventPriority.NORMAL if status == "completed" else EventPriority.HIGH,
        )
        self._runs_since_maintenance += 1
        self.run_maintenance()

        # the run summary is a durable artifact of the run
        self.storage.artifacts.save(
            f"{dag.run_id}_summary.txt", self._summarize(dag), category="run_summaries",
        )

        node_results = [n.to_dict() for n in dag.topological_order()]
        confidences = [n.result.get("verification", {}).get("confidence", 0.0) for n in dag.nodes.values()]
        return KernelResponse(
            run_id=dag.run_id,
            goal=goal,
            status=status,
            response=self._summarize(dag),
            confidence=min(confidences) if confidences else 0.0,
            node_results=node_results,
            verified=all(n.result.get("verification", {}).get("approved", False) for n in dag.nodes.values() if n.status == "completed"),
        )

    # -- node execution ----------------------------------------------------
    def _run_node(self, node: DAGNode) -> dict[str, Any]:
        # provider selection is cached per task type; the cache is cleared
        # whenever learning refreshes the routing policy
        cache_key = f"provider:{node.task_type}"
        provider = self.registry.get(self.storage.cache.get(cache_key) or "")
        if provider is None:
            provider = self.selector.select({"capability": node.task_type, "task_type": node.task_type})
            if provider is not None:
                self.storage.cache.set(cache_key, provider.id)
        node.provider_id = provider.id if provider else ""
        # a matching library skill is a reuse hint for the executing runtime
        known_skill = self.skill_library.find_skill(node.name)
        self.resources.acquire()
        try:
            result = self.runtime.step(node.goal, reasoner=provider.backend if provider else None)
            output: dict[str, Any] = {
                "status": result.status,
                "chosen": result.chosen,
                "explanation": result.explanation,
                "response": f"[{node.name}] {result.explanation} -> {result.chosen['name'] if result.chosen else 'no action'}",
                "entity_count": result.summary.get("entity_count"),
                "relation_count": result.summary.get("relation_count"),
                "confidence": 0.9 if result.status == "accepted" else 0.2,
            }
            if known_skill is not None:
                output["skill_hint"] = {
                    "name": known_skill.name,
                    "score": self.skill_benchmark.score(known_skill),
                }
        finally:
            self.resources.release()

        # retrieval augmentation: related memories (keyword + vector search)
        # ride along with the node output
        related = self.memory.retrieve(node.goal, top_k=3)
        output["related_memories"] = [m.content for m in related]

        # research nodes run the discovery loop (hypothesis -> verify ->
        # semantic memory); build-focused execute nodes run the coding pipeline
        if node.task_type == "research":
            evidence = output["related_memories"] + [
                f"{key}={value}" for key, value in list(self.world.facts.items())[:3]
            ]
            discoveries = self.research_manager.discover({
                "observation": node.goal,
                "evidence": evidence,
            })
            output["discoveries"] = [d.statement for d in discoveries]
        if node.task_type == "execute" and node.metadata.get("focus") == "code":
            output["coding"] = self._run_coding_pipeline(node)

        # platform-lineage pass: route + execute the node as a platform Task
        # (additive observability; must never change output["status"])
        task = PlatformTask(
            name=node.name,
            capability_required=node.task_type,
            inputs={"goal": node.goal},
            estimated_cost=node.metadata.get("predicted_cost_ms", 100.0) / 1000.0,
        )
        try:
            platform_result = self.platform_executor.execute(task)
            output["platform_execution"] = platform_result.to_dict()
        except Exception as exc:
            output["platform_execution"] = {"status": "error", "error": str(exc)}

        report = self.verifier.verify(output, context={"world_facts": self.world.facts, "task": task})
        output["verification"] = report.to_dict()
        self.publisher.publish(
            EventType.VERIFICATION_PASSED if report.approved else EventType.VERIFICATION_FAILED,
            {"node": node.name, "violations": report.violations},
            priority=EventPriority.NORMAL if report.approved else EventPriority.HIGH,
        )
        if report.approved:
            self._commit_memory(node, output)
        self._learn_node(node, output, report)
        # node-output scratch: raw outputs live in the object store so
        # reporting can read them back without re-walking the DAG
        self.storage.objects.store(node.id, json.dumps(output, default=str).encode("utf-8"))
        return output

    def _run_coding_pipeline(self, node: DAGNode) -> dict[str, Any]:
        """Generate -> verify -> optimize -> benchmark; best code becomes an artifact."""
        candidates = self.code_generator.generate_alternatives(node.goal)
        verified = self.code_verifier.verify_all(candidates)
        summary: dict[str, Any] = {
            "candidates": len(candidates),
            "verified": len(verified),
            "best_score": 0.0,
        }
        if not verified:
            return summary
        optimized = [self.code_optimizer.optimize(candidate) for candidate in verified]
        results = self.code_benchmark.compare(optimized)
        best = max(results, key=lambda r: r.score)
        best_candidate = next(c for c in optimized if str(c.id) == best.candidate_id)
        artifact = self.storage.artifacts.save(f"{node.id}.py", best_candidate.code, category="code")
        summary.update({
            "best_score": best.score,
            "best_time_ms": best.execution_time_ms,
            "artifact": str(artifact),
        })
        return summary

    def _platform_constraint_stage(self, output: dict[str, Any], context: dict[str, Any]) -> list[str]:
        task = context.get("task")
        if task is None or self.platform_constraints.validate(task):
            return []
        return [f"platform_constraint:{self.platform_constraints.explain(task)}"]

    def _commit_memory(self, node: DAGNode, output: dict[str, Any]) -> None:
        confidence = output.get("verification", {}).get("confidence", 0.5)
        record = ProvenanceRecord(
            source=Source(type="system", identifier=node.provider_id or "kernel", context=node.goal),
            confidence=ConfidenceModel(base_confidence=confidence, verification_count=1),
        )
        record.add_evidence(Evidence(
            type="observation",
            data=output.get("response", ""),
            confidence=confidence,
            metadata={"node_id": node.id, "task_type": node.task_type},
        ))
        record.lineage = self.lineage.record(record.id, operation="created", description=f"node {node.name}")
        self.audit.log(
            action="memory.commit",
            actor="kernel",
            target=node.name,
            details={"provenance_id": str(record.id), "node_id": node.id},
            result="approved",
        )
        self.storage.save_document("provenance", str(record.id), record.to_dict())
        self.memory.store(MemoryEntity(
            name=f"step:{node.name}",
            content=output.get("response", ""),
            memory_type="episodic",
            confidence=confidence,
            tags=[node.task_type],
            provenance_id=record.id,
        ))
        newly = sync_library_to_registry(self.runtime.skills, self.skill_registry)
        if newly:
            self.publisher.publish(EventType.SKILL_PROMOTED, {"count": newly})

    def _checkpoint(self, dag: ExecutionDAG) -> None:
        checkpoint_id = self.checkpoints.checkpoint(dag, variables={"goal": dag.goal})
        # a compressed copy of the DAG lands in the artifact store; the
        # primary (uncompressed) checkpoint/restore path is untouched
        compressed = self.compression.compress(dag.to_dict())
        self.storage.artifacts.save(
            f"{dag.run_id}_{checkpoint_id}.json",
            json.dumps(compressed, default=str),
            category="checkpoints_compressed",
        )
        self.publisher.publish(
            EventType.CHECKPOINT_SAVED,
            {"run_id": dag.run_id, "checkpoint_id": checkpoint_id},
            priority=EventPriority.LOW,
        )

    # -- learning ----------------------------------------------------------
    def _learn_node(self, node: DAGNode, output: dict[str, Any], report) -> None:
        reward = self.rewards.compute(output, output.get("verification"))
        self.experience.record(
            run_id="",  # per-node rows are aggregated by provider/task
            goal=node.goal,
            task_type=node.task_type,
            provider_id=node.provider_id,
            success=output.get("status") in {"success", "accepted"} and report.approved,
            reward=reward,
            confidence=report.confidence,
        )
        self.registry.record_outcome(node.provider_id, output.get("status") == "accepted")
        if self.learning_enabled:
            self.routing_optimizer.refresh()
            # the routing policy may have shifted: cached selections are stale
            self.storage.cache.clear()

    def _learn_plan(self, dag: ExecutionDAG) -> None:
        nodes = list(dag.nodes.values())
        if not nodes:
            return
        success_rate = sum(1 for n in nodes if n.status == "completed") / len(nodes)
        self.planner_optimizer.record_plan(len(nodes), success_rate)

    # -- maintenance -------------------------------------------------------
    def run_maintenance(self, force: bool = False) -> dict[str, Any] | None:
        """Periodic upkeep: extract skills from episodes, evolve the skill
        pool, and back up storage. Runs every ``maintenance_interval`` runs
        (or immediately with ``force=True``)."""
        if not force and self._runs_since_maintenance < self.maintenance_interval:
            return None
        self._runs_since_maintenance = 0
        extracted = self.skill_extractor.extract_from_episodes(self.memory.episodic)
        evolution = self.skill_evolution.evolve()
        # curate the knowledge graph: keep a compressed copy in the graph
        # store (compress() works in place, so it gets its own deep copy)
        import copy

        graph = self.memory.knowledge_graph
        compressed = self.graph_compressor.compress(copy.deepcopy(graph))
        self.storage.graph.save_graph("knowledge_compressed", compressed)
        backup = self.storage.backups.create_backup(label="maintenance")
        pruned = self.storage.backups.prune()
        report = {
            "skills_extracted": len(extracted),
            "evolution": evolution,
            "graph": {"nodes": len(graph.nodes), "compressed_nodes": len(compressed.nodes)},
            "backup": backup.name,
            "backups_pruned": pruned,
        }
        self.publisher.publish(EventType.MAINTENANCE_COMPLETED, report, priority=EventPriority.LOW)
        return report

    # -- knowledge graph operations ----------------------------------------
    def graph_report(self) -> dict[str, Any]:
        """Structural report over the live knowledge graph: quality metrics,
        fractal dimension, and node-type census."""
        graph = self.memory.knowledge_graph
        hierarchy = GraphHierarchy()
        hierarchy.add_graph(graph)
        analyzer = FractalAnalyzer(hierarchy)
        query = QueryEngine(graph)
        node_types = sorted({n.node_type for n in graph.nodes.values()})
        return {
            "metrics": GraphMetrics.compute(graph).to_dict(),
            "fractal_dimension": analyzer.compute_fractal_dimension(graph),
            "node_types": {t: len(query.get_nodes_by_type(t)) for t in node_types},
        }

    def graph_traverse(self, start_label: str | None = None, max_depth: int = 5) -> list[str]:
        """BFS over the knowledge graph from a labelled node (or the oldest)."""
        graph = self.memory.knowledge_graph
        if not graph.nodes:
            return []
        start_id = None
        if start_label is not None:
            start_id = self.memory.graph_index.lookup_by_label(start_label)
        if start_id is None:
            start_id = next(iter(graph.nodes))
        engine = TraversalEngine(graph, self.memory.graph_index)
        return [graph.nodes[nid].label for nid in engine.bfs(start_id, max_depth=max_depth)]

    def graph_merge(self, node_ids: list, label: str = ""):
        """Admin operation: collapse the given nodes into one super-node."""
        return merge_nodes(self.memory.knowledge_graph, node_ids, label)

    def graph_split(self, num_partitions: int = 2) -> list[Graph]:
        """Admin operation: partition the knowledge graph into subgraphs."""
        return split_by_clustering(self.memory.knowledge_graph, num_partitions)

    def graph_expand(self, node_id, expansion: Graph) -> None:
        """Admin operation: expand an abstract node into a detailed subgraph."""
        expand_node(self.memory.knowledge_graph, node_id, expansion)

    # -- reporting ---------------------------------------------------------
    def _summarize(self, dag: ExecutionDAG) -> str:
        lines = [f"run {dag.run_id}: {dag.goal}"]
        for node in dag.topological_order():
            result = node.result
            scratch = self.storage.objects.retrieve(node.id)
            if scratch:
                result = json.loads(scratch.decode("utf-8"))
            chosen = result.get("chosen") or {}
            lines.append(f"  - {node.name} [{node.status}] via {node.provider_id}: {chosen.get('name', result.get('error', ''))}")
        return "\n".join(lines)

    def snapshot(self, name: str = "kernel") -> str:
        return self.snapshots.snapshot(name, {
            "universe": self.runtime.universe.snapshot("kernel"),
            "world": self.world.to_dict(),
            "registry": self.registry.to_dict(),
        })

    def stats(self) -> dict[str, Any]:
        return {
            "storage": self.storage.stats(),
            "events": self.telemetry.total_events,
            "experience_episodes": self.experience.count,
            "providers": sorted(self.registry.providers),
            "skills": len(self.skill_registry.skills),
            "world_jobs": len(self.world.jobs),
        }

    def shutdown(self) -> None:
        self.world.save()
        self.storage.save_document("vectors", "memory_embeddings", {
            "vectors": self.memory.vectors.vectors,
            "texts": self.memory.vector_texts,
        })
        self.events.stop()
