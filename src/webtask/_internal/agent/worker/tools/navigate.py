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

    async def execute(self, params: Params, **kwargs) -> None:
        """Execute navigation.

        Args:
            params: Validated parameters
            **kwargs: worker_browser injected by ToolRegistry
        """
        worker_browser = kwargs.get("worker_browser")
        await worker_browser.navigate(params.url)
