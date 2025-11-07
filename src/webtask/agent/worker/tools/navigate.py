"""Navigate browser tool."""

from pydantic import BaseModel, Field
from ...tool import Tool


class NavigateTool(Tool):
    """Navigate to a URL."""

    name = "navigate"
    description = "Navigate to a URL"

    class Params(BaseModel):
        """Parameters for navigate tool."""

        url: str = Field(description="URL to navigate to")

    async def execute(self, params: Params, **kwargs) -> str:
        """Execute navigation.

        Args:
            params: Validated parameters
            **kwargs: llm_browser injected by ToolRegistry

        Returns:
            Success message
        """
        llm_browser = kwargs.get("llm_browser")
        await llm_browser.navigate(params.url)
        return f"Navigated to {params.url}"
