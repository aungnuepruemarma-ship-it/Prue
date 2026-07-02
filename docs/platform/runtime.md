# Runtime

The Runtime is the central orchestrator. It owns every subsystem. Nothing owns Runtime.

## Lifecycle

1. Load Config
2. Initialize Logger
3. Load Plugins
4. Create Container
5. Create Runtime
6. Register Event Listeners
7. Initialize Storage
8. Initialize Memory
9. Initialize Planner
10. Initialize Router
11. Start Scheduler
12. Ready

## Shutdown Sequence

1. Stop Scheduler
2. Flush Event Queue
3. Save Memory
4. Save Graph
5. Save Storage
6. Close Adapters
7. Exit
