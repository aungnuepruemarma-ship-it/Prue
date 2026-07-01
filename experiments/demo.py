from __future__ import annotations
from ncp.core.runtime import Runtime, build_default_universe

def main():
    runtime = Runtime(build_default_universe())
    goals = [
        "create a new concept and connect memory",
        "update the active memory with a useful pattern",
        "research a better way to route capabilities",
    ]
    for goal in goals:
        result = runtime.step(goal)
        print("=" * 80)
        print("GOAL:", goal)
        print("STATUS:", result.status)
        print("CHOSEN:", result.chosen)
        print("EXPLANATION:", result.explanation)
        print("SUMMARY:", result.summary)

if __name__ == "__main__":
    main()
