"""Version utilities."""

from typing import NamedTuple


class Version(NamedTuple):
    """Semantic version."""
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def parse_version(version_str: str) -> Version:
    """Parse version string into Version tuple."""
    parts = version_str.split(".")
    return Version(
        major=int(parts[0]) if len(parts) > 0 else 0,
        minor=int(parts[1]) if len(parts) > 1 else 0,
        patch=int(parts[2]) if len(parts) > 2 else 0,
    )
