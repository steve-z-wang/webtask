"""Subtask - metadata for one subtask."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class SubtaskStatus(str, Enum):
    """Status of a subtask."""

    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    REQUESTED_RESCHEDULE = "requested_reschedule"


@dataclass
class Subtask:
    """
    Subtask metadata.

    Created by Manager, executed by Worker, verified by Verifier.
    History is tracked at Task level (linear).
    """

    description: str
    """Goal for this subtask."""

    status: SubtaskStatus = SubtaskStatus.ASSIGNED
    """Current status of the subtask."""

    feedback: Optional[str] = None
    """Feedback provided when marked complete or requested_reschedule."""

    created_at: datetime = field(default_factory=datetime.now)
    """When this subtask was created."""

    completed_at: Optional[datetime] = None
    """When this subtask was marked complete or requested_reschedule."""

    def mark_in_progress(self) -> None:
        """Mark subtask as in progress."""
        self.status = SubtaskStatus.IN_PROGRESS

    def mark_complete(self, feedback: str) -> None:
        """Mark subtask as complete.

        Args:
            feedback: Feedback about what was accomplished
        """
        self.status = SubtaskStatus.COMPLETE
        self.feedback = feedback
        self.completed_at = datetime.now()

    def mark_requested_reschedule(self, feedback: str) -> None:
        """Mark subtask as requesting reschedule from Manager.

        Args:
            feedback: Explanation of why reschedule is needed
        """
        self.status = SubtaskStatus.REQUESTED_RESCHEDULE
        self.feedback = feedback
        self.completed_at = datetime.now()

    @property
    def is_complete(self) -> bool:
        """Check if subtask is complete."""
        return self.status == SubtaskStatus.COMPLETE

    @property
    def is_assigned(self) -> bool:
        """Check if subtask is assigned."""
        return self.status == SubtaskStatus.ASSIGNED

    @property
    def is_in_progress(self) -> bool:
        """Check if subtask is in progress."""
        return self.status == SubtaskStatus.IN_PROGRESS

    @property
    def is_requested_reschedule(self) -> bool:
        """Check if subtask has requested reschedule."""
        return self.status == SubtaskStatus.REQUESTED_RESCHEDULE

    def __str__(self) -> str:
        """Format subtask for human-readable output."""
        status_emoji = {
            SubtaskStatus.ASSIGNED: "📋",
            SubtaskStatus.IN_PROGRESS: "🔄",
            SubtaskStatus.COMPLETE: "✅",
            SubtaskStatus.REQUESTED_RESCHEDULE: "⚠️",
        }
        emoji = status_emoji.get(self.status, "")
        result = f"{emoji} {self.description} [{self.status.value}]"
        if self.feedback:
            result += f" - {self.feedback}"
        return result
