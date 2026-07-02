"""Main CLI entry point."""

import argparse
import logging
import sys

from ncp.core.entities import Goal
from ncp.runtime.container import Container
from ncp.utils.config import load_config
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="NCP - Neural Capability Platform")
    parser.add_argument("--config", default="configs", help="Config directory")
    parser.add_argument("--goal", help="Goal to execute")
    parser.add_argument("--serve", action="store_true", help="Start API server")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    parser.add_argument("--stats", action="store_true", help="Show stats")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load config
    config = load_config(args.config)

    if args.demo:
        run_demo(config)
    elif args.goal:
        run_goal(config, args.goal)
    elif args.stats:
        show_stats(config)
    elif args.serve:
        start_server(config)
    else:
        parser.print_help()


def run_demo(config):
    """Run a demo."""
    print("NCP Demo - Initializing system...")

    container = Container(config=config).build()
    runtime = container.get_runtime()
    runtime.initialize()

    print("System initialized!")
    print(f"Runtime state: {runtime.state.status.name}")

    # Execute a sample goal
    goal = Goal(name="demo_goal", description="Demonstrate NCP capabilities")
    results = runtime.execute_goal(goal)

    print(f"\nGoal executed: {len(results)} results")
    for r in results:
        print(f"  - {r.status}: {r.output}")

    runtime.shutdown()
    print("\nDemo complete!")


def run_goal(config, goal_text):
    """Execute a goal."""
    container = Container(config=config).build()
    runtime = container.get_runtime()
    runtime.initialize()

    goal = Goal(name=goal_text)
    results = runtime.execute_goal(goal)

    for r in results:
        print(f"{r.status}: {r.output}")

    runtime.shutdown()


def show_stats(config):
    """Show system stats."""
    container = Container(config=config).build()
    runtime = container.get_runtime()
    runtime.initialize()

    stats = runtime.state.to_dict()
    for key, value in stats.items():
        print(f"{key}: {value}")

    runtime.shutdown()


def start_server(config):
    """Start API server."""
    try:
        import uvicorn

        from ncp.api.server import create_app

        app = create_app(config)
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError:
        print("API server requires: pip install fastapi uvicorn")
        sys.exit(1)


if __name__ == "__main__":
    main()
