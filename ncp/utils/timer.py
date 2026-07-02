"""Timing utilities."""

import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable

from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Timer:
    """Context manager for timing code blocks."""
    name: str = ""
    _start: float = field(default=0.0, repr=False)
    _elapsed: float = field(default=0.0, repr=False)

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        self._elapsed = time.perf_counter() - self._start
        if self.name:
            logger.debug("%s took %.3f ms", self.name, self._elapsed * 1000)

    @property
    def elapsed_ms(self) -> float:
        if self._elapsed:
            return self._elapsed * 1000
        return (time.perf_counter() - self._start) * 1000


def timed(func: Callable) -> Callable:
    """Decorator to time function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug("%s took %.3f ms", func.__name__, elapsed)
        return result
    return wrapper
