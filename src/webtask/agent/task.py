"""Task definitions and execution tracking."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .planner.planner_session import PlannerSession
    from .worker.worker_session import WorkerSession
    from .verifier.verifier_session import VerifierSession

from .subtask_queue import SubtaskQueue


@dataclass
class Task:
    """Basic task definition - input to TaskExecutor."""

    description: str
    resources: Dict[str, str] = field(default_factory=dict)


@dataclass
class TaskExecution:
    """Record of task execution - output from TaskExecutor.

    Contains the original task, execution history, subtask queue state, and completion status.
    """

    task: Task
    history: List[Union["PlannerSession", "WorkerSession", "VerifierSession"]] = field(
        default_factory=list
    )
    subtask_queue: SubtaskQueue = field(default_factory=SubtaskQueue)
    complete: bool = False

    def add_session(
        self, session: Union["PlannerSession", "WorkerSession", "VerifierSession"]
    ) -> None:
        """Add a session to execution history."""
        self.history.append(session)

    def mark_complete(self) -> None:
        """Mark task as complete."""
        self.complete = True

    def __str__(self) -> str:
        """Return formatted string representation for debugging."""
        lines = []
        lines.append("=" * 80)
        lines.append("TASK EXECUTION")
        lines.append("=" * 80)
        lines.append(f"Task: {self.task.description}")
        lines.append(f"Complete: {self.complete}")
        lines.append("")

        # Show subtask queue
        lines.append("SUBTASK QUEUE:")
        lines.append("-" * 80)
        if len(self.subtask_queue) == 0:
            lines.append("No subtasks yet")
        else:
            for line in str(self.subtask_queue).split("\n"):
                lines.append(f"  {line}")
        lines.append("")

        # Show execution history
        if self.history:
            lines.append("EXECUTION HISTORY:")
            lines.append("-" * 80)
            for i, session in enumerate(self.history, 1):
                lines.append(f"\nSession {i}:")
                # Indent each line of the session
                for line in str(session).split("\n"):
                    lines.append(f"  {line}")
                lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)
