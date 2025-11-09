"""Manager tool - complete task."""

from pydantic import BaseModel, Field
from ...tool import Tool


class CompleteTaskTool(Tool):
    """Signal that the entire task has been completed."""

    name = "complete_task"
    description = "Signal that the entire task has been completed and all requirements have been met"

    class Params(BaseModel):
        """Parameters for complete_task tool."""

        details: str = Field(
            description="Summary of what was accomplished and why the task is completed"
        )

    async def execute(self, params: Params, **kwargs) -> None:
        """Transition signal.

        Args:
            params: Validated parameters
            **kwargs: Unused
        """
        pass
