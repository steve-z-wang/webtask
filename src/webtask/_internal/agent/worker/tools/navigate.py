
from pydantic import BaseModel, Field
from ...tool import Tool


class NavigateTool(Tool):

    name = "navigate"
    description = "Navigate to a URL"

    class Params(BaseModel):

        url: str = Field(description="URL to navigate to")

    async def execute(self, params: Params, **kwargs) -> None:
        worker_browser = kwargs.get("worker_browser")
        await worker_browser.navigate(params.url)
