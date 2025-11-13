
from pydantic import BaseModel, Field
from ...tool import Tool


class RequestRescheduleTool(Tool):

    name = "request_reschedule"
    description = "Signal that the current subtask could not be completed and Manager needs to reschedule/replan (e.g., subtask failed, wrong approach, blocker encountered, unclear goal)"

    class Params(BaseModel):

        feedback: str = Field(
            description="Explanation of why reschedule is needed - what went wrong, what was tried, what blocked progress"
        )

    async def execute(self, params: Params, **kwargs) -> None:
        pass
