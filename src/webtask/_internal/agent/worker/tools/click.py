"""Click tool for clicking elements."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from webtask.agent.tool import Tool

if TYPE_CHECKING:
    from ..worker_browser import WorkerBrowser


class ClickTool(Tool):
    """Click an element on the page."""

    name = "click"
    description = "Click an element on the page"

    class Params(BaseModel):
        """Parameters for click tool."""

        element_id: str = Field(description="ID of the element to click")
        description: str = Field(
            description="Human-readable description of what element you're clicking (e.g., 'Submit button', 'Login link')"
        )

    def __init__(self, worker_browser: "WorkerBrowser"):
        """Initialize click tool with worker browser."""
        self.worker_browser = worker_browser

    async def execute(self, params: Params) -> None:
        """Execute click on element."""
        await self.worker_browser.click(params.element_id)
