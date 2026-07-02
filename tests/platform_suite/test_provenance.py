"""Tests for provenance module."""


from ncp.provenance.audit import AuditTrail
from ncp.provenance.confidence import ConfidenceModel
from ncp.provenance.evidence import Evidence
from ncp.provenance.lineage import LineageTracker
from ncp.provenance.source import Source


class TestSource:
    def test_creation(self):
        s = Source(type="llm", identifier="gpt-4")
        assert s.type == "llm"


class TestEvidence:
    def test_creation(self):
        e = Evidence(type="observation", data="test data")
        assert e.type == "observation"


class TestConfidenceModel:
    def test_compute(self):
        c = ConfidenceModel(base_confidence=0.8, source_reliability=0.9,
                           evidence_strength=0.7, verification_count=2)
        score = c.compute()
        assert score > 0


class TestAuditTrail:
    def test_log(self):
        at = AuditTrail()
        at.log("test_action", actor="user")
        assert at.entry_count == 1

    def test_get_entries(self):
        at = AuditTrail()
        at.log("action1")
        at.log("action2")
        entries = at.get_entries(action="action1")
        assert len(entries) == 1


class TestLineageTracker:
    def test_record_get(self):
        lt = LineageTracker()
        import uuid
        item_id = uuid.uuid4()
        lt.record(item_id, operation="created")
        assert item_id in lt.entries
