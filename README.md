# NCP — Nexus Computing Platform

NCP is a modular orchestration and reasoning platform. It coordinates:
- goals
- planning
- capability routing
- reasoning modules
- an SMT-style finite constraint gate (Φ)
- objective scoring
- memory and skill extraction
- storage and monitoring

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
Planner
  ↓
Capability Router
  ↓
Reasoner / Tool / Solver
  ↓
Constraint Engine (Φ)
  ↓
Objective Function
  ↓
Executor
  ↓
Memory + Skill Update
  ↓
Storage + Monitoring
```

This repo is a GitHub-ready reference implementation: runnable, testable, modular, and easy to extend.
