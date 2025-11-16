"""VerifierSession - tracks one verifier.run() execution with conversation history."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class VerifierDecision(str, Enum):
    """Verifier decision about task completion."""

    COMPLETE_TASK = "complete_task"
    REQUEST_CORRECTION = "request_correction"
    ABORT_TASK = "abort_task"


@dataclass
class VerifierSession:
    """Verifier session with conversation history."""

    task_description: str
    decision: VerifierDecision
    feedback: str
    start_time: datetime
    end_time: datetime
    max_steps: int = 5
    steps_used: int = 0
    summary: str = ""

    def __str__(self) -> str:
        """Simple string representation showing basic info."""
        return f"VerifierSession(steps={self.steps_used}/{self.max_steps}, decision={self.decision})"
