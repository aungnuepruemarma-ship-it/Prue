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

from dataclasses import dataclass, field
from typing import Any

from ncp.core.entities import Memory as MemoryEntity
from ncp.core.runtime import Runtime, build_default_universe
from ncp.events.bus import EventBus
from ncp.events.event import EventType
from ncp.execution.compiler import DAGCompiler
from ncp.execution.dag import ExecutionDAG
from ncp.execution.dag_executor import DAGExecutor
from ncp.execution.node import DAGNode
from ncp.kernel.capability_registry import ProviderSelector, build_default_registry
from ncp.kernel.resource_manager import ResourceManager
from ncp.learning.experience_db import ExperienceDB
from ncp.learning.planner_optimizer import PlannerOptimizer
from ncp.learning.reward_engine import RewardEngine
from ncp.learning.routing_optimizer import RoutingOptimizer
from ncp.learning.telemetry_engine import TelemetryEngine
from ncp.memory.manager import MemoryManager
from ncp.recovery.checkpoint_manager import CheckpointManager
from ncp.recovery.crash_recovery import CrashRecovery
from ncp.recovery.restore_manager import RestoreManager
from ncp.recovery.snapshot_manager import SnapshotManager
from ncp.skills.bridge import sync_library_to_registry
from ncp.skills.registry import SkillRegistry
from ncp.storage.relational_store import RelationalStore
from ncp.storage.storage import Storage as PlatformStorage
from ncp.storage.storage_manager import StorageManager
from ncp.utils.config import Config as SystemConfig
from ncp.utils.runtime_config import RuntimeConfig
from ncp.verification.verifier import Verifier
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

    def __init__(self, storage_root: str = "storage", learning_enabled: bool = True):
        self.storage = StorageManager(storage_root)
        self.events = EventBus(auto_dispatch=True)
        self.events.start()

        self.registry = build_default_registry()
        self.selector = ProviderSelector(self.registry)
        self.resources = ResourceManager()

        self.compiler = DAGCompiler()
        self.verifier = Verifier()

        # execution service: the reference runtime performs the actual
        # state transformations (activation -> Phi gate -> objective -> commit)
        self.runtime = Runtime(
            build_default_universe(),
            config=RuntimeConfig(output_dir=str(self.storage.root / "world_state" / "runtime")),
        )
        self.memory = MemoryManager(storage=PlatformStorage(config=SystemConfig()), event_bus=self.events, config=SystemConfig())
        self.skill_registry = SkillRegistry()

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
        self.events.publish(type=EventType.RECOVERY_STARTED.value, payload={"run_id": run_id}, source="kernel")
        response = self._execute(dag, dag.goal, project=None)
        self.events.publish(type=EventType.RECOVERY_COMPLETED.value, payload={"run_id": run_id}, source="kernel")
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
        self.events.publish(type=EventType.TASK_STARTED.value, payload={"run_id": dag.run_id, "goal": goal}, source="kernel")

        executor = DAGExecutor(node_runner=self._run_node, checkpoint_hook=self._checkpoint)
        executor.run(dag)

        status = "completed" if dag.succeeded else ("partial" if any(n.status == "completed" for n in dag.nodes.values()) else "failed")
        self.world.goals.set_status(goal_record.id, "completed" if status == "completed" else "failed")
        self.world.finish_job(dag.run_id, status)
        self.world.observe_universe(self.runtime.universe)
        self.world.save()
        self._learn_plan(dag)
        self.events.publish(
            type=(EventType.TASK_FINISHED if status == "completed" else EventType.TASK_FAILED).value,
            payload={"run_id": dag.run_id, "status": status},
            source="kernel",
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
        provider = self.selector.select({"capability": node.task_type, "task_type": node.task_type})
        node.provider_id = provider.id if provider else ""
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
        finally:
            self.resources.release()

        report = self.verifier.verify(output, context={"world_facts": self.world.facts})
        output["verification"] = report.to_dict()
        self.events.publish(
            type=(EventType.VERIFICATION_PASSED if report.approved else EventType.VERIFICATION_FAILED).value,
            payload={"node": node.name, "violations": report.violations},
            source="kernel",
        )
        if report.approved:
            self._commit_memory(node, output)
        self._learn_node(node, output, report)
        return output

    def _commit_memory(self, node: DAGNode, output: dict[str, Any]) -> None:
        self.memory.store(MemoryEntity(
            name=f"step:{node.name}",
            content=output.get("response", ""),
            memory_type="episodic",
            confidence=output.get("verification", {}).get("confidence", 0.5),
            tags=[node.task_type],
        ))
        newly = sync_library_to_registry(self.runtime.skills, self.skill_registry)
        if newly:
            self.events.publish(type=EventType.SKILL_PROMOTED.value, payload={"count": newly}, source="kernel")

    def _checkpoint(self, dag: ExecutionDAG) -> None:
        checkpoint_id = self.checkpoints.checkpoint(dag, variables={"goal": dag.goal})
        self.events.publish(
            type=EventType.CHECKPOINT_SAVED.value,
            payload={"run_id": dag.run_id, "checkpoint_id": checkpoint_id},
            source="kernel",
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

    def _learn_plan(self, dag: ExecutionDAG) -> None:
        nodes = list(dag.nodes.values())
        if not nodes:
            return
        success_rate = sum(1 for n in nodes if n.status == "completed") / len(nodes)
        self.planner_optimizer.record_plan(len(nodes), success_rate)

    # -- reporting ---------------------------------------------------------
    def _summarize(self, dag: ExecutionDAG) -> str:
        lines = [f"run {dag.run_id}: {dag.goal}"]
        for node in dag.topological_order():
            chosen = node.result.get("chosen") or {}
            lines.append(f"  - {node.name} [{node.status}] via {node.provider_id}: {chosen.get('name', node.result.get('error', ''))}")
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
        self.events.stop()
