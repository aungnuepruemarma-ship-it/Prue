import pytest

from ncp.execution.compiler import DAGCompiler, split_goal
from ncp.execution.dag import ExecutionDAG
from ncp.execution.dag_executor import DAGExecutor
from ncp.execution.node import DAGNode


def test_split_goal_sequential_and_parallel():
    parts = split_goal("research routing, then build the index and write the report")
    assert parts[0] == ("research routing", [])
    assert parts[1][0] == "build the index"
    assert parts[2][0] == "write the report"
    assert parts[1][1] == [0] and parts[2][1] == [0], "both branches depend on the first segment"


def test_compiler_produces_dependent_nodes():
    dag = DAGCompiler().compile("research routing, then build the index")
    order = dag.topological_order()
    assert len(order) >= 3
    research_nodes = [n for n in order if n.goal == "research routing"]
    build_nodes = [n for n in order if n.goal == "build the index"]
    assert research_nodes and build_nodes
    assert build_nodes[0].depends_on, "second segment must depend on the first"


def test_topological_order_detects_cycles():
    dag = ExecutionDAG(goal="cycle")
    a = dag.add_node(DAGNode(name="a", goal="a"))
    b = dag.add_node(DAGNode(name="b", goal="b"))
    dag.add_dependency(a.id, b.id)
    dag.add_dependency(b.id, a.id)
    with pytest.raises(ValueError):
        dag.topological_order()


def test_executor_skips_dependents_of_failures():
    dag = ExecutionDAG(goal="failure path")
    first = dag.add_node(DAGNode(name="first", goal="boom"))
    second = dag.add_node(DAGNode(name="second", goal="after"))
    dag.add_dependency(second.id, first.id)

    def runner(node):
        if node.goal == "boom":
            raise RuntimeError("provider exploded")
        return {"status": "success"}

    checkpoints = []
    DAGExecutor(node_runner=runner, checkpoint_hook=lambda d: checkpoints.append(len(d.nodes))).run(dag)
    assert dag.nodes[first.id].status == "failed"
    assert dag.nodes[second.id].status == "skipped"
    assert checkpoints, "checkpoint hook must fire"


def test_dag_round_trips_through_dict():
    dag = DAGCompiler().compile("update the index")
    restored = ExecutionDAG.from_dict(dag.to_dict())
    assert restored.run_id == dag.run_id
    assert {n.id for n in restored.nodes.values()} == {n.id for n in dag.nodes.values()}
