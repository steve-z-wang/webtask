"""Step - represents a complete agent cycle (mode execution → action execution)."""

from pydantic import BaseModel
from typing import Optional, List
from .schemas.mode import ModeResult, VerifyResult


class ExecutionResult(BaseModel):
    """Result of executing an action."""

    success: bool
    error: Optional[str] = None


class Step(BaseModel):
    """Represents one complete agent cycle."""

    result: ModeResult
    executions: List[ExecutionResult]

    @property
    def is_complete(self) -> bool:
        """Check if task is complete (only VerifyResult can mark complete)."""
        return isinstance(self.result, VerifyResult) and self.result.complete


class TaskResult(BaseModel):
    """Result of executing a task."""

    completed: bool
    steps: List[Step]
    message: str
