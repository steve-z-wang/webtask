"""Verifier tool - mark subtask failed."""

from pydantic import BaseModel, Field
from ...tool import Tool


class MarkSubtaskFailedTool(Tool):
    """Signal that current subtask has failed."""

    name = "mark_subtask_failed"
    description = "Signal that the current subtask failed and requirements were not met (e.g., worker couldn't find element, page error, blocker encountered)"

    class Params(BaseModel):
        """Parameters for mark_subtask_failed tool."""

        failure_reason: str = Field(
            description="Reason why this subtask failed and what went wrong"
        )

    async def execute(self, params: Params, **kwargs) -> None:
        """Verification signal.

        Args:
            params: Validated parameters
            **kwargs: Unused
        """
        pass
