"""Step - represents a complete agent cycle (proposal → execution → verification)."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class Action:
    """
    Represents an action to be executed.

    Pure data structure with tool name and parameters.
    """

    reason: str
    tool_name: str
    parameters: Dict[str, Any]


@dataclass
class ExecutionResult:
    """
    Result of executing an action.

    Attributes:
        success: Whether execution succeeded
        error: Error message if execution failed
    """

    success: bool
    error: Optional[str] = None


@dataclass
class VerificationResult:
    """
    Result of verifying task completion.

    Attributes:
        complete: Whether the task is complete
        message: Explanation or reasoning for the verification result
    """

    complete: bool
    message: str


@dataclass
class Step:
    """
    Represents one complete agent cycle.

    Contains the proposals, execution results, and verification result.
    """

    proposals: List[Action]  # Changed from singular to plural
    executions: List[ExecutionResult]  # Changed from singular to plural
    verification: VerificationResult


@dataclass
class TaskResult:
    """
    Result of executing a task.

    Attributes:
        completed: Whether the task was completed successfully
        steps: List of all steps taken during execution
        message: Final verification message
    """

    completed: bool
    steps: List[Step]
    message: str
