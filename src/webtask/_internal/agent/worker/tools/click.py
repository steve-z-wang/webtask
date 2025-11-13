
from pydantic import BaseModel, Field
from ...tool import Tool


class ClickTool(Tool):

    name = "click"
    description = "Click an element on the page"

    class Params(BaseModel):

        element_id: str = Field(description="ID of the element to click")

    async def execute(self, params: Params, **kwargs) -> None:
        worker_browser = kwargs.get("worker_browser")
        await worker_browser.click(params.element_id)
