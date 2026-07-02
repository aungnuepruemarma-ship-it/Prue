# NCP - Neural Capability Platform

A modular AI orchestration system with hierarchical memory, fractal graphs, and autonomous skill discovery.

## Quick Start

```bash
# Setup
make setup

# Run tests
make test

# Run benchmarks
make benchmark

# Start server
make serve
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for full details.

## Module Structure

```
ncp/
  api/          - REST API endpoints
  cli/          - Command-line interface
  interfaces/   - Abstract base classes
  core/         - Entity hierarchy
  runtime/      - System orchestrator
  events/       - Event bus
  planner/      - Goal decomposition
  router/       - Capability selection
  constraints/  - Validation engine
  simulator/    - Outcome prediction
  memory/       - Hierarchical memory
  graph/        - Fractal knowledge graph
  compression/  - Rate-distortion compression
  provenance/   - Audit trail
  storage/      - Persistence layer
  skills/       - Skill extraction
  research/     - Discovery loop
  coding/       - Code generation
  workers/      - Background processors
  utils/        - Shared utilities
```

## License

MIT License - see [LICENSE](LICENSE)
