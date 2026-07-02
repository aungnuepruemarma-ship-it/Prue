"""Tests for router module."""


from ncp.core.entities import Task
from ncp.interfaces.capability import CapabilityCard
from ncp.router.history import RoutingDecision, RoutingHistory
from ncp.router.policy import RoutingPolicy
from ncp.router.registry import CapabilityRegistry


class TestCapabilityRegistry:
    def test_register_get(self):
        reg = CapabilityRegistry()
        card = CapabilityCard(name="test", type="llm")
        reg.register(card)
        assert reg.get("test") == card

    def test_list_all(self):
        reg = CapabilityRegistry()
        reg.register(CapabilityCard(name="a", type="llm"))
        reg.register(CapabilityCard(name="b", type="tool"))
        assert len(reg.list_all()) == 2

    def test_find_by_type(self):
        reg = CapabilityRegistry()
        reg.register(CapabilityCard(name="test", type="llm"))
        found = reg.find_by_type("llm")
        assert len(found) == 1


class TestRoutingHistory:
    def test_record(self):
        h = RoutingHistory()
        h.record(RoutingDecision(capability_name="test", success=True))
        assert len(h.decisions) == 1

    def test_success_rate(self):
        h = RoutingHistory()
        h.record(RoutingDecision(capability_name="cap1", success=True))
        h.record(RoutingDecision(capability_name="cap1", success=True))
        h.record(RoutingDecision(capability_name="cap1", success=False))
        rate = h.get_success_rate("cap1")
        assert abs(rate - 0.667) < 0.01

    def test_empty_success_rate(self):
        h = RoutingHistory()
        rate = h.get_success_rate("unknown")
        assert rate == 0.5  # Neutral default


class TestRoutingPolicy:
    def test_select_single(self):
        p = RoutingPolicy()
        cap = CapabilityCard(name="only", type="llm")
        selected = p.select(Task(), [cap])
        assert selected.name == "only"

    def test_select_best(self):
        p = RoutingPolicy()
        caps = [
            CapabilityCard(name="fast", type="llm", latency_ms=100, reliability=0.9),
            CapabilityCard(name="slow", type="llm", latency_ms=1000, reliability=0.5),
        ]
        selected = p.select(Task(), caps)
        assert selected.name == "fast"
