"""TaskExecution model for planner-worker-verifier architecture."""

from dataclasses import dataclass, field
from typing import Dict, List, Union
from .subtask_queue import SubtaskQueue


@dataclass
class TaskExecution:
    """Record of task execution with state and history."""

    description: str
    resources: Dict[str, str] = field(default_factory=dict)
    history: List[Union["PlannerSession", "WorkerSession", "VerifierSession"]] = field(default_factory=list)
    subtask_queue: SubtaskQueue = field(default_factory=SubtaskQueue)
    complete: bool = False  # Track task completion status

    def add_session(self, session: Union["PlannerSession", "WorkerSession", "VerifierSession"]) -> None:
        self.history.append(session)

    def mark_complete(self) -> None:
        """Mark task as complete."""
        self.complete = True

    def __str__(self) -> str:
        """Return formatted string representation."""
        lines = []
        lines.append("=" * 80)
        lines.append("TASK EXECUTION")
        lines.append("=" * 80)
        lines.append(f"\nTask: {self.description}")
        lines.append(f"Sessions: {len(self.history)}")
        lines.append(f"Subtasks: {len(self.subtask_queue.subtasks)}")

        lines.append("\n" + "-" * 80)
        lines.append("SUBTASKS:")
        lines.append("-" * 80)
        lines.append(str(self.subtask_queue))

        lines.append("\n" + "-" * 80)
        lines.append("EXECUTION HISTORY:")
        lines.append("-" * 80)
        for i, session in enumerate(self.history, 1):
            lines.append(f"\n{i}. {session}")

        lines.append("\n" + "=" * 80)
        return "\n".join(lines)

    def print_summary(self) -> None:
        """Print a formatted summary of the task execution."""
        print(self)
