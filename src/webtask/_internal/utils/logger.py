"""Logger utility for webtask."""

import logging
import sys
import os

# Configure root logger once
_configured = False


def _configure_logging():
    """Configure root logger once."""
    global _configured
    if _configured:
        return

    # Get root logger for webtask
    root_logger = logging.getLogger("webtask")

    # Only configure if no handlers exist
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    # Set log level from environment (default: INFO)
    log_level = os.getenv("WEBTASK_LOG_LEVEL", "INFO").upper()
    try:
        root_logger.setLevel(getattr(logging, log_level))
    except AttributeError:
        # Invalid log level, default to INFO
        root_logger.setLevel(logging.INFO)

    # Prevent propagation to avoid duplicate logs
    root_logger.propagate = False

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    """
    # Configure root logger once
    _configure_logging()

    # Return logger (will inherit from root)
    return logging.getLogger(name)
