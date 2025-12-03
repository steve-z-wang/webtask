"""Tab management tools."""

from typing import TYPE_CHECKING
from pydantic import Field
from webtask.llm.tool import Tool, ToolParams
from webtask.llm.message import ToolResult, ToolResultStatus

if TYPE_CHECKING:
    from webtask._internal.agent.agent_browser import AgentBrowser


class OpenTabTool(Tool):
    """Open a new browser tab."""

    name = "open_tab"
    description = "Open a new blank browser tab and switch to it"

    class Params(ToolParams):
        """Parameters for open_tab tool."""

        description: str = Field(
            description="Why you are opening a new tab (e.g., 'Open new tab to search for product')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize open_tab tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Open a new tab."""
        await self.browser.open_tab()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Opened new tab: {params.description}",
        )


class SwitchTabTool(Tool):
    """Switch to a different browser tab."""

    name = "switch_tab"
    description = (
        "Switch to a different browser tab by its index (shown in Tabs section)"
    )

    class Params(ToolParams):
        """Parameters for switch_tab tool."""

        tab_index: int = Field(
            description="The tab index to switch to (0-based, as shown in Tabs section)",
            ge=0,
        )
        description: str = Field(
            description="Why you are switching to this tab (e.g., 'Switch back to main tab')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize switch_tab tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Switch to specified tab."""
        self.browser.focus_tab(params.tab_index)
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Switched to tab [{params.tab_index}]: {params.description}",
        )
