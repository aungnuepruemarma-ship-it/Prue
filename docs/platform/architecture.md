# NCP Architecture

## Overview

NCP (Neural Capability Platform) is a modular AI orchestration system designed for autonomous task execution, hierarchical memory management, and continuous skill improvement.

## Core Principles

1. **Interface-Driven Design**: All subsystems communicate through well-defined interfaces
2. **Event-Driven Architecture**: No module directly calls another; everything emits events
3. **Hierarchical Memory**: Multi-scale memory with fractal graph structure
4. **Dependency Injection**: Container manages all subsystem lifecycle
5. **No Circular Dependencies**: Strict dependency graph from interfaces downward

## System Layers

```
Application (CLI/API)
    |
    v
Runtime (Orchestrator)
    |
    +-- Planner (Goal -> Task Graph)
    +-- Router (Capability Selection)
    +-- Executor (Action Execution)
    +-- Memory (Hierarchical Storage)
    +-- Storage (Persistence)
    +-- Constraints (Validation)
    +-- Simulator (Outcome Prediction)
    +-- Research (Discovery Loop)
    +-- EventBus (Communication)
```

## Data Flow

```
Goal -> Plan -> Route -> Validate -> Simulate -> Execute -> Event -> Memory -> Graph -> Compress -> Store
```

## Module Dependencies

Application -> Runtime -> Interfaces -> Implementations -> Storage
