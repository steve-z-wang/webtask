"""Run - tracks task execution with conversation history."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from webtask.agent.result import Result


@dataclass
class Run:
    """Task execution run - full execution history with embedded result."""

    result: Result
    summary: str
    messages: List

    task_description: str
    steps_used: int
    max_steps: int

    final_dom: Optional[str] = None
    final_screenshot: Optional[str] = None

    def __str__(self) -> str:
        return f"Run(task='{self.task_description}', steps={self.steps_used}/{self.max_steps}, status={self.result.status.value if self.result.status else 'pending'})"
