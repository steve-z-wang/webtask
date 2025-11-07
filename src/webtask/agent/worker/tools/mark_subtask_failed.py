"""Worker decision tool - mark subtask failed."""

from pydantic import BaseModel, Field
from ...tool import Tool


class MarkSubtaskFailedTool(Tool):
    """Signal that current subtask has failed and cannot be completed."""

    name = "mark_subtask_failed"
    description = "Signal that the current subtask has failed and cannot be completed (e.g., element not found, page error, blocker encountered)"

    class Params(BaseModel):
        """Parameters for mark_subtask_failed tool."""

        reason: str = Field(
            description="Reason why this subtask failed and cannot be completed"
        )

    async def execute(self, params: Params, **kwargs) -> str:
        """Transition signal.

        Args:
            params: Validated parameters
            **kwargs: Unused

        Returns:
            Failure reason
        """
        return params.reason
