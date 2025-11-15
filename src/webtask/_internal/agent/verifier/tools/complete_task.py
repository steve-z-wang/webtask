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

    @staticmethod
    def describe(params: Params) -> str:
        """Generate description of complete_task action."""
        return "Task completed"

    async def execute(self, params: Params) -> None:
        """Verification signal - no action needed."""
        pass
