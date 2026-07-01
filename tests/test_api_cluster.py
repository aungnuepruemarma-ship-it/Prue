from ncp.api.protocol import TaskRequest, handle_request
from ncp.core.runtime import Runtime, build_default_universe
from ncp.distributed.cluster import Cluster
from ncp.utils.config import Config


def test_handle_request_drives_runtime(tmp_path):
    runtime = Runtime(build_default_universe(), config=Config(output_dir=str(tmp_path / "out")))
    response = handle_request(runtime, TaskRequest(task_id="t1", goal="create a new concept"))
    assert response.task_id == "t1"
    assert response.status == "accepted"
    assert response.result["chosen"]["name"]


def test_cluster_round_robin(tmp_path):
    cluster = Cluster()
    cluster.add_node("a", output_dir=str(tmp_path / "a"))
    cluster.add_node("b", output_dir=str(tmp_path / "b"))
    nodes = [cluster.submit(f"update goal {i}").result["node"] for i in range(4)]
    assert nodes == ["a", "b", "a", "b"]


def test_cluster_skips_offline_nodes(tmp_path):
    cluster = Cluster()
    cluster.add_node("a", output_dir=str(tmp_path / "a"))
    node_b = cluster.add_node("b", output_dir=str(tmp_path / "b"))
    node_b.status = "offline"
    nodes = {cluster.submit("update something").result["node"] for _ in range(3)}
    assert nodes == {"a"}


def test_empty_cluster_reports_no_nodes():
    assert Cluster().submit("anything").status == "no_nodes"
