"""Verifier tool - mark task complete."""

from pydantic import BaseModel, Field
from ...tool import Tool


class MarkTaskCompleteTool(Tool):
    """Signal that the entire task is complete."""

    name = "mark_task_complete"
    description = "Signal that the entire task is complete and all requirements have been met"

    class Params(BaseModel):
        """Parameters for mark_task_complete tool."""

        message: str = Field(description="Summary of what was accomplished and why the task is complete")

    async def execute(self, params: Params, **kwargs) -> str:
        """Transition signal.

        Args:
            params: Validated parameters
            **kwargs: Unused

        Returns:
            Summary message
        """
        return params.message
