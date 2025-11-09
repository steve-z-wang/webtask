"""WorkerSession - tracks one worker.run() execution."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from ..tool_call import Iteration


@dataclass
class WorkerSession:
    session_number: int  # 1-indexed session number
    subtask_description: str
    max_iterations: int = 10
    iterations: List[Iteration] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        lines = ["=== Worker Session ==="]
        lines.append(f"Subtask: {self.subtask_description}")
        lines.append(f"Iterations: {len(self.iterations)}/{self.max_iterations}")
        lines.append("")
        for iteration in self.iterations:
            lines.append(f"--- Iteration {iteration.iteration_number} ---")
            # Indent each line of the iteration
            for line in str(iteration).split("\n"):
                lines.append(f"  {line}")
            lines.append("")
        return "\n".join(lines)
