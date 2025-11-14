"""Fill tool for filling form elements."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from webtask.agent.tool import Tool

if TYPE_CHECKING:
    from ..worker_browser import WorkerBrowser


class FillTool(Tool):
    """Fill a form element with a value."""

    name = "fill"
    description = "Fill a form element with a value (fast, direct value setting)"

    class Params(BaseModel):
        """Parameters for fill tool."""

        element_id: str = Field(description="ID of the element to fill")
        value: str = Field(description="Value to fill into the element")
        description: str = Field(
            description="Human-readable description of what element you're filling (e.g., 'Email input field', 'Password field')"
        )

    def __init__(self, worker_browser: "WorkerBrowser"):
        """Initialize fill tool with worker browser."""
        self.worker_browser = worker_browser

    async def execute(self, params: Params) -> None:
        """Execute fill on element."""
        element = await self.worker_browser.select(params.element_id)
        await element.fill(params.value)
