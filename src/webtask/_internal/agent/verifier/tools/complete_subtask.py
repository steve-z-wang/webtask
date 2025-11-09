"""Verifier tool - complete subtask."""

from pydantic import BaseModel, Field
from ...tool import Tool


class CompleteSubtaskTool(Tool):
    """Signal that current subtask is complete."""

    name = "complete_subtask"
    description = "Signal that the current subtask was successfully completed and all requirements were met"

    class Params(BaseModel):
        """Parameters for complete_subtask tool."""

        feedback: str = Field(
            description="What was accomplished and how requirements were met"
        )

    async def execute(self, params: Params, **kwargs) -> None:
        """Verification signal.

        Args:
            params: Validated parameters
            **kwargs: Unused
        """
        pass
