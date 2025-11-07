"""Worker decision tool - mark subtask complete."""

from pydantic import BaseModel, Field
from ...tool import Tool


class MarkSubtaskCompleteTool(Tool):
    """Signal that current subtask is complete."""

    name = "mark_subtask_complete"
    description = "Signal that the current subtask is complete and ready to move to next subtask"

    class Params(BaseModel):
        """Parameters for mark_subtask_complete tool."""

        message: str = Field(description="Summary of what was accomplished")

    async def execute(self, params: Params, **kwargs) -> str:
        """Transition signal.

        Args:
            params: Validated parameters
            **kwargs: Unused

        Returns:
            Summary message
        """
        return params.message
