"""Navigate browser tool."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from webtask.agent.tool import Tool

if TYPE_CHECKING:
    from ..worker_browser import WorkerBrowser


class NavigateTool(Tool):
    """Navigate to a URL."""

    name = "navigate"
    description = "Navigate to a URL"

    class Params(BaseModel):
        """Parameters for navigate tool."""

        url: str = Field(description="URL to navigate to")

    def __init__(self, worker_browser: "WorkerBrowser"):
        """Initialize navigate tool with worker browser."""
        self.worker_browser = worker_browser

    async def execute(self, params: Params) -> None:
        """Execute navigation."""
        await self.worker_browser.navigate(params.url)
