"""Tests for storage module."""


from ncp.storage.cache import CacheStore
from ncp.storage.entity_store import EntityStore
from ncp.storage.snapshot import SnapshotStore
from ncp.storage.storage import Storage


class TestCacheStore:
    def test_get_set(self):
        cache = CacheStore()
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_ttl_expiry(self):
        cache = CacheStore(default_ttl=0.001)
        cache.set("key", "value")
        import time
        time.sleep(0.01)
        assert cache.get("key") is None

    def test_invalidate(self):
        cache = CacheStore()
        cache.set("key", "value")
        cache.invalidate("key")
        assert cache.get("key") is None


class TestEntityStore:
    def test_store_retrieve(self):
        store = EntityStore()
        store.store("key", {"data": "value"})
        assert store.retrieve("key") == {"data": "value"}

    def test_version(self):
        store = EntityStore()
        store.store("key", "v1")
        store.store("key", "v2")
        assert store.get_version("key") == 2


class TestSnapshotStore:
    def test_create_restore(self):
        ss = SnapshotStore()
        ss.create("test", {"data": "snapshot"})
        restored = ss.restore("test")
        assert restored == {"data": "snapshot"}

    def test_list_snapshots(self):
        ss = SnapshotStore()
        ss.create("snap1", {})
        ss.create("snap2", {})
        assert len(ss.list_snapshots()) == 2


class TestStorage:
    def test_save_load(self):
        s = Storage()
        s.save("key", {"data": "test"})
        loaded = s.load("key")
        assert loaded == {"data": "test"}

    def test_delete(self):
        s = Storage()
        s.save("key", "value")
        s.delete("key")
        assert s.load("key") is None

    def test_list_keys(self):
        s = Storage()
        s.save("prefix_key1", "v1")
        s.save("prefix_key2", "v2")
        s.save("other", "v3")
        keys = s.list_keys("prefix")
        assert len(keys) == 2
