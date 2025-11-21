"""Custom exceptions for webtask."""


class WebtaskError(Exception):
    """Base exception for all webtask errors."""

    pass


class TaskAbortedError(WebtaskError):
    """Raised when a task is aborted by the agent."""

    def __init__(self, message: str, feedback: str | None = None):
        super().__init__(message)
        self.feedback = feedback


class VerificationAbortedError(WebtaskError):
    """Raised when a verification is aborted by the agent."""

    def __init__(self, message: str, feedback: str | None = None):
        super().__init__(message)
        self.feedback = feedback


class ExtractionAbortedError(WebtaskError):
    """Raised when an extraction is aborted by the agent."""

    def __init__(self, message: str, feedback: str | None = None):
        super().__init__(message)
        self.feedback = feedback
