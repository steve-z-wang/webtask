"""Session types for agent roles."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from .tool_call import ToolCall, Iteration

if TYPE_CHECKING:
    from .subtask import Subtask
    from .task import TaskExecution


@dataclass
class SchedulerSession:
    """Session from one scheduler.run() call.

    Created with task execution and config, passed to scheduler.run() to be filled.
    Scheduler always ends by calling start_work (or timeout).
    """

    task: "TaskExecution"
    max_iterations: int = 10
    iterations: List[Iteration] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def add_iteration(self, iteration: Iteration) -> None:
        self.iterations.append(iteration)

    def __str__(self) -> str:
        lines = [f"Scheduler Session ({len(self.iterations)} iterations)"]
        for i, iteration in enumerate(self.iterations, 1):
            lines.append(f"  Iteration {i}:")
            lines.append(f"    {iteration.message}")
            for tc in iteration.tool_calls:
                lines.append(f"    {tc}")
        return "\n".join(lines)


@dataclass
class WorkerSession:
    """Session from one worker.run() call.

    Created with subtask and config, passed to worker.run() to be filled.
    Worker updates the subtask status directly (complete/failed).
    """

    subtask: "Subtask"
    max_iterations: int = 10
    iterations: List[Iteration] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def add_iteration(self, iteration: Iteration) -> None:
        self.iterations.append(iteration)

    def __str__(self) -> str:
        lines = [
            f"Worker Session - Subtask: {self.subtask.description}",
            f"Status: {self.subtask.status.value.upper()}",
            f"Iterations: {len(self.iterations)}"
        ]
        for i, iteration in enumerate(self.iterations, 1):
            lines.append(f"  Iteration {i}: {iteration.message}")
            for tc in iteration.tool_calls:
                lines.append(f"    {tc}")
        return "\n".join(lines)
