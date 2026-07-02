"""Logging utilities.

Every module uses: logger = get_logger(__name__)
"""

import logging
import sys

LOG_LEVELS = {
    "TRACE": 5,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

# Add TRACE level
logging.addLevelName(5, "TRACE")


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module.

    Usage:
        logger = get_logger(__name__)
        logger.info("message")
        logger.debug("debug info")
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
