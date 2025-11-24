"""Custom exceptions for webtask."""

# Re-export from dodo so users can do: from webtask import TaskAbortedError
from dodo import TaskAbortedError


class WebtaskError(Exception):
    """Base exception for webtask-specific errors."""

    pass


__all__ = ["WebtaskError", "TaskAbortedError"]
