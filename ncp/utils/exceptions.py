"""Custom exceptions for NCP."""


class NCPError(Exception):
    """Base exception for NCP."""
    pass


class ValidationError(NCPError):
    """Raised when validation fails."""
    pass


class ExecutionError(NCPError):
    """Raised when task execution fails."""
    pass


class StorageError(NCPError):
    """Raised when storage operation fails."""
    pass


class MemoryError(NCPError):
    """Raised when memory operation fails."""
    pass


class RoutingError(NCPError):
    """Raised when routing fails."""
    pass


class PlanningError(NCPError):
    """Raised when planning fails."""
    pass


class ConstraintError(NCPError):
    """Raised when constraint check fails."""
    pass


class SimulationError(NCPError):
    """Raised when simulation fails."""
    pass


class ResearchError(NCPError):
    """Raised when research operation fails."""
    pass


class SkillError(NCPError):
    """Raised when skill operation fails."""
    pass
