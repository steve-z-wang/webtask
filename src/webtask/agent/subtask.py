"""Subtask - metadata for one subtask."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class SubtaskStatus(str, Enum):
    """Status of a subtask."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class Subtask:
    """
    Subtask metadata.

    Created by Scheduler, executed by Worker, verified by Verifier.
    History is tracked at Task level (linear).
    """

    description: str
    """Goal for this subtask."""

    status: SubtaskStatus = SubtaskStatus.PENDING
    """Current status of the subtask."""

    failure_reason: Optional[str] = None
    """Reason for failure (if status is FAILED)."""

    created_at: datetime = field(default_factory=datetime.now)
    """When this subtask was created."""

    completed_at: Optional[datetime] = None
    """When this subtask was marked complete or failed."""

    def mark_in_progress(self) -> None:
        """Mark subtask as in progress."""
        self.status = SubtaskStatus.IN_PROGRESS

    def mark_complete(self) -> None:
        """Mark subtask as complete."""
        self.status = SubtaskStatus.COMPLETE
        self.completed_at = datetime.now()

    def mark_failed(self, reason: str) -> None:
        """Mark subtask as failed.

        Args:
            reason: Reason why the subtask failed
        """
        self.status = SubtaskStatus.FAILED
        self.failure_reason = reason
        self.completed_at = datetime.now()

    def mark_canceled(self) -> None:
        """Mark subtask as canceled."""
        self.status = SubtaskStatus.CANCELED
        self.completed_at = datetime.now()

    @property
    def is_complete(self) -> bool:
        """Check if subtask is complete."""
        return self.status == SubtaskStatus.COMPLETE

    @property
    def is_pending(self) -> bool:
        """Check if subtask is pending."""
        return self.status == SubtaskStatus.PENDING

    @property
    def is_in_progress(self) -> bool:
        """Check if subtask is in progress."""
        return self.status == SubtaskStatus.IN_PROGRESS

    def __str__(self) -> str:
        """Format subtask for human-readable output."""
        status_emoji = {
            SubtaskStatus.PENDING: "⏳",
            SubtaskStatus.IN_PROGRESS: "🔄",
            SubtaskStatus.COMPLETE: "✅",
            SubtaskStatus.FAILED: "❌",
            SubtaskStatus.CANCELED: "🚫",
        }
        emoji = status_emoji.get(self.status, "")
        result = f"{emoji} {self.description} [{self.status.value}]"
        if self.status == SubtaskStatus.FAILED and self.failure_reason:
            result += f" - {self.failure_reason}"
        return result
