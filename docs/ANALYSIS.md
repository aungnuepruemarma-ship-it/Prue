# NCP Codebase Analysis

*An architecture and code-quality deep-dive of the NCP (Nexus Computing Platform) reference implementation, as of commit `de846b1`.*

> **Status:** This document describes the codebase as originally imported. Every bug and design flaw identified below (§7) has since been fixed, and the stub modules (§3) have been implemented and wired into the runtime — see `IMPROVEMENT_ROADMAP.md` for the item-by-item status.

## 1. Overview

NCP is a ~950-line, pure-stdlib Python package (no third-party dependencies) that implements a goal-driven orchestration loop: a goal string flows through activation, routing, candidate generation, a constraint gate (Φ), objective scoring, execution, and memory/skill updates, with JSON persistence after every step.

The honest one-line summary: **NCP is a coherent architectural sketch with a working end-to-end toy loop, wrapped in aspirational specs and a ring of empty stub packages.** Roughly half the module tree contains real (if simple) logic; the other half is placeholder classes that nothing instantiates. Three of the core mechanisms have verified defects (see §7).

## 2. End-to-end control flow

Entry point: `experiments/demo.py` builds a default two-entity universe and calls `Runtime.step(goal)` for three hardcoded goals.

The orchestration loop is `Runtime.step` (`ncp/core/runtime.py:50-89`):

```
goal
 ├─ Planner.plan(goal)                      # computed, but never used downstream (§7.4)
 ├─ ActivationEngine.score(universe, goal)  # token-overlap entity activation
 ├─ CapabilityRouter.route(goal, ...)       # keyword → reasoner → candidates
 ├─ for each candidate:
 │    ├─ FinitePhiChecker.check(...)        # Φ admissibility gate (on a clone — see §7.1)
 │    └─ ObjectiveFunction.score(...)       # entropy + cost + size − novelty
 ├─ scored.sort(); pick LOWEST score        # objective is minimized
 ├─ Executor.execute(universe, chosen)      # commit the winning transformation
 ├─ history / memory-graph / skill updates
 └─ JsonStore.save() — rewrites all four JSON files every step
```

Key detail: `runtime.py:67-68` sorts ascending and takes `scored[0]`, so **lower objective scores win**.

## 3. Module inventory: real vs stub

### Substantive (real logic, toy scale)

| Module | What it actually does |
|---|---|
| `core/runtime.py` | The orchestrator; wires all components; `build_default_universe()` seeds 2 entities + 1 relation |
| `core/entity.py`, `core/universe.py` | Data model: `Entity`, `Relation`, `Universe` with `clone`/`snapshot`/history |
| `core/transformation.py` | `TransformationCandidate` (name, task_type, params, cost, `execute` callable) |
| `core/transformations.py` | The four real mutators: create/update/merge entities, add relation (closures that bump versions and record history) |
| `core/activation.py` | Scores entities `0.2·token_overlap + 0.2·confidence` vs threshold 0.35; falls back to the single highest-confidence entity |
| `planning/planner.py` | Keyword-matches the goal into a fixed 2–3 step `Plan` (build/research/default branches) |
| `routing/router.py` | Keyword-routes to one of three reasoners and delegates `propose` |
| `reasoning/rule_based.py` | The only reasoner with logic: emits up to 5 candidates (create/update/merge/relate + an always-present `query_memory` no-op) |
| `constraints/finite_phi.py` | Φ gate: size limits, task-type whitelist, trial-apply on a clone, dangling-relation check, one hardcoded "forbidden" policy |
| `objective/objective.py` | `1.0·(0.05·E) + 1.2·entropy + 1.0·(0.2E+0.1R+0.05A) − 0.2·novelty`, minimized |
| `execution/executor.py` | Calls `candidate.apply(universe)` |
| `memory/graph.py`, `memory/history.py` | Rebuilds a node/edge graph from the universe; append-only event log |
| `memory/skills.py` | `SkillExtractor.promote`: promotes action **bigrams** seen ≥ 2 times in history to named `Skill`s |
| `storage/json_store.py` | Writes `universe.json`, `episodes.jsonl`, `memory_graph.json`, `skills.json` |
| `monitoring/diagnostics.py`, `curiosity/engine.py`, `utils/*` | Counters; "suggest `research <most frequent goal word>`"; config/ids/metrics helpers |

### Stubs (no behavior; nothing instantiates them)

| Module | State |
|---|---|
| `adapters/external.py` | `available()` hardcoded `False`; never used |
| `api/protocol.py` | Bare request/response dataclasses; no server |
| `compiler/ir.py` | IR dataclasses; unused |
| `distributed/cluster.py` | `Node`/`Cluster` shell; unused |
| `graph/graph.py` | Second `Graph` class **duplicating** `memory/graph.py`; has `edges` field but no `add_edge`; unused |
| `research/engine.py` | `add_finding` container; the "research" plan/route never touches it |
| `world_model/model.py` | `update_fact` dict wrapper; unused |
| `reasoning/llm_adapter.py`, `reasoning/mythos_adapter.py` | **Pseudo-stubs**: both store an unused endpoint/executable and delegate verbatim to `RuleBasedReasoner`. The router's "llm"/"mythos" branches are behaviorally identical to "rule" |

The stub packages map one-to-one to the unimplemented roadmap items in `spec/roadmap.md` / `ROADMAP.md` (API server, distributed runtime, compiler, world model).

## 4. Data model and core algorithms

- **Entity** (`core/entity.py`): `id, type, name, state{}, knowledge{}, confidence, cost, version, metadata{}`. Note: `to_dict()` returns the *same* nested dict objects by reference — the root cause of the aliasing bug (§7.1).
- **Universe** (`core/universe.py`): `entities{id→Entity}, relations[], history[], version`. `snapshot()` **omits `history`**, so op-level provenance is never persisted (§7.6).
- **Φ gate** (`constraints/finite_phi.py:21-48`): despite the "SMT-style" docstring, it is six hand-written imperative checks — entity/relation count limits, non-empty name, a task-type whitelist (which includes `research`/`plan`/`skill` types no reasoner ever produces), trial-apply-must-not-raise, no dangling relation endpoints, and a single hardcoded string policy (`"forbidden" in goal` blocks creates). There is no solver.
- **Skills**: frequently recurring **bigrams** over the action stream (`memory/skills.py:37-51`), e.g. `skill_update_entity_query_memory`. `SkillLibrary.update_from_history` is a literal `pass` yet is called every step.

## 5. Test coverage

Three tests, all happy-path:

- `test_runtime.py` — asserts `step()` returns *any* of the three statuses (accepted/rejected/no_candidates), i.e. only "doesn't crash".
- `test_constraints.py` — Φ accepts one valid update. **No test ever asserts Φ rejects anything** (limits, dangling relations, unknown task types, the forbidden policy).
- `test_skills.py` — a repeated bigram promotes a skill.

Uncovered: objective scoring, executor, router branches, planner, activation, curiosity, memory-graph ingestion, storage round-trip, `Universe.clone` correctness, and every negative/edge path. Nothing asserts the LLM/Mythos adapters differ from rule-based (they don't).

## 6. Spec vs implementation

| Spec claim | Reality |
|---|---|
| `invariants.md`: "No state update is committed without constraint validation" | Φ does run first, **but validation itself mutates live state** via the shallow clone (§7.1) — the invariant is violated in spirit |
| `invariants.md`: "Skills are promoted only from repeated successful traces" | The extractor consumes **all** events, including `status: "rejected"` ones (they carry a `candidate` key at `runtime.py:61`) |
| `invariants.md`: "Storage must preserve provenance and version metadata" | `snapshot()` drops `universe.history`; op-level provenance never reaches disk |
| `requirements.md`: "working, episodic, semantic, and skill memory layers" | Only a flat event log + rebuilt graph + skill bigrams; no tiering |
| `architecture.md` / README: "router selects models/tools by capability"; "SMT-style constraint gate" | Routing is keyword matching; the `CapabilityCard` registry (including an "smt" solver card) is defined but **never consulted**; no SMT anywhere |
| `schemas.md` | Accurate — matches the code |

## 7. Verified findings

Findings 1–3 were reproduced with a script against the live code; the outputs below are actual observed behavior.

### 7.1 BUG — Φ validation and objective scoring mutate the live universe (high impact)

`Universe.clone()` (`core/universe.py:32`) builds trial entities via `Entity(**v.to_dict())`, and `Entity.to_dict()` (`core/entity.py:17-28`) returns the **same** `state`/`knowledge`/`metadata` dicts by reference. `make_update_entity` then does `entity.state.update(...)` (`core/transformations.py:27-28`) on the shared dict. So trial-applying a candidate inside `FinitePhiChecker.check` (`finite_phi.py:34`) or `ObjectiveFunction.score` (`objective.py:17`) writes into the real universe — for **every** update/merge candidate, including ones ultimately rejected or not chosen.

Observed:

```
live e_root.state BEFORE check: {'status': 'seed'}
Phi admissible: True (candidate was only CHECKED on a clone, never executed)
live e_root.state AFTER check:  {'status': 'seed', 'tainted_by_validation': True}
```

(Relation *lists* are rebuilt so list appends are safe, but relation `metadata` dicts are aliased the same way. Merge candidates also inherit aliased dicts via `{**s.state, **t.state}` only at merge time — the source entities' dicts remain shared with the trial.)

### 7.2 BUG — the novelty term is always 1.0 (feature silently disabled)

`objective.py:22` searches `universe.history` for a `"candidate"` key, but universe history events are written by `record_history` with an `"op"` key only (`transformations.py:20,31,54,62`). The comprehension is always empty, so every candidate is "novel" and `−0.2·novelty` is a constant that can never break ties. Observed: a candidate committed 3 times still gets `novelty = 1.0`; the history key set is `['id', 'knowledge_patch', 'op', 'state_patch']` — no `'candidate'`.

(The runtime's *own* `HistoryLog` does use a `candidate` key, but the objective is handed the universe history, not the runtime history — a wiring mismatch.)

### 7.3 DESIGN FLAW — the objective is goal-agnostic and penalizes the goal's own action

The score is minimized and grows with entity count and structural cost, with no term for goal relevance. For the goal `"create a new concept entity"`, observed candidate scores (lower wins):

```
create_entity    score=1.9500   ← the action the goal asks for scores WORST
update_entity    score=1.7000   ← chosen (tie with no-op, wins on sort stability)
add_relation     score=1.8000
query_memory     score=1.7000   ← the do-nothing no-op ties for best
```

The create action is structurally penalized *because* it creates, and the always-present `query_memory` no-op (`rule_based.py:64-73`, `execute=lambda u: u`) ties for best. The system's incentives run opposite to its goals; only sort stability keeps it from literally choosing to do nothing.

### 7.4 Dead wiring

- **Planner output is decorative**: computed at `runtime.py:52`, returned in `summary["plan"]`, never used for routing or execution. Planner, router, and reasoner are three independent keyword matchers that don't compose.
- **Router's capability registry is dead data** (`router.py:29-33`); `route` never reads it. The "verify/valid/constraint/proof" branch routes to `rule` — same as the default branch. All three reasoner routes are behaviorally identical (§3).
- `SkillLibrary.update_from_history` is `pass` but called every step (`runtime.py:73`).
- Dead imports: the four `make_*` factories in `runtime.py:7`; `asdict` in `memory/graph.py`; `HistoryLog.ngrams` is never called (the skill extractor re-implements bigrams).

### 7.5 Fragility and hygiene

- **Activation threshold knife-edge**: with the default universe, a goal containing "memory" scores `e_mem` at exactly `0.34` vs threshold `0.35` — one word of overlap misses activation by 0.01 and silently changes which entities candidates target.
- **Persistence**: `save()` rewrites all four JSON files on every step — O(history) I/O per step.
- **Naming**: `core/transformation.py` vs `core/transformations.py`; unused `graph/graph.py` vs real `memory/graph.py`.
- **Packaging/CI**: `pytest.ini` duplicates `[tool.pytest.ini_options]` in `pyproject.toml`; CI tests only Python 3.11 although `requires-python >= 3.10`; no lint/type-check step; generated artifacts (`ncp_output/*.json`) are committed.

## 8. Bottom line

The core loop genuinely runs end to end and the architecture is legible — activation → routing → propose → gate → score → execute → remember is a sound skeleton. But the three load-bearing mechanisms that would make it *principled* are each compromised: the constraint gate has side effects (7.1), the objective's exploration term is dead (7.2) and its incentives are inverted relative to goals (7.3). Fixing those three, then collapsing or implementing the stub ring, is the path from sketch to system — see `IMPROVEMENT_ROADMAP.md`. For how NCP's ideas relate to established systems, see `RESEARCH.md`.
