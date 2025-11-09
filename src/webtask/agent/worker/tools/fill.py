"""Fill tool for filling form elements."""

from pydantic import BaseModel, Field
from ...tool import Tool


class FillTool(Tool):
    """Fill a form element with a value."""

    name = "fill"
    description = "Fill a form element with a value (fast, direct value setting)"

    class Params(BaseModel):
        """Parameters for fill tool."""

        element_id: str = Field(description="ID of the element to fill")
        value: str = Field(description="Value to fill into the element")

    async def execute(self, params: Params, **kwargs) -> None:
        """Execute fill on element.

        Args:
            params: Validated parameters
            **kwargs: worker_browser injected by ToolRegistry
        """
        worker_browser = kwargs.get("worker_browser")
        element = await worker_browser.select(params.element_id)
        await element.fill(params.value)
