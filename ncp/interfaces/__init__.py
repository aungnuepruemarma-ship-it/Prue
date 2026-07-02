"""NCP Interfaces - Abstract base classes for all subsystems."""

from ncp.interfaces.capability import CapabilityCard, CapabilityInterface
from ncp.interfaces.constraints import ConstraintInterface
from ncp.interfaces.executor import ExecutorInterface
from ncp.interfaces.memory import MemoryInterface
from ncp.interfaces.planner import PlannerInterface
from ncp.interfaces.research import ResearchInterface
from ncp.interfaces.router import RouterInterface
from ncp.interfaces.simulator import SimulatorInterface
from ncp.interfaces.storage import StorageInterface

__all__ = [
    "PlannerInterface",
    "RouterInterface",
    "ExecutorInterface",
    "MemoryInterface",
    "StorageInterface",
    "ConstraintInterface",
    "SimulatorInterface",
    "ResearchInterface",
    "CapabilityInterface",
    "CapabilityCard",
]
