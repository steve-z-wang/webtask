"""Navigation tools for URL and history navigation."""

from typing import TYPE_CHECKING
from dodo import tool

if TYPE_CHECKING:
    from webtask._internal.agent.agent_browser import AgentBrowser


@tool
class GotoTool:
    """Go to a URL."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(self, url: str) -> str:
        """
        Args:
            url (str): URL to go to
        """
        if not self.browser.has_current_page():
            await self.browser.open_tab()
        page = self.browser.get_current_page()
        await page.goto(url)
        await self.browser.wait()
        return f"Went to {url}"


@tool
class GoBackTool:
    """Navigate to the previous page in browser history."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(self, description: str) -> str:
        """
        Args:
            description (str): Why you're going back (e.g., 'Return to search results')
        """
        page = self.browser.get_current_page()
        await page.go_back()
        await self.browser.wait()
        return f"Went back: {description}"


@tool
class GoForwardTool:
    """Navigate to the next page in browser history."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(self, description: str) -> str:
        """
        Args:
            description (str): Why you're going forward (e.g., 'Return to product page')
        """
        page = self.browser.get_current_page()
        await page.go_forward()
        await self.browser.wait()
        return f"Went forward: {description}"


@tool
class SearchTool:
    """Navigate to the default search engine homepage."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(self, description: str) -> str:
        """
        Args:
            description (str): Why you're going to search (e.g., 'Start new search for product')
        """
        if not self.browser.has_current_page():
            await self.browser.open_tab()
        page = self.browser.get_current_page()
        await page.goto("https://www.google.com")
        await self.browser.wait()
        return f"Went to search: {description}"


@tool
class KeyCombinationTool:
    """Press keyboard keys or combinations (e.g., 'Control+C', 'Enter', 'Escape')."""

    def __init__(self, browser: "AgentBrowser"):
        self.browser = browser

    async def run(self, keys: str, description: str) -> str:
        """
        Args:
            keys (str): Keys to press (e.g., 'Control+C', 'Enter', 'Alt+Tab')
            description (str): What this key combination does (e.g., 'Copy selected text', 'Submit form')
        """
        page = self.browser.get_current_page()
        await page.keyboard_press(keys)
        await self.browser.wait()
        return f"Pressed {keys}: {description}"
