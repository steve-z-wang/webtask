"""Tool call and iteration tracking for agent execution."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass


class ProposedToolCall(BaseModel):
    """
    Tool call request from LLM (proposal phase).

    This is what the LLM returns - pure JSON-serializable data for validation.
    """

    description: str = Field(
        description="Past-tense description of what this action does (e.g., 'Clicked the cart icon', 'Filled quantity field with 2')"
    )
    tool: str = Field(description="Tool name to execute")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool-specific parameters"
    )


@dataclass
class ToolCall:
    """
    Tool call with execution tracking (runtime).

    Mutable dataclass for tracking execution state without Pydantic overhead.
    """

    # Request (from LLM)
    description: str
    tool: str
    parameters: Dict[str, Any]

    # Execution result (filled after execution)
    success: Optional[bool] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

    @classmethod
    def from_proposed(cls, proposed: ProposedToolCall) -> "ToolCall":
        """Create ToolCall from proposed tool call."""
        return cls(
            description=proposed.description,
            tool=proposed.tool,
            parameters=proposed.parameters,
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
        """String representation for debugging."""
        status = (
            "[SUCCESS]"
            if self.success
            else "[FAILED]" if self.success is not None else "[PENDING]"
        )
        lines = [f"{status} {self.description}"]
        lines.append(
            f"   Tool: {self.tool}({', '.join(f'{k}={v}' for k, v in self.parameters.items())})"
        )
        if not self.success and self.error:
            lines.append(f"   Error: {self.error}")
        return "\n".join(lines)


class ProposedIteration(BaseModel):
    """
    Proposed iteration from LLM (one loop iteration).

    Contains the LLM's observation, thinking, and tool calls to execute.
    This is what the LLM returns in one iteration of a role's run() loop.
    """

    observation: str = Field(
        description="Observation of current page state (success/error messages, loading states, what just changed)"
    )
    thinking: str = Field(description="Analysis and reasoning about what to do next")
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

    iteration_number: int  # 1-indexed iteration number
    observation: str
    thinking: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_proposed(cls, proposed: ProposedIteration) -> "Iteration":
        """Create Iteration from proposed iteration (before execution)."""
        return cls(observation=proposed.observation, thinking=proposed.thinking)

    def add_tool_call(self, tool_call: ToolCall) -> None:
        """Add an executed tool call to this iteration."""
        self.tool_calls.append(tool_call)

    def __str__(self) -> str:
        """String representation for debugging."""
        lines = []
        lines.append(f"Observation: {self.observation}")
        lines.append(f"Thinking: {self.thinking}")
        lines.append(f"Actions ({len(self.tool_calls)}):")
        for tc in self.tool_calls:
            # Indent each line of the tool call
            for line in str(tc).split("\n"):
                lines.append(f"  {line}")
        return "\n".join(lines)
