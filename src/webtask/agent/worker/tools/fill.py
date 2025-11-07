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

    async def execute(self, params: Params, **kwargs) -> str:
        """Execute fill on element.

        Args:
            params: Validated parameters
            **kwargs: llm_browser injected by ToolRegistry

        Returns:
            Success message
        """
        llm_browser = kwargs.get("llm_browser")
        await llm_browser.fill(params.element_id, params.value)
        return f"Filled element {params.element_id} with '{params.value}'"
