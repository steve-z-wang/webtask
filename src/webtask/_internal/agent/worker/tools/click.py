"""Click tool for clicking elements."""

from pydantic import BaseModel, Field
from ...tool import Tool


class ClickTool(Tool):
    """Click an element on the page."""

    name = "click"
    description = "Click an element on the page"

    class Params(BaseModel):
        """Parameters for click tool."""

        element_id: str = Field(description="ID of the element to click")

    async def execute(self, params: Params, **kwargs) -> None:
        """Execute click on element.

        Args:
            params: Validated parameters
            **kwargs: worker_browser injected by ToolRegistry
        """
        worker_browser = kwargs.get("worker_browser")
        await worker_browser.click(params.element_id)
