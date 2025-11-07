"""Scheduler tools for subtask queue management."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from ..tool import Tool

if TYPE_CHECKING:
    from ..task import TaskExecution


class AddSubtaskTool(Tool):
    """Add subtask to end of backlog."""

    name = "add_subtask"
    description = "Add a new subtask to the end of the backlog"

    class Params(BaseModel):
        description: str = Field(description="Subtask description")

    async def execute(self, params: Params, **kwargs) -> str:
        """Append subtask to queue.

        Args:
            params: Validated parameters
            **kwargs: task injected by ToolRegistry

        Returns:
            Success message
        """
        task = kwargs.get("task")
        task.subtask_queue.add(params.description)
        return f"Added subtask: {params.description}"


class CancelSubtaskTool(Tool):
    """Cancel subtask at specific position."""

    name = "cancel_subtask"
    description = "Cancel a subtask at a specific position in the backlog (marks as canceled, doesn't delete)"

    class Params(BaseModel):
        index: int = Field(description="Index of subtask to cancel (0-based)")

    async def execute(self, params: Params, **kwargs) -> str:
        """Mark subtask as canceled.

        Args:
            params: Validated parameters
            **kwargs: task injected by ToolRegistry

        Returns:
            Success message
        """
        task = kwargs.get("task")
        task.subtask_queue.cancel(params.index)
        return f"Canceled subtask at index {params.index}"


class StartWorkTool(Tool):
    """Signal transition to worker."""

    name = "start_work"
    description = "Signal that planning is complete and worker should begin executing subtasks"

    class Params(BaseModel):
        pass

    async def execute(self, params: Params, **kwargs) -> str:
        """Transition signal - no operation needed.

        Args:
            params: Validated parameters
            **kwargs: Unused

        Returns:
            Success message
        """
        return "Starting work on subtasks"
