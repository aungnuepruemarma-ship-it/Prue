"""NCP Router - Capability selection and routing."""

from ncp.router.history import RoutingHistory
from ncp.router.policy import RoutingPolicy
from ncp.router.registry import CapabilityRegistry
from ncp.router.router import Router

__all__ = ["Router", "CapabilityRegistry", "RoutingHistory", "RoutingPolicy"]
