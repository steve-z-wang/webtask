"""Step - represents a complete agent cycle (proposal → execution → verification)."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class Action:
    """Represents an action to be executed."""

    reason: str
    tool_name: str
    parameters: Dict[str, Any]


@dataclass
class ExecutionResult:
    """Result of executing an action."""

    success: bool
    error: Optional[str] = None


@dataclass
class VerificationResult:
    """Result of verifying task completion."""

    complete: bool
    message: str


@dataclass
class Step:
    """Represents one complete agent cycle."""

    proposals: List[Action]
    executions: List[ExecutionResult]
    verification: VerificationResult


@dataclass
class TaskResult:
    """Result of executing a task."""

    completed: bool
    steps: List[Step]
    message: str
