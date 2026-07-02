from ncp.storage.relational_store import RelationalStore
from ncp.storage.storage_manager import SUBDIRS, StorageManager


def test_storage_manager_creates_spec_layout(tmp_path):
    StorageManager(str(tmp_path / "storage"))
    for sub in SUBDIRS:
        assert (tmp_path / "storage" / sub).is_dir(), sub


def test_relational_store_round_trip(tmp_path):
    store = RelationalStore(str(tmp_path / "db" / "test.db"))
    store.insert("tasks", {"name": "t1", "cost": 1.5, "meta": {"k": [1, 2]}})
    store.insert("tasks", {"name": "t2", "cost": 0.5, "meta": {}})
    rows = store.query("tasks", {"name": "t1"})
    assert len(rows) == 1
    assert rows[0]["meta"] == {"k": [1, 2]}
    assert store.count("tasks") == 2
    assert store.query("missing_table") == []


def test_artifact_store_save_and_list(tmp_path):
    manager = StorageManager(str(tmp_path / "storage"))
    manager.artifacts.save("report.md", "# hello", category="reports")
    assert manager.artifacts.load("report.md", category="reports") == b"# hello"
    assert manager.artifacts.list_artifacts("reports") == ["reports/report.md"]


def test_checkpoint_store_latest(tmp_path):
    manager = StorageManager(str(tmp_path / "storage"))
    manager.checkpoints.save("run1", {"step": 1})
    manager.checkpoints.save("run1", {"step": 2})
    latest = manager.checkpoints.load_latest("run1")
    assert latest["payload"]["step"] == 2
    assert manager.checkpoints.list_runs() == ["run1"]


def test_backup_round_trip(tmp_path):
    manager = StorageManager(str(tmp_path / "storage"))
    manager.save_document("registry", "providers", {"a": 1})
    backup = manager.backups.create_backup("test")
    assert backup.exists()
    restore_dir = tmp_path / "restored"
    manager.backups.restore(backup.name, str(restore_dir))
    assert (restore_dir / "registry" / "providers.json").exists()


def test_document_round_trip(tmp_path):
    manager = StorageManager(str(tmp_path / "storage"))
    manager.save_document("world_state", "world", {"facts": {"x": "1"}})
    assert manager.load_document("world_state", "world") == {"facts": {"x": "1"}}
    assert manager.load_document("world_state", "missing") is None
