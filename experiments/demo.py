from __future__ import annotations

from ncp.core.runtime import Runtime, build_default_universe
from ncp.distributed.cluster import Cluster


def run_single_runtime() -> None:
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
        print("NEXT GOAL:", result.summary.get("next_goal"))
        print("WORLD MODEL:", result.summary.get("world_model", {}).get("facts"))
        print("SKILLS:", result.summary.get("skills"))

def run_cluster() -> None:
    print("=" * 80)
    print("CLUSTER: two nodes, round-robin task submission via the API protocol")
    cluster = Cluster()
    cluster.add_node("node_a")
    cluster.add_node("node_b")
    for goal in ["create a shared index", "research task routing", "update the index"]:
        response = cluster.submit(goal)
        print(f"  {response.result.get('node')}: goal={goal!r} status={response.status} chosen={response.result.get('chosen', {})}")

def main() -> None:
    run_single_runtime()
    run_cluster()

if __name__ == "__main__":
    main()
