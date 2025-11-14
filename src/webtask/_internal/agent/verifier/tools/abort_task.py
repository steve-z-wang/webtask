"""Verifier tool - abort task."""

from pydantic import BaseModel, Field
from webtask.agent.tool import Tool


class AbortTaskTool(Tool):
    """Signal that task cannot be completed."""

    name = "abort_task"
    description = "Signal that the task cannot be completed due to unfixable blocker (e.g., wrong approach, impossible requirement, bot challenge, permanent error)"

    class Params(BaseModel):
        """Parameters for abort_task tool."""

        feedback: str = Field(
            description="Explanation of why task cannot be completed - what went wrong, what was tried, what blocked progress"
        )

    async def execute(self, params: Params) -> None:
        """Verification signal - no action needed."""
        pass
