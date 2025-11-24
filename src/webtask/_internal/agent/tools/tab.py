"""Tab management tools."""

from typing import TYPE_CHECKING
from dodo import tool

if TYPE_CHECKING:
    from webtask._internal.agent.agent_browser import AgentBrowser


@tool
class OpenTabTool:
    """Open a new blank browser tab and switch to it."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(self, description: str) -> str:
        """
        Args:
            description (str): Why you are opening a new tab (e.g., 'Open new tab to search for product')
        """
        await self.browser.open_tab()
        return f"Opened new tab: {description}"


@tool
class SwitchTabTool:
    """Switch to a different browser tab by its index (shown in Tabs section)."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(self, tab_index: int, description: str) -> str:
        """
        Args:
            tab_index (int): The tab index to switch to (0-based, as shown in Tabs section)
            description (str): Why you are switching to this tab (e.g., 'Switch back to main tab')
        """
        self.browser.focus_tab(tab_index)
        return f"Switched to tab [{tab_index}]: {description}"
