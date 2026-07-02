"""Call-reachability regression guard (Phase 11).

`tests/test_connectivity.py` proves every module is non-empty and importable
from the entry points; this suite proves the stronger property that the
previously-dead methods are *called* by a live Kernel path. Each target is
patched with ``autospec=True, side_effect=original`` — real behavior is
preserved, the mock only counts invocations — then one full Kernel lifecycle
runs and every target must have been hit at least once.

Rows are added chunk by chunk as Phase 11 wires each package in.
"""

from __future__ import annotations

import importlib
from unittest import mock

import pytest

# (module, class, method) triples that were dead before Phase 11.
TARGETS = [
    # Chunk 1 — platform lineage wired into the Kernel pipeline
    ("ncp.planner.planner", "Planner", "plan"),
    ("ncp.planner.decomposition", "Decomposer", "decompose"),
    ("ncp.router.router", "Router", "route"),
    ("ncp.runtime.executor", "Executor", "execute"),
    ("ncp.constraints.solver", "ConstraintSolver", "validate"),
    ("ncp.simulator.simulator", "Simulator", "simulate"),
    # Chunk 2 — provenance, compression, recovery, storage sub-stores, vectors
    ("ncp.provenance.lineage", "LineageTracker", "record"),
    ("ncp.provenance.audit", "AuditTrail", "log"),
    ("ncp.compression.manager", "CompressionManager", "compress"),
    ("ncp.recovery.crash_recovery", "CrashRecovery", "interrupted_runs"),
    ("ncp.storage.vector_store", "VectorStore", "store_embedding"),
    ("ncp.storage.vector_store", "VectorStore", "search"),
    ("ncp.storage.artifact_store", "ArtifactStore", "save"),
    ("ncp.storage.object_store", "ObjectStore", "store"),
    ("ncp.storage.cache", "CacheStore", "set"),
    ("ncp.memory.manager", "MemoryManager", "retrieve"),
    # Chunk 3 — research and coding node types
    ("ncp.research.manager", "ResearchManager", "discover"),
    ("ncp.research.discovery", "DiscoveryEngine", "discover"),
    ("ncp.research.verification", "VerificationEngine", "verify"),
    ("ncp.coding.generator", "CodeGenerator", "generate_alternatives"),
    ("ncp.coding.verifier", "CodeVerifier", "verify_all"),
    ("ncp.coding.optimizer", "CodeOptimizer", "optimize"),
    ("ncp.coding.benchmark", "CodeBenchmark", "compare"),
    # Chunk 4 — skills, workers, event publisher/dispatcher, capability graph
    ("ncp.events.publisher", "EventPublisher", "publish"),
    ("ncp.events.dispatcher", "EventDispatcher", "register_worker"),
    ("ncp.workers.scheduler", "WorkerScheduler", "register_worker"),
    ("ncp.workers.consolidation", "ConsolidationWorker", "run"),
    ("ncp.workers.cleanup", "CleanupWorker", "run"),
    ("ncp.skills.library", "SkillLibrary", "find_skill"),
    ("ncp.skills.extractor", "SkillExtractor", "extract_from_episodes"),
    ("ncp.skills.evolution", "SkillEvolution", "evolve"),
    ("ncp.capabilities.graph", "CapabilityGraph", "rebuild"),
    ("ncp.storage.backup_manager", "BackupManager", "create_backup"),
]

GOAL = "research task routing, then build a helper and update the index"


@pytest.fixture(scope="module")
def call_counts(tmp_path_factory):
    """Run one full Kernel lifecycle with every target instrumented."""
    from ncp.kernel import Kernel

    patchers = []
    spies: dict[tuple[str, str, str], mock.Mock] = {}
    for module_name, cls_name, method_name in TARGETS:
        cls = getattr(importlib.import_module(module_name), cls_name)
        original = getattr(cls, method_name)
        patcher = mock.patch.object(cls, method_name, autospec=True, side_effect=original)
        spies[(module_name, cls_name, method_name)] = patcher.start()
        patchers.append(patcher)
    try:
        kernel = Kernel(storage_root=str(tmp_path_factory.mktemp("reachability") / "storage"))
        try:
            response = kernel.submit(GOAL)
            assert response.status == "completed", "lifecycle run must itself succeed"
            kernel.run_maintenance(force=True)
        finally:
            kernel.shutdown()
        return {key: spy.call_count for key, spy in spies.items()}
    finally:
        for patcher in patchers:
            patcher.stop()


@pytest.mark.parametrize(("module_name", "cls_name", "method_name"), TARGETS)
def test_method_reached_from_kernel(call_counts, module_name, cls_name, method_name):
    count = call_counts[(module_name, cls_name, method_name)]
    assert count >= 1, (
        f"{module_name}.{cls_name}.{method_name} was never called during a "
        f"full Kernel lifecycle — a Phase 11 wire has been disconnected"
    )
