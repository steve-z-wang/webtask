"""WorkerSession - tracks one worker.run() execution with conversation history."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Any


class WorkerEndReason(str, Enum):
    """Worker execution end reason."""

    COMPLETE_WORK = "complete_work"
    ABORT_WORK = "abort_work"
    MAX_STEPS = "max_steps"


@dataclass
class WorkerSession:
    """Worker session with conversation history."""

    task_description: str

    start_time: datetime
    end_time: datetime
    max_steps: int = 20
    steps_used: int = 0
    summary: str = ""

    end_reason: Optional[WorkerEndReason] = None
    final_dom: Optional[str] = None
    final_screenshot: Optional[str] = None
    output: Optional[Any] = None  # Structured output from set_output() tool

    def __str__(self) -> str:
        """Simple string representation showing basic info."""
        return f"WorkerSession(task='{self.task_description}', steps={self.steps_used}/{self.max_steps}, end_reason={self.end_reason})"
