"""Step - represents a complete agent cycle (propose actions → execute actions)."""

from pydantic import BaseModel
from typing import Optional, List
from .schemas.mode import Proposal


class ExecutionResult(BaseModel):
    """Result of executing an action."""

    success: bool
    error: Optional[str] = None


class Step(BaseModel):
    """Represents one complete agent cycle."""

    proposal: Proposal
    executions: List[ExecutionResult]

    @property
    def is_complete(self) -> bool:
        """Check if task is complete (mark_complete tool was called)."""
        return any(action.tool == "mark_complete" for action in self.proposal.actions)


class TaskResult(BaseModel):
    """Result of executing a task."""

    completed: bool
    steps: List[Step]
    message: str
