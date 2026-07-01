# NCP Improvement Roadmap

*Prioritized, concrete fixes derived from `ANALYSIS.md` (verified findings) and `RESEARCH.md` (borrowable ideas). Effort estimates: S < 1h, M = half-day, L = multi-day.*

> **Status:** All P0 items, all P1 items (with stubs implemented and wired in rather than deleted, plus a declarative Φ without the optional Z3 backend), and all P2 items were implemented after this document was written. The remaining open ideas are the optional Z3 encoding (P1.6 second step) and ACT-R-style activation decay beyond the recency bonus that was added (P2.4).

## P0 — Correctness (the loop currently violates its own invariants)

### P0.1 Make `Universe.clone` a deep copy — fixes the validation-mutates-state bug (S)
- **Where**: `ncp/core/universe.py:30-36`, `ncp/core/entity.py:17-28`
- **What**: trial entities share `state`/`knowledge`/`metadata` dicts with live entities, so Φ checks and objective scoring mutate the real universe (verified, `ANALYSIS.md` §7.1).
- **Fix**: in `clone()`, use `copy.deepcopy` for the nested dicts (or have `to_dict()` return copies — but that changes `snapshot()`/storage semantics too, so prefer fixing `clone`). Same treatment for `Relation.metadata`.
- **Test**: assert that after `FinitePhiChecker.check` with an update candidate, the live entity's `state` is unchanged.

### P0.2 Fix the dead novelty term (S)
- **Where**: `ncp/objective/objective.py:22`
- **What**: it reads `universe.history` looking for a `"candidate"` key that universe history never contains (only `"op"`); novelty is always 1.0 (verified, §7.2).
- **Fix**: either match on `"op"` (map candidate names ↔ op names), or pass the runtime's `HistoryLog` (which *does* record `candidate`) into `score`.
- **Test**: a candidate already present in history must get novelty 0.0.

### P0.3 Goal-condition the objective — stop rewarding inaction (M)
- **Where**: `ncp/objective/objective.py:14-23`
- **What**: the minimized score grows with entity count/cost and has no goal-relevance term, so for a "create" goal the create candidate scores worst and the no-op ties for best (verified, §7.3).
- **Fix**: add a relevance term, e.g. token overlap between the goal and `candidate.description`/`candidate.task_type`/`params`, subtracted from the score with a weight large enough to dominate the ~0.25 structural penalty of one create. Reuse the tokenization already in `ActivationEngine.score` (`core/activation.py:15-24`) — extract it to `utils`.
- **Test**: for goal "create a new concept entity", `create_entity` must win; for a pure recall goal, `query_memory` may win.

### P0.4 Promote skills only from successful traces (S)
- **Where**: `ncp/memory/skills.py:38`
- **What**: the extractor consumes rejected events too, violating `spec/invariants.md`.
- **Fix**: filter `events` to `e.get("status") == "accepted"` (runtime events) or op-bearing universe events, before building bigrams.
- **Test**: a repeated rejected candidate must not produce a skill.

### P0.5 Persist provenance (S)
- **Where**: `ncp/core/universe.py:48-54` (`snapshot` omits `history`), `ncp/storage/json_store.py`
- **Fix**: include `history` in `snapshot()`; add a `load_universe` counterpart so persistence is round-trippable.
- **Test**: save → load → deep-equal snapshot.

## P1 — Make the architecture real (each stub either works or goes)

### P1.1 Wire the planner into execution (M)
`Plan` is computed and returned but never used (`runtime.py:52`). Either route each `PlanStep` through the router (steps become sub-goals driving `propose_candidates`) or delete the planner from the loop. Recommended: iterate steps, so plans stop being decorative.

### P1.2 Make the router consult its capability registry (M)
`CapabilityRouter.route` (`routing/router.py:35-45`) ignores `self.registry`, and the "verify" branch routes to the same reasoner as the default. Match task types derived from the goal/plan step to `CapabilityCard.strengths`, and drop cards that advertise nonexistent capabilities (the "smt" solver card) until they exist.

### P1.3 Implement one real LLM adapter (M/L)
`LLMAdapter` and `MythosAdapter` both delegate to `RuleBasedReasoner`, making all routes identical. Implement one real adapter behind the existing `Reasoner` ABC (`reasoning/base.py`) that calls an LLM API to propose `TransformationCandidate`s (constrained JSON out → validated into the four `make_*` factories). Keep the rule-based reasoner as the zero-dependency default; gate the adapter behind an extras dependency.

### P1.4 Close the skill loop (M)
Skills are write-only. During candidate proposal, check `SkillLibrary` for patterns whose first op matches the current context and emit a composite candidate. Also: delete the no-op `SkillLibrary.update_from_history` (`skills.py:30-31`) and its call site (`runtime.py:73`), or move `SkillExtractor.promote` into it.

### P1.5 Delete or demote dead stubs (S)
- Remove unused duplicate `ncp/graph/graph.py` (real one: `ncp/memory/graph.py`).
- Remove or move to a clearly-labeled `experimental/` namespace: `adapters/external.py`, `api/protocol.py`, `compiler/ir.py`, `distributed/cluster.py`, `research/engine.py`, `world_model/model.py`. Empty packages that mirror roadmap items belong in the roadmap, not the tree.
- Rename `core/transformation.py` → `core/candidate.py` (or merge into `transformations.py`) to kill the near-identical filenames.
- Drop dead imports (`runtime.py:7` factories, `memory/graph.py` `asdict`) and unused `HistoryLog.ngrams` (or use it in the skill extractor instead of re-implementing bigrams).

### P1.6 Declarative Φ, optionally Z3-backed (L)
Turn Φ's hardcoded checks (`constraints/finite_phi.py:21-48`) into a list of named predicate objects evaluated over the trial state; the `"forbidden" in goal` string check becomes a data-defined policy. Optional second step: encode the finite invariants in `z3-solver` to make "SMT-style" literal and get unsat cores for real explanations in `explanation.py`. (See `RESEARCH.md` §2.3.)

## P2 — Engineering hygiene

### P2.1 Test the negative paths (M)
Priority order: Φ rejections (limits, dangling relations, unknown task type, forbidden policy), clone purity (P0.1's test), objective ordering (P0.3's test), storage round-trip (P0.5's test), router branch selection, activation threshold + fallback, curiosity suggestion.

### P2.2 CI and packaging (S)
- Matrix CI over Python 3.10–3.13 (currently 3.11 only vs `requires-python >= 3.10`); add `ruff check` (and optionally `mypy`) steps to `.github/workflows/ci.yml`.
- Delete `pytest.ini` (duplicate of `[tool.pytest.ini_options]` in `pyproject.toml`).
- Remove committed artifacts: add `ncp_output/` to `.gitignore` and `git rm -r --cached ncp_output`.

### P2.3 Incremental persistence (M)
`Runtime.save()` rewrites all four JSON files every step. Append episodes to `episodes.jsonl` incrementally; snapshot the universe every N steps or on shutdown. Pairs naturally with checkpoint/restore (P0.5, `RESEARCH.md` idea #1).

### P2.4 Soften the activation knife-edge (S)
`0.2·overlap + 0.2·confidence` vs threshold 0.35 puts the seed `e_mem` entity at 0.34 — one hundredth below activation. Either lower the default threshold, weight overlap higher, or (better) add recency-based base activation (ACT-R style, see `RESEARCH.md` §2.2).

## Suggested sequencing

1. **Sprint 1 (correctness)**: P0.1 → P0.2 → P0.4 → P0.5 → P0.3, each with its test (covers most of P2.1 en route). Small diffs, immediately makes the specs' invariants true.
2. **Sprint 2 (hygiene)**: P2.2, P1.5 — cheap cleanups that shrink the surface before feature work.
3. **Sprint 3 (architecture)**: P1.1 + P1.2 together (plan→route is one feature), then P1.4, then P1.3.
4. **Sprint 4 (differentiators)**: P1.6 and P2.3 — the pieces that make NCP's "verified, resumable, skill-learning loop" pitch real.
