# Architecture

NCP is organized into runtime layers:
- boot
- kernel
- planner
- router
- constraints
- execution
- memory
- storage
- monitoring
- distributed runtime

The router selects models/tools by capability. Φ checks admissibility. The objective function ranks admissible candidates. Memory and skills update after every committed step.
