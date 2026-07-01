# Interfaces

## Reasoner
- input: goal, universe, active entity ids
- output: transformation candidates

## Constraint checker
- input: universe, candidate, goal
- output: admissibility, violations, explanation

## Executor
- input: universe, candidate
- output: updated universe

## Storage
- input: universe/history/graph/skills
- output: persisted artifacts
