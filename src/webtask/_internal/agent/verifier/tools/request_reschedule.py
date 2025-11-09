"""Verifier tool - request reschedule."""

from pydantic import BaseModel, Field
from ...tool import Tool


class RequestRescheduleTool(Tool):
    """Signal that Manager needs to reschedule/replan."""

    name = "request_reschedule"
    description = "Signal that the current subtask could not be completed and Manager needs to reschedule/replan (e.g., subtask failed, wrong approach, blocker encountered, unclear goal)"

    class Params(BaseModel):
        """Parameters for request_reschedule tool."""

        feedback: str = Field(
            description="Explanation of why reschedule is needed - what went wrong, what was tried, what blocked progress"
        )

    async def execute(self, params: Params, **kwargs) -> None:
        """Verification signal.

        Args:
            params: Validated parameters
            **kwargs: Unused
        """
        pass
