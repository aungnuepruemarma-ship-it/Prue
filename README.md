# NCP — Nexus Computing Platform

NCP is an AI operating system built from two unified lineages plus an
AI-OS layer on top:

- a **reference runtime**: goal → activation → capability routing →
  declarative constraint gate (Φ) → goal-conditioned objective → execution
  → memory/skill learning;
- the **Neural Capability Platform**: interfaces, event bus, DI container,
  7-tier hierarchical memory, UUID-keyed knowledge graph, provenance,
  compression, research loop;
- the **kernel** (Phases 6–10): persistent storage layer, execution DAGs,
  provider-independent verification, world state, learning engine, and
  crash recovery.

Phase 11 unified the two lineages into **one call graph**: the CLI/API
delegate to the kernel, the kernel drives the platform planner/router/
executor/constraints per node, and a call-reachability test proves that
33 previously-standalone methods (provenance, compression, vector memory,
research, coding, skills evolution, workers, graph analytics, recovery)
are genuinely invoked by every kernel lifecycle.

Everything runs on the standard library; optional extras add the HTTP API
(`[api]`), YAML configs (`[config]`), and the Anthropic-backed reasoner
(`[llm]`, or just set `ANTHROPIC_API_KEY` — the stdlib transport is built in).

## Quick start

```bash
pip install -e ".[dev]"
pytest -q                      # 293 tests
python -m experiments.demo     # reference runtime + cluster + kernel
python -m ncp.cli.main --demo  # platform spine (goal -> plan -> route -> execute)
```

```python
from ncp.kernel import Kernel

kernel = Kernel(storage_root="storage")
response = kernel.submit("research task routing, then update the index", project="my-project")
print(response.status, response.confidence)
print(response.response)
kernel.resume(response.run_id)   # recovery: restart -> load checkpoint -> continue
```

## Architecture

```text
User
  ↓
Kernel (single entry point; everything communicates via the event bus)
  ↓
Planner → DAG Compiler        (", then" chains, "and" parallel branches)
  ↓
Scheduler / Provider Selector (constraints + learned policy over rich
  ↓                            provider records — no hardcoded model names)
Execution DAG                 (per-node checkpoints; failures skip dependents)
  ↓
Capability Providers          (rule reasoner / Claude / external executable,
  ↓                            each proposal gated by Φ and objective-scored)
Verifier                      (constraint → fact-check → consistency →
  ↓                            safety → confidence; provider-independent)
Memory                        (7 tiers + episodic history + skill promotion
  ↓                            bridged into the platform skill registry)
Response                      (+ world state, telemetry, experience DB)
```

Storage layout (`storage/`): `relational/` (sqlite3; postgres slot),
`vectors/`, `graph/`, `artifacts/`, `checkpoints/`, `world_state/`,
`telemetry/`, `backups/`, `cache/`, `registry/` — stdlib backends,
pluggable for PostgreSQL/Qdrant/Neo4j (declared in `docker-compose.yml`).

## Key properties

- **Nothing calls a model directly** — the kernel selects providers by
  capability constraints and historical success (the learning engine's
  policy replaces `if code: use X`).
- **Every output is verified** before commit, independent of its provider.
- **Every node is checkpointed** — `Kernel.resume(run_id)` continues an
  interrupted run without redoing completed work.
- **NCP remembers projects, not chats** — world state (projects, goals,
  jobs, sessions) persists across restarts.
- **No empty modules, no orphans** — a connectivity test enforces that all
  40 subpackages are non-empty and reachable from the entry points, and
  `tests/test_call_reachability.py` proves 33 key methods across every
  subsystem are *called* (not just imported) during a kernel lifecycle.
- **Vector memory** — every stored item is embedded (stdlib feature-hashing:
  word + character-trigram features, L2-normalized) into a cosine-similarity
  vector store; retrieval finds paraphrases keyword search misses, and
  embeddings persist across restarts.
- **Self-healing boot** — the kernel diagnoses interrupted runs at startup
  and auto-resumes them (`startup_report_summary()`).

## Documentation

- `docs/ANALYSIS.md` — deep-dive of the original reference runtime
- `docs/PLATFORM_ANALYSIS.md` — analysis of the merged platform, the
  revisions applied, and the Phase 6–10 build
- `docs/RESEARCH.md` — related-work positioning
- `docs/IMPROVEMENT_ROADMAP.md` — completed roadmap with status
- `docs/platform/` and `spec/` — platform docs and specifications
