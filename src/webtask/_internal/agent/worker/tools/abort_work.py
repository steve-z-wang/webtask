"""Worker tool - signal cannot proceed with subtask."""

from pydantic import BaseModel, Field
from webtask.agent.tool import Tool


class AbortWorkTool(Tool):
    """Signal that the worker cannot proceed further with the subtask."""

    name = "abort_work"
    description = "Signal that you cannot proceed further with this subtask (stuck, blocked, error, or impossible to complete)"

    class Params(BaseModel):
        """Parameters for abort_work tool."""

        reason: str = Field(
            description="Explain why you cannot continue and provide any relevant context about what went wrong or what is blocking you"
        )

    async def execute(self, params: Params) -> None:
        """Signal that work is aborted."""
        pass
