# NCP — Nexus Computing Platform

NCP is a modular orchestration and reasoning platform. It coordinates:
- goals
- planning (compiled to an IR that drives routing)
- capability routing via a registry of capability cards
- reasoning modules (rule-based, LLM-backed with offline fallback, external-executable)
- a declarative finite constraint gate (Φ) — side-effect-free admissibility checks
- goal-conditioned objective scoring
- memory, skill extraction, and skill replay
- a world model, research findings, storage, and monitoring
- a task protocol and a round-robin cluster of runtimes

The LLM reasoner uses the Anthropic API when `ANTHROPIC_API_KEY` is set and
falls back to the rule-based reasoner otherwise; the platform itself stays
pure-stdlib with no required dependencies.

## Quick start

```bash
pip install -e .
pytest -q
python -m experiments.demo
```

## Output

The demo writes JSON artifacts to `ncp_output/`:
- `universe.json`
- `episodes.jsonl`
- `memory_graph.json`
- `skills.json`

## Architecture

```text
Goal
  ↓
Planner → Compiler (Plan → IR task hints)
  ↓
Capability Router (registry of capability cards)
  ↓
Reasoners (rule / LLM / external) + learned-skill candidates
  ↓
Constraint Engine (Φ) — declarative, side-effect-free
  ↓
Objective Function (goal relevance + novelty − growth)
  ↓
Executor
  ↓
Memory Graph + Skill Update + World Model + Research Findings
  ↓
Storage (incremental episodes, restorable snapshots) + Monitoring
```

A `TaskRequest`/`TaskResponse` protocol (`ncp.api`) exposes the runtime, and
`ncp.distributed.Cluster` round-robins tasks across multiple runtimes.

This repo is a GitHub-ready reference implementation: runnable, testable, modular, and easy to extend.
