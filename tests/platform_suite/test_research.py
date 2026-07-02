"""Tests for research module."""


from ncp.research.discovery import DiscoveryEngine
from ncp.research.hypothesis import Hypothesis
from ncp.research.verification import VerificationEngine


class TestHypothesis:
    def test_creation(self):
        h = Hypothesis(statement="Test hypothesis", confidence=0.8)
        assert h.statement == "Test hypothesis"
        assert h.status == "pending"


class TestVerificationEngine:
    def test_verify_confident(self):
        v = VerificationEngine()
        h = Hypothesis(statement="test", confidence=0.8, evidence=["data"])
        assert v.verify(h) is True
        assert h.status == "verified"

    def test_verify_low_confidence(self):
        v = VerificationEngine()
        h = Hypothesis(statement="test", confidence=0.3)
        assert v.verify(h) is False

    def test_verify_no_evidence(self):
        v = VerificationEngine()
        h = Hypothesis(statement="test", confidence=0.9, evidence=[])
        assert v.verify(h) is False


class TestDiscoveryEngine:
    def test_generate_hypothesis(self):
        de = DiscoveryEngine(verification=VerificationEngine())
        h = de.generate_hypothesis("observation", {"context": "data"})
        assert h.statement == "Hypothesis about: observation"

    def test_run_experiment(self):
        de = DiscoveryEngine(verification=VerificationEngine())
        h = Hypothesis(statement="test")
        exp = de.run_experiment(h)
        assert exp.status == "completed"

    def test_discover(self):
        de = DiscoveryEngine(verification=VerificationEngine())
        h = Hypothesis(statement="test", confidence=0.8, evidence=["data"])
        de.hypotheses.append(h)
        discoveries = de.discover({})
        assert len(discoveries) >= 1
