"""TaskExecution - execution history for one task."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Union, TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from .worker.worker_session import WorkerSession
    from .verifier.verifier_session import VerifierSession


class TaskStatus(str, Enum):
    """Task execution status."""

    COMPLETE = "complete_task"
    ABORTED = "abort_task"


@dataclass
class TaskExecution:
    """Execution history for one task - pure data container."""

    task_description: str
    sessions: List[Union["WorkerSession", "VerifierSession"]]
    status: TaskStatus
    created_at: datetime
    completed_at: datetime

    @property
    def summary(self) -> str:
        """Generate comprehensive summary of task execution."""
        lines = ["=" * 80]
        lines.append("TASK EXECUTION SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Task: {self.task_description}")
        lines.append(f"Status: {self.status.value}")

        duration = (self.completed_at - self.created_at).total_seconds()
        lines.append(
            f"Duration: {duration:.2f}s ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {self.completed_at.strftime('%H:%M:%S')})"
        )
        lines.append(f"Total Sessions: {len(self.sessions)}")
        lines.append("")

        # Count session types
        from .worker.worker_session import WorkerSession
        from .verifier.verifier_session import VerifierSession

        worker_count = sum(1 for s in self.sessions if isinstance(s, WorkerSession))
        verifier_count = sum(1 for s in self.sessions if isinstance(s, VerifierSession))
        lines.append(f"  - Worker sessions: {worker_count}")
        lines.append(f"  - Verifier sessions: {verifier_count}")
        lines.append("")

        # Show each session summary
        for i, session in enumerate(self.sessions, 1):
            lines.append(f"{'─' * 80}")
            if isinstance(session, WorkerSession):
                lines.append(f"Session {i}: WorkerSession")
                lines.append(f"  Steps: {session.steps_used}/{session.max_steps}")
                lines.append(f"  End reason: {session.end_reason}")
            else:
                lines.append(f"Session {i}: VerifierSession")
                lines.append(f"  Steps: {session.steps_used}/{session.max_steps}")
                lines.append(f"  Decision: {session.decision}")
                if session.feedback:
                    lines.append(f"  Feedback: {session.feedback}")

        lines.append("=" * 80)
        return "\n".join(lines)

    def __str__(self) -> str:
        """Simple string representation showing basic info."""
        return f"TaskExecution(task='{self.task_description}', status={self.status.value}, sessions={len(self.sessions)})"


@dataclass
class TaskResult:
    """User-facing result with output and feedback."""

    status: TaskStatus
    output: Optional[Any] = None  # Structured data from set_output()
    feedback: Optional[str] = None  # Human summary from verifier
    execution: Optional[TaskExecution] = None  # Full execution history for debugging

    @property
    def is_complete(self) -> bool:
        """Check if task completed successfully."""
        return self.status == TaskStatus.COMPLETE
