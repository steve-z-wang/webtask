
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class SubtaskStatus(str, Enum):

    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    REQUESTED_RESCHEDULE = "requested_reschedule"


@dataclass
class Subtask:

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
        self.status = SubtaskStatus.IN_PROGRESS

    def mark_complete(self, feedback: str) -> None:
        self.status = SubtaskStatus.COMPLETE
        self.feedback = feedback
        self.completed_at = datetime.now()

    def mark_requested_reschedule(self, feedback: str) -> None:
        self.status = SubtaskStatus.REQUESTED_RESCHEDULE
        self.feedback = feedback
        self.completed_at = datetime.now()

    @property
    def is_complete(self) -> bool:
        return self.status == SubtaskStatus.COMPLETE

    @property
    def is_assigned(self) -> bool:
        return self.status == SubtaskStatus.ASSIGNED

    @property
    def is_in_progress(self) -> bool:
        return self.status == SubtaskStatus.IN_PROGRESS

    @property
    def is_requested_reschedule(self) -> bool:
        return self.status == SubtaskStatus.REQUESTED_RESCHEDULE

    def __str__(self) -> str:
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
