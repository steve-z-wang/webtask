"""Add subtask tool for Manager."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from ...tool import Tool

if TYPE_CHECKING:
    pass


class AddSubtaskTool(Tool):
    """Add a new subtask to the pending queue."""

    name = "add_subtask"
    description = "Add a new subtask to the pending queue with the given goal"

    class Params(BaseModel):
        goal: str = Field(description="Subtask goal to achieve")

    async def execute(self, params: Params, **kwargs) -> None:
        """Add a new subtask to the pending queue.

        Args:
            params: Validated parameters
            **kwargs: subtask_queue injected by ToolRegistry
        """
        subtask_queue = kwargs.get("subtask_queue")

        # Add subtask to pending queue
        subtask_queue.add_subtask(params.goal)
