
from pydantic import BaseModel, Field
from ...tool import Tool


class MarkDoneWorkingTool(Tool):

    name = "mark_done_working"
    description = "Signal that you've finished attempting this subtask and are ready for verification (Verifier will check if it succeeded)"

    class Params(BaseModel):

        details: str = Field(
            description="Summary of what you attempted and what state the page is in"
        )

    async def execute(self, params: Params, **kwargs) -> None:
        pass
