"""Tests for interfaces."""

from abc import ABC

from ncp.interfaces.capability import CapabilityCard
from ncp.interfaces.constraints import ConstraintInterface
from ncp.interfaces.executor import ExecutorInterface
from ncp.interfaces.memory import MemoryInterface
from ncp.interfaces.planner import PlannerInterface
from ncp.interfaces.research import ResearchInterface
from ncp.interfaces.router import RouterInterface
from ncp.interfaces.simulator import SimulatorInterface
from ncp.interfaces.storage import StorageInterface


class TestInterfaces:
    def test_planner_is_abc(self):
        assert issubclass(PlannerInterface, ABC)

    def test_router_is_abc(self):
        assert issubclass(RouterInterface, ABC)

    def test_executor_is_abc(self):
        assert issubclass(ExecutorInterface, ABC)

    def test_memory_is_abc(self):
        assert issubclass(MemoryInterface, ABC)

    def test_storage_is_abc(self):
        assert issubclass(StorageInterface, ABC)

    def test_constraints_is_abc(self):
        assert issubclass(ConstraintInterface, ABC)

    def test_simulator_is_abc(self):
        assert issubclass(SimulatorInterface, ABC)

    def test_research_is_abc(self):
        assert issubclass(ResearchInterface, ABC)


class TestCapabilityCard:
    def test_card_creation(self):
        card = CapabilityCard(
            name="test",
            type="llm",
            latency_ms=100,
            cost_per_call=0.01,
            reliability=0.95,
        )
        assert card.name == "test"
        assert card.reliability == 0.95
