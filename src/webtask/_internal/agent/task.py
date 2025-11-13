
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Union, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .manager.manager_session import ManagerSession
    from .subtask_execution import SubtaskExecution

from .subtask_queue import SubtaskQueue


class TaskStatus(str, Enum):

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"


@dataclass
class Task:

    description: str
    resources: Dict[str, str] = field(default_factory=dict)


@dataclass
class TaskExecution:

    task: Task
    history: List[Union["ManagerSession", "SubtaskExecution"]] = field(
        default_factory=list
    )
    subtask_queue: SubtaskQueue = field(default_factory=SubtaskQueue)
    status: TaskStatus = TaskStatus.IN_PROGRESS
    failure_reason: str | None = None

    def add_session(self, session: Union["ManagerSession", "SubtaskExecution"]) -> None:
        self.history.append(session)

    def mark_completed(self) -> None:
        self.status = TaskStatus.COMPLETED

    def mark_aborted(self, reason: str) -> None:
        self.status = TaskStatus.ABORTED
        self.failure_reason = reason

    def __str__(self) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append("TASK EXECUTION")
        lines.append("=" * 80)
        lines.append(f"Task: {self.task.description}")
        lines.append(f"Status: {self.status.value}")
        if self.status == TaskStatus.ABORTED and self.failure_reason:
            lines.append(f"Abort Reason: {self.failure_reason}")
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
            from .manager.manager_session import ManagerSession
            from .subtask_execution import SubtaskExecution

            for item in self.history:
                if isinstance(item, ManagerSession):
                    lines.append(f"\n[Manager Session {item.session_number}]")
                    for line in str(item).split("\n"):
                        lines.append(f"  {line}")
                elif isinstance(item, SubtaskExecution):
                    lines.append("\n[Subtask Execution]")
                    for line in str(item).split("\n"):
                        lines.append(f"  {line}")
                lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)
