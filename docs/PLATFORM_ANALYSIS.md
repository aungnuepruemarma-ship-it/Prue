# Platform Analysis: the Kimi NCP Monorepo, its Review Report, and the Merge

*Analysis of the uploaded "Neural Capability Platform" monorepo and `REVIEW_REPORT.md`, the revisions applied, and how both codebases were unified. Companion to `ANALYSIS.md` (which covers the original reference runtime).*

## 1. What was uploaded

A parallel NCP implementation (~8,000 LOC, 157 Python files, 24 modules): interface-driven design (10 ABCs), event bus, DI container/runtime/scheduler/lifecycle, 7-tier memory (working/session/episodic/semantic/procedural/skill/archive), a 14-file knowledge-graph package (incl. a real box-counting fractal-dimension analyzer), compression, provenance, multi-store persistence, skills evolution, a research loop, coding tools, CLI + FastAPI server — plus its own review report claiming 144/144 tests passing.

## 2. Analysis findings

**The review report is accurate but incomplete.** We reproduced the 144/144 test result exactly (0.31s, only pyyaml needed). But the tests are shallow unit tests that never call `Runtime.execute_goal` — and that path was **broken**:

- **Blocker: EventBus API mismatch.** Thirteen call sites (planner ×3, router, executor ×3, memory manager ×3, …) called `event_bus.publish(type=..., payload=...)` against a signature accepting only a prebuilt `Event`. The first thing `execute_goal` does is publish a planner event, so **the demo crashed with `TypeError` before executing a single task** — and the failure handler crashed the same way. The report's "bug fixes applied" only fixed the two call sites in `lifecycle.py`, which is precisely why lifecycle tests passed while the goal path never could.
- **Declared vs real dependencies.** 12 required deps declared (numpy, networkx, httpx, structlog, rich, click, …); only three third-party imports actually exist in the code (`fastapi`/`pydantic` in one file, `yaml` in one file). `networkx` was declared while the whole graph package is hand-rolled.
- **Island modules.** Vector/graph/object stores, graph fractal/merge/split/expansion/compression, skill evolution, coding benchmark, provenance dependency/version were importable but exported by nothing and unreachable from any entry point. `coding/`, `provenance/`, `compression/`, `workers/` were never touched by the runtime. The scheduler queued tasks nothing dequeued; the simulator was injected but never called; the executor returned canned success strings.
- **33 `datetime.utcnow()` call sites** (deprecated in 3.12), one via a gratuitous `__import__("datetime")`.
- **Placeholders**: `security/`, `monitoring/`, `distributed/`, `adapters/` were single-docstring modules.

**Verdict:** a well-organized, uniformly-styled architectural scaffold with genuinely good bones (interfaces, events, DI, memory taxonomy) whose end-to-end path had never actually run.

## 3. Revisions applied

| Issue | Fix |
|---|---|
| EventBus kwargs mismatch (13 sites) | `publish()` accepts both an `Event` and keyword fields; goal path now runs end-to-end (`python -m ncp.cli.main --demo`) |
| No integration tests | `tests/platform_suite/test_integration.py` pins goal → planner → router → executor → memory, event emission, compound-goal decomposition |
| `datetime.utcnow()` ×33 | shared timezone-aware `utils.timeutils.utcnow()`; a test asserts all timestamps are aware |
| Dead dependencies | required deps trimmed to **zero**; `[api]` extra (fastapi/uvicorn, import-guarded), `[config]` extra (pyyaml, JSON fallback) |
| Island modules | all exported through package `__init__`s and reachable from entry points (enforced by the connectivity test) |
| Placeholders | filled by the reference implementations (Diagnostics → monitoring, Cluster → distributed, ExternalAdapter → adapters) plus a new `SecurityPolicy` consumed by the verification pipeline |
| utils → core import cycle | serializer's `Entity` import deferred |

## 4. Merge decisions (deep merge into one `ncp` package)

| Collision | Resolution |
|---|---|
| two `Runtime`s | reference `ncp.core.runtime.Runtime` (state-transforming loop) + platform `ncp.runtime.runtime.Runtime` (exported as `PlatformRuntime`); the kernel composes both |
| two `Graph`s | platform UUID-keyed knowledge graph keeps `graph/graph.py`; reference string-keyed view is `graph/simple.py::SimpleGraph` (backs `MemoryGraph`) |
| two `Config`s | platform YAML/env loader keeps `utils/config.py` (`SystemConfig`); reference limits dataclass is `utils/runtime_config.py::RuntimeConfig` |
| two `Entity` families | platform hierarchy (Goal→Task→Memory→Skill→Tool→Result) lands as `core/entities.py`; operational `Entity`/`Universe` stay in `core/entity.py`/`core/universe.py` |
| two skill systems | learned bigram skills sync into the platform `SkillRegistry` via `skills/bridge.py` |
| two test suites | unified under `tests/` (platform suite in `tests/platform_suite/`), 219 tests total |

## 5. Phases 6–10 (the AI-OS layer)

Built on the merged core exactly per the phase spec, stdlib-backed (sqlite3 / files / in-process vectors) with pluggable backends for real services:

- **Phase 6** `storage/`: `StorageManager` facade over relational (sqlite3, postgres slot), vectors, graph, objects, cache, snapshots, artifacts, checkpoints, backups — the spec's on-disk layout.
- **Phase 7** `kernel/` + `capabilities/`: `Kernel.submit(goal)` is the single entry point (User → Kernel → Planner → Execution DAG → Providers → Verifier → Memory → Response). Providers are rich records selected by constraints + learned policy; nothing names a model directly.
- **Execution DAG** `execution/`: goals compile into graphs (`, then` = sequential, `and` = parallel branches); per-node checkpoints; failed branches skip their dependents without killing independent ones.
- **Verification** `verification/`: constraint → fact-check (vs world facts) → consistency → safety → confidence, on every provider output, provider-independent.
- **Phase 8** `world/`: projects/goals/jobs/sessions persisted across restarts — NCP remembers projects, not chats.
- **Phase 9** `learning/`: all events → telemetry (sqlite); experience DB + rewards; `RoutingOptimizer` turns historical success into the routing policy (tested: a learned policy overrides the keyword/prior default).
- **Phase 10** `recovery/`: per-node checkpoints, snapshots, crash detection, `Kernel.resume(run_id)` — restart → load → continue, preserving completed work (tested with a mid-DAG crash drill).

## 6. Current state

- **219 tests**, all passing; ruff clean; connectivity test enforces no empty or orphaned modules across all 40 subpackages.
- Zero required dependencies; extras: `[dev]`, `[api]`, `[config]`, `[llm]`.
- Three entry points: `Runtime` (reference loop), `python -m ncp.cli.main --demo` / `PlatformRuntime` (platform spine), and `Kernel.submit()` (the AI-OS pipeline that composes both).

## 7. Phase 11 — Full unification (one true call graph)

A definitive call-reachability audit (code-read, not trace-based) confirmed the merge had produced **two working pipelines that never called each other**: CLI/API → platform `Container`/`Runtime`/`Planner`/`Router`, and `Kernel.submit()` → reference runtime + Phase 6–10 layer — with roughly 35–40 real, individually-tested modules (provenance, compression, coding, simulator, most of research/graph/skills, workers, the platform's own planner/router/executor) unreachable from any production entry point. Phase 11 removed the split:

- **One engine**: `Container.build()` constructs the `Kernel` sharing its own event bus, memory, planner, router, constraints, simulator, executor, and research instances; `PlatformRuntime.execute_goal()` delegates to `Kernel.submit()`. CLI and API are unchanged callers.
- **Platform lineage in every node**: the DAG compiler annotates each sub-goal with the platform planner's plan score and the simulator's outcome prediction; each node is additionally routed and executed as a platform `Task`; the `ConstraintSolver` runs as an extra verification stage.
- **Provenance + audit**: every committed memory carries a persisted `ProvenanceRecord` (source, evidence, confidence), a lineage entry, and an audit-trail row.
- **Vector memory** (user-requested): `memory/embedding.py` provides stdlib feature-hashing embeddings (word + char-trigram, L2-normalized); every stored item lands in the `VectorStore`; retrieval adds a similarity-thresholded vector stage; embeddings persist via the storage `vectors/` slot.
- **Research & coding node types**: research nodes run the discovery loop (evidence-corroborated hypotheses enter semantic memory); build-focused nodes run generate → verify → optimize → benchmark and save the best candidate as a code artifact.
- **Skills, workers, events**: episode-based skill extraction + evolution in `Kernel.run_maintenance()` (every 10th run: skills, graph compression, backups); consolidation/cleanup workers dispatched on `TASK_FINISHED` via `EventDispatcher`; all kernel events go through `EventPublisher` with `EventPriority` triage.
- **Knowledge graph**: `MemoryManager` mirrors every item into a live `Graph` + `GraphIndex` (typed nodes, temporal edges); `RetrievalEngine.retrieve` is genuinely called; kernel exposes `graph_report/graph_traverse/graph_merge/graph_split/graph_expand`.
- **Recovery is automatic**: the kernel diagnoses interrupted runs at boot and auto-resumes them; checkpoints also get a compressed artifact copy.
- **Cluster on the kernel**: each distributed node owns a `Kernel`; `api/protocol.py` gains `handle_kernel_request`.
- **The guard**: `tests/test_call_reachability.py` patches 33 previously-dead methods with counting spies (`autospec` + original `side_effect`) and drives one full kernel lifecycle — every target must be called. Import-only connectivity can no longer mask a disconnected module.

Latent bugs surfaced and fixed by the wiring: `ResearchManager`'s in-function `Memory` import (broke isinstance routing after module reloads), `MemoryManager._store_episodic` double-appending episodes and never marking them successful (starved the skill extractor), `split_by_clustering` calling a method that only exists on `QueryEngine`, and the discovery gate being unpassable (hypotheses spawned below the verification threshold with no way to gain confidence).

**Current state: 293 tests, ruff clean, sandbox-verified (clean checkout → fresh venv → suite → CLI demo → kernel E2E → maintenance → crash/auto-resume drill).**
