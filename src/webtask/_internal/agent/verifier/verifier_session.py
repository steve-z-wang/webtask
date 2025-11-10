"""VerifierSession - tracks one verifier.run() execution."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from ..tool_call import Iteration, ToolCall
from ..worker.worker_session import WorkerSession


@dataclass
class VerifierSession:
    session_number: int  # 1-indexed session number
    task_description: str
    subtask_description: str
    worker_session: WorkerSession
    max_iterations: int = 3
    iterations: List[Iteration] = field(default_factory=list)
    subtask_decision: Optional[ToolCall] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        lines = ["=== Verifier Session ==="]
        lines.append(f"Task: {self.task_description}")
        lines.append(f"Subtask: {self.subtask_description}")
        if self.subtask_decision:
            lines.append(f"Subtask Decision: {self.subtask_decision.tool}")
        lines.append(f"Iterations: {len(self.iterations)}/{self.max_iterations}")
        lines.append("")
        for iteration in self.iterations:
            lines.append(f"--- Iteration {iteration.iteration_number} ---")
            # Indent each line of the iteration
            for line in str(iteration).split("\n"):
                lines.append(f"  {line}")
            lines.append("")
        return "\n".join(lines)
