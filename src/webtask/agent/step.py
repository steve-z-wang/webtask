"""Step - represents a complete agent cycle (proposal → execution)."""

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
class ProposalResult:
    """Result from proposer including completion status and actions."""

    complete: bool
    message: str
    actions: List[Action]


@dataclass
class Step:
    """Represents one complete agent cycle."""

    proposal: ProposalResult
    executions: List[ExecutionResult]


@dataclass
class TaskResult:
    """Result of executing a task."""

    completed: bool
    steps: List[Step]
    message: str
