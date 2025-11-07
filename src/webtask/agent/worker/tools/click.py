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

    async def execute(self, params: Params, **kwargs) -> str:
        """Execute click on element.

        Args:
            params: Validated parameters
            **kwargs: llm_browser injected by ToolRegistry

        Returns:
            Success message
        """
        llm_browser = kwargs.get("llm_browser")
        await llm_browser.click(params.element_id)
        return f"Clicked element {params.element_id}"
