
from pydantic import BaseModel, Field
from ...tool import Tool


class AbortTaskTool(Tool):

    name = "abort_task"
    description = (
        "Signal that the entire task has been aborted due to conditions beyond control "
        "(e.g., website unavailable, item doesn't exist, missing required authentication)"
    )

    class Params(BaseModel):

        reason: str = Field(
            description="Explanation of why the task cannot be completed and what blocked it"
        )

    async def execute(self, params: Params, **kwargs) -> None:
        pass
