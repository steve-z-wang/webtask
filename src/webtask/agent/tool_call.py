"""Tool call and iteration tracking for agent execution."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProposedToolCall(BaseModel):
    """
    Tool call request from LLM (proposal phase).

    This is what the LLM returns - pure JSON-serializable data for validation.
    """

    tool: str = Field(description="Tool name to execute")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool-specific parameters"
    )
    reason: str = Field(description="Why this tool call is needed")

    def __str__(self) -> str:
        """Format for human-readable output."""
        params_str = ", ".join(f"{k}={v}" for k, v in self.parameters.items())
        return f"{self.tool}({params_str}) - {self.reason}"


@dataclass
class ToolCall:
    """
    Tool call with execution tracking (runtime).

    Mutable dataclass for tracking execution state without Pydantic overhead.
    """

    # Request (from LLM)
    tool: str
    parameters: Dict[str, Any]
    reason: str

    # Execution result (filled after execution)
    success: Optional[bool] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

    @classmethod
    def from_proposed(cls, proposed: ProposedToolCall) -> "ToolCall":
        """Create ToolCall from proposed tool call."""
        return cls(
            tool=proposed.tool,
            parameters=proposed.parameters,
            reason=proposed.reason,
        )

    def mark_success(self, result: Any = None) -> None:
        """Mark tool call as successful."""
        self.success = True
        self.result = result
        self.timestamp = datetime.now()

    def mark_failure(self, error: str) -> None:
        """Mark tool call as failed."""
        self.success = False
        self.error = error
        self.timestamp = datetime.now()

    @property
    def executed(self) -> bool:
        """Check if tool call has been executed."""
        return self.success is not None

    def __str__(self) -> str:
        """Format for human-readable output."""
        # Format parameters without truncation
        params_str = ", ".join(f"{k}={v}" for k, v in self.parameters.items())
        result_str = f"{self.tool}({params_str}) - {self.reason}"

        if self.executed:
            status = "✓" if self.success else "✗"
            result_str = f"{status} {result_str}"
            if not self.success and self.error:
                result_str += f"\n   Error: {self.error}"

        return result_str


class ProposedIteration(BaseModel):
    """
    Proposed iteration from LLM (one loop iteration).

    Contains the LLM's message and list of tool calls to execute.
    This is what the LLM returns in one iteration of a role's run() loop.
    """

    message: str = Field(description="LLM's reasoning/message for this iteration")
    tool_calls: List[ProposedToolCall] = Field(
        default_factory=list, description="Tool calls to execute"
    )


@dataclass
class Iteration:
    """
    Executed iteration with results (runtime).

    Tracks what happened in one iteration of a role's loop.
    Tool calls are added progressively as they execute.
    """

    message: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_proposed(cls, proposed: ProposedIteration) -> "Iteration":
        """Create Iteration from proposed iteration (before execution)."""
        return cls(message=proposed.message)

    def add_tool_call(self, tool_call: ToolCall) -> None:
        """Add an executed tool call to this iteration."""
        self.tool_calls.append(tool_call)

    def __str__(self) -> str:
        """Format iteration for human-readable output."""
        lines = [f"Message: {self.message}"]
        if self.tool_calls:
            lines.append("Tool calls:")
            for i, tc in enumerate(self.tool_calls, 1):
                lines.append(f"  {i}. {tc}")
        return "\n".join(lines)
