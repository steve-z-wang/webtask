"""Custom exceptions for webtask."""


class WebtaskError(Exception):
    """Base exception for all webtask errors."""

    pass


class TaskAbortedError(WebtaskError):
    """Raised when a task (do/verify/extract) is aborted by the agent."""

    def __init__(self, message: str, feedback: str | None = None):
        super().__init__(message)
        self.feedback = feedback
