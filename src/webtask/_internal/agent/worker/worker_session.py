"""WorkerSession - tracks worker execution with conversation history."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..worker.worker import ToolCallPair


class WorkerStatus(str, Enum):
    """Worker execution status."""

    COMPLETED = "completed"
    ABORTED = "aborted"
    MAX_STEPS = "max_steps"


@dataclass
class WorkerSession:
    """Worker session - execution result + conversation history."""

    # Execution result
    status: WorkerStatus
    output: Optional[Any]  # Structured data from set_output
    feedback: str  # Summary of what happened

    # Conversation history (for persist_context)
    pairs: List["ToolCallPair"]  # Full conversation (LLM calls + results)

    # Metadata
    task_description: str
    steps_used: int
    max_steps: int

    # Optional debug info
    final_dom: Optional[str] = None
    final_screenshot: Optional[str] = None

    def __str__(self) -> str:
        """Simple string representation showing basic info."""
        return f"WorkerSession(task='{self.task_description}', steps={self.steps_used}/{self.max_steps}, status={self.status.value})"
