
from pydantic import BaseModel, Field
from ...tool import Tool


class RequestCorrectionTool(Tool):

    name = "request_correction"
    description = "Request Worker to make corrections to fix issues (use when fixable without replanning)"

    class Params(BaseModel):

        feedback: str = Field(
            description="What needs to be corrected and how to fix it"
        )

    async def execute(self, params: Params, **kwargs) -> None:
        pass
