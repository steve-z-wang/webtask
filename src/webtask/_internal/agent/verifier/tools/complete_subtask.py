
from pydantic import BaseModel, Field
from ...tool import Tool


class CompleteSubtaskTool(Tool):

    name = "complete_subtask"
    description = "Signal that the current subtask was successfully completed and all requirements were met"

    class Params(BaseModel):

        feedback: str = Field(
            description="What was accomplished and how requirements were met"
        )

    async def execute(self, params: Params, **kwargs) -> None:
        pass
