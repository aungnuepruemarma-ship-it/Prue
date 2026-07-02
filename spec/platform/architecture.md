# Architecture Specification

## Subsystems

| Subsystem | Responsibility | Dependencies |
|-----------|---------------|--------------|
| Runtime | Orchestration | All |
| Planner | Goal decomposition | Router, Constraints |
| Router | Capability selection | Registry, History |
| Executor | Action execution | EventBus |
| Memory | Hierarchical storage | Graph, Storage |
| Graph | Structured knowledge | Compression |
| Compression | Efficient storage | Memory |
| Constraints | Validation | Solver |
| Simulator | Outcome prediction | Physics |
| Research | Discovery loop | Memory, Skills |
| Storage | Persistence | None |
| EventBus | Communication | None |
