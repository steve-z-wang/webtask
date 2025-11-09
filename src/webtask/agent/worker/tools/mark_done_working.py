"""Worker tool - signal done working on subtask."""

from pydantic import BaseModel, Field
from ...tool import Tool


class MarkDoneWorkingTool(Tool):
    """Signal that worker has finished attempting the subtask."""

    name = "mark_done_working"
    description = "Signal that you've finished attempting this subtask and are ready for verification (Verifier will check if it succeeded)"

    class Params(BaseModel):
        """Parameters for mark_done_working tool."""

        details: str = Field(
            description="Summary of what you attempted and what state the page is in"
        )

    async def execute(self, params: Params, **kwargs) -> None:
        """Signal that work is done.

        Args:
            params: Validated parameters
            **kwargs: Unused
        """
        pass
