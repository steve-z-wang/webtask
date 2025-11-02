"""Step - represents a complete agent cycle (proposal → execution)."""

from pydantic import BaseModel
from typing import Optional, List
from .schemas import Proposal


class ExecutionResult(BaseModel):
    """Result of executing an action."""

    success: bool
    error: Optional[str] = None


class Step(BaseModel):
    """Represents one complete agent cycle."""

    proposal: Proposal
    executions: List[ExecutionResult]


class TaskResult(BaseModel):
    """Result of executing a task."""

    completed: bool
    steps: List[Step]
    message: str
