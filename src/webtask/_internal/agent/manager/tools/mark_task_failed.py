"""Manager tool - mark task failed."""

from pydantic import BaseModel, Field
from ...tool import Tool


class MarkTaskFailedTool(Tool):
    """Signal that the entire task has failed and cannot be completed."""

    name = "mark_task_failed"
    description = (
        "Signal that the entire task has failed due to conditions beyond control "
        "(e.g., website unavailable, item doesn't exist, missing required authentication)"
    )

    class Params(BaseModel):
        """Parameters for mark_task_failed tool."""

        reason: str = Field(
            description="Explanation of why the task cannot be completed and what blocked it"
        )

    async def execute(self, params: Params, **kwargs) -> None:
        """Transition signal.

        Args:
            params: Validated parameters
            **kwargs: Unused
        """
        pass
