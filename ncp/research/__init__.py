"""NCP Research — discovery loop (platform) + runtime findings (reference)."""

from .discovery import DiscoveryEngine
from .engine import ResearchEngine, ResearchFinding, is_research_goal
from .experiment import Experiment
from .hypothesis import Hypothesis
from .manager import ResearchManager
from .verification import VerificationEngine

__all__ = [
    "ResearchEngine",
    "ResearchFinding",
    "is_research_goal",
    "ResearchManager",
    "DiscoveryEngine",
    "Hypothesis",
    "Experiment",
    "VerificationEngine",
]
