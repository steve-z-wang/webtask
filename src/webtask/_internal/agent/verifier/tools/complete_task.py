"""Verifier tool - complete task."""

from pydantic import BaseModel, Field
from webtask.agent.tool import Tool


class CompleteTaskTool(Tool):
    """Signal that task was successfully completed."""

    name = "complete_task"
    description = (
        "Signal that the task was successfully completed and all requirements were met"
    )

    class Params(BaseModel):
        """Parameters for complete_task tool."""

        feedback: str = Field(
            description="What was accomplished and how requirements were met"
        )

    async def execute(self, params: Params) -> None:
        """Verification signal - no action needed."""
        pass
