"""Run - tracks task execution with conversation history."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Any
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status."""

    COMPLETED = "completed"
    ABORTED = "aborted"


@dataclass
class TaskResult:
    """Internal task execution result with status."""

    status: Optional[TaskStatus] = None
    output: Optional[Any] = None
    feedback: Optional[str] = None

    @property
    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED if self.status else False

    def __str__(self) -> str:
        status_str = self.status.value if self.status else "pending"
        return f"TaskResult(status={status_str}, output={self.output is not None})"


@dataclass
class Run:
    """Task execution run - full execution history with embedded result."""

    result: TaskResult
    messages: List

    task_description: str
    steps_used: int
    max_steps: int

    def __str__(self) -> str:
        return f"Run(task='{self.task_description}', steps={self.steps_used}/{self.max_steps}, status={self.result.status.value if self.result.status else 'pending'})"
