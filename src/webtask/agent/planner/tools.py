"""Scheduler tools for subtask queue management."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from ..tool import Tool

if TYPE_CHECKING:
    pass


class StartSubtaskTool(Tool):
    """Start a new subtask."""

    name = "start_subtask"
    description = "Start a new subtask with the given goal"

    class Params(BaseModel):
        goal: str = Field(description="Subtask goal to achieve")

    async def execute(self, params: Params, **kwargs) -> None:
        """Start a new subtask.

        Args:
            params: Validated parameters
            **kwargs: subtask_queue injected by ToolRegistry
        """
        subtask_queue = kwargs.get("subtask_queue")

        # Start new subtask (moves current to history if exists)
        subtask_queue.start_new(params.goal)
