"""Tests for compression module."""


from ncp.compression.decoder import Decoder
from ncp.compression.delta import DeltaCompressor
from ncp.compression.dictionary import CompressionDictionary
from ncp.compression.encoder import Encoder
from ncp.compression.manager import CompressionManager


class TestCompressionDictionary:
    def test_add_get(self):
        d = CompressionDictionary()
        d.add_motif("test", "pattern")
        assert d.size() == 1


class TestEncoderDecoder:
    def test_roundtrip(self):
        d = CompressionDictionary()
        d.add_motif("hello", "hello world")
        enc = Encoder(d)
        dec = Decoder(d)
        encoded = enc.encode("hello world test")
        decoded = dec.decode(encoded)
        assert "test" in decoded


class TestCompressionManager:
    def test_compress_string(self):
        cm = CompressionManager()
        result = cm.compress("test data", mode="dictionary")
        assert "data" in result
        assert "original_size" in result

    def test_compress_dict(self):
        cm = CompressionManager()
        result = cm.compress({"key": "value"})
        assert "data" in result

    def test_stats(self):
        cm = CompressionManager()
        cm.compress("test")
        stats = cm.get_stats()
        assert stats["total_compressions"] == 1


class TestDeltaCompressor:
    def test_compute_delta(self):
        dc = DeltaCompressor()
        dc.set_baseline({"a": 1, "b": 2})
        deltas = dc.compute_delta({"a": 1, "b": 3})
        assert len(deltas) == 1
