from ncp.api.protocol import TaskRequest, handle_kernel_request, handle_request
from ncp.core.runtime import Runtime, build_default_universe
from ncp.distributed.cluster import Cluster
from ncp.kernel.kernel import Kernel
from ncp.utils.runtime_config import Config


def test_handle_request_drives_runtime(tmp_path):
    runtime = Runtime(build_default_universe(), config=Config(output_dir=str(tmp_path / "out")))
    response = handle_request(runtime, TaskRequest(task_id="t1", goal="create a new concept"))
    assert response.task_id == "t1"
    assert response.status == "accepted"
    assert response.result["chosen"]["name"]


def test_handle_kernel_request_drives_kernel(tmp_path):
    kernel = Kernel(storage_root=str(tmp_path / "storage"))
    try:
        response = handle_kernel_request(kernel, TaskRequest(task_id="t2", goal="update the index"))
        assert response.task_id == "t2"
        assert response.status == "completed"
        assert response.result["verified"]
        assert response.result["nodes"] >= 1
        assert response.result["run_id"] in kernel.world.jobs
    finally:
        kernel.shutdown()


def test_cluster_round_robin(tmp_path):
    cluster = Cluster()
    cluster.add_node("a", output_dir=str(tmp_path / "a"))
    cluster.add_node("b", output_dir=str(tmp_path / "b"))
    try:
        nodes = [cluster.submit(f"update goal {i}").result["node"] for i in range(4)]
        assert nodes == ["a", "b", "a", "b"]
    finally:
        cluster.shutdown()


def test_cluster_skips_offline_nodes(tmp_path):
    cluster = Cluster()
    cluster.add_node("a", output_dir=str(tmp_path / "a"))
    node_b = cluster.add_node("b", output_dir=str(tmp_path / "b"))
    node_b.status = "offline"
    try:
        nodes = {cluster.submit("update something").result["node"] for _ in range(3)}
        assert nodes == {"a"}
    finally:
        cluster.shutdown()


def test_empty_cluster_reports_no_nodes():
    assert Cluster().submit("anything").status == "no_nodes"


def test_cluster_uses_kernel_per_node(tmp_path):
    cluster = Cluster()
    node = cluster.add_node("a", output_dir=str(tmp_path / "a"))
    try:
        assert isinstance(node.kernel, Kernel)
        response = cluster.submit("update the index")
        assert response.result["node"] == "a"
        assert response.result["run_id"] in node.kernel.world.jobs
    finally:
        cluster.shutdown()
