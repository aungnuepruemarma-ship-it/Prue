# Interface Contracts

All subsystems implement interfaces defined in `ncp/interfaces/`.

## Key Interfaces

- PlannerInterface: plan(goal) -> Plan
- RouterInterface: route(task) -> Capability
- ExecutorInterface: execute(action) -> Result
- MemoryInterface: store/query/retrieve
- StorageInterface: save/load/delete
- ConstraintInterface: validate/solve/explain
- SimulatorInterface: simulate(action) -> Prediction
