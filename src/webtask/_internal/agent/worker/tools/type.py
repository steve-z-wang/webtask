"""Type tool for typing text into elements."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from webtask.agent.tool import Tool

if TYPE_CHECKING:
    from ..worker_browser import WorkerBrowser


class TypeTool(Tool):
    """Type text into an element character by character."""

    name = "type"
    description = "Type text into an element character by character with realistic delays (appends to existing text - use fill to replace)"

    class Params(BaseModel):
        """Parameters for type tool."""

        element_id: str = Field(description="ID of the element to type into")
        text: str = Field(description="Text to type into the element")
        description: str = Field(
            description="Human-readable description of what element you're typing into (e.g., 'Search box', 'Comment field')"
        )

    def __init__(self, worker_browser: "WorkerBrowser"):
        """Initialize type tool with worker browser."""
        self.worker_browser = worker_browser

    async def execute(self, params: Params) -> None:
        """Execute type on element."""
        element = await self.worker_browser.select(params.element_id)
        # Type text character by character (appends to existing content)
        await element.type(params.text)
