
from pydantic import BaseModel, Field
from ...tool import Tool


class CompleteTaskTool(Tool):

    name = "complete_task"
    description = "Signal that the entire task has been completed and all requirements have been met"

    class Params(BaseModel):

        details: str = Field(
            description="Summary of what was accomplished and why the task is completed"
        )

    async def execute(self, params: Params, **kwargs) -> None:
        pass
