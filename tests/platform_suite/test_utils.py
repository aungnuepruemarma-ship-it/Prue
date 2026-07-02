"""Tests for utilities."""


from ncp.utils.config import Config
from ncp.utils.hashing import hash_dict, hash_string
from ncp.utils.ids import generate_id
from ncp.utils.timer import Timer
from ncp.utils.version import parse_version


class TestConfig:
    def test_config_get_set(self):
        c = Config()
        c.set("test.key", "value")
        assert c.get("test.key") == "value"

    def test_config_default(self):
        c = Config()
        assert c.get("missing", "default") == "default"

    def test_config_merge(self):
        c = Config()
        c.merge({"a": {"b": 1}})
        assert c.get("a.b") == 1


class TestHashing:
    def test_hash_string(self):
        h = hash_string("test")
        assert len(h) == 64  # SHA-256 hex

    def test_hash_dict(self):
        h1 = hash_dict({"a": 1, "b": 2})
        h2 = hash_dict({"b": 2, "a": 1})
        assert h1 == h2  # Order independent


class TestIds:
    def test_generate_id(self):
        id1 = generate_id()
        id2 = generate_id()
        assert id1 != id2


class TestTimer:
    def test_timer(self):
        with Timer() as t:
            pass
        assert t.elapsed_ms >= 0


class TestVersion:
    def test_parse_version(self):
        v = parse_version("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
