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
        """Initialize goto tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute goto."""
        if not self.browser.has_current_page():
            await self.browser.open_tab()
        page = self.browser.get_current_page()
        await page.goto(params.url)
        await self.browser.wait()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Went to {params.url}",
        )


class GoBackTool(Tool):
    """Navigate back in browser history."""

    name = "go_back"
    description = "Navigate to the previous page in browser history"

    class Params(BaseModel):
        """Parameters for go_back tool."""

        description: str = Field(
            description="Why you're going back (e.g., 'Return to search results')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize go_back tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute go back."""
        page = self.browser.get_current_page()
        await page.go_back()
        await self.browser.wait()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Went back: {params.description}",
        )


class GoForwardTool(Tool):
    """Navigate forward in browser history."""

    name = "go_forward"
    description = "Navigate to the next page in browser history"

    class Params(BaseModel):
        """Parameters for go_forward tool."""

        description: str = Field(
            description="Why you're going forward (e.g., 'Return to product page')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize go_forward tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute go forward."""
        page = self.browser.get_current_page()
        await page.go_forward()
        await self.browser.wait()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Went forward: {params.description}",
        )


class SearchTool(Tool):
    """Navigate to search engine homepage."""

    name = "search"
    description = "Navigate to the default search engine homepage"

    class Params(BaseModel):
        """Parameters for search tool."""

        description: str = Field(
            description="Why you're going to search (e.g., 'Start new search for product')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize search tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute search navigation."""
        if not self.browser.has_current_page():
            await self.browser.open_tab()
        page = self.browser.get_current_page()
        await page.goto("https://www.google.com")
        await self.browser.wait()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Went to search: {params.description}",
        )


class KeyCombinationTool(Tool):
    """Press keyboard key combinations."""

    name = "key_combination"
    description = (
        "Press keyboard keys or combinations (e.g., 'Control+C', 'Enter', 'Escape')"
    )

    class Params(BaseModel):
        """Parameters for key_combination tool."""

        keys: str = Field(
            description="Keys to press (e.g., 'Control+C', 'Enter', 'Alt+Tab')"
        )
        description: str = Field(
            description="What this key combination does (e.g., 'Copy selected text', 'Submit form')"
        )

    def __init__(self, browser: "AgentBrowser"):
        """Initialize key_combination tool with browser."""
        self.browser = browser

    async def execute(self, params: Params) -> ToolResult:
        """Execute key combination."""
        page = self.browser.get_current_page()
        await page.keyboard_press(params.keys)
        await self.browser.wait()
        return ToolResult(
            name=self.name,
            status=ToolResultStatus.SUCCESS,
            description=f"Pressed {params.keys}: {params.description}",
        )
