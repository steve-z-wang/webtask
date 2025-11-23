"""Navigation tools for URL and history navigation."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field
from webtask.llm.tool import Tool
from webtask.llm.message import ToolResult, ToolResultStatus

if TYPE_CHECKING:
    from webtask._internal.agent.agent_browser import AgentBrowser


class GotoTool(Tool):
    """Go to a URL."""

    name = "goto"
    description = "Go to a URL"

    class Params(BaseModel):
        """Parameters for goto tool."""

        url: str = Field(description="URL to go to")

    def __init__(self, browser: "AgentBrowser"):
        """Initialize goto tool with worker browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute goto."""
        await self.browser.goto(params.url)
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Went to {params.url}",
        )
