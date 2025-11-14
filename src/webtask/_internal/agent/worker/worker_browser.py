"""WorkerBrowser - adds element mapping layer on top of AgentBrowser."""

from typing import Dict
from webtask._internal.dom.domnode import DomNode
from ..agent_browser import AgentBrowser
from ...page_context.dom_context_builder import DomContextBuilder


class WorkerBrowser:
    """Worker-specific browser with element mapping.

    Wraps AgentBrowser and adds element ID mapping for Worker interactions.
    Provides select(element_id) to get browser elements by ID.
    NO throttling - that's handled by Worker.
    """

    def __init__(self, agent_browser: AgentBrowser):
        """Initialize WorkerBrowser.

        Args:
            agent_browser: Shared AgentBrowser instance
        """
        self._agent_browser = agent_browser
        self._element_map: Dict[str, DomNode] = {}

    def _get_xpath(self, element_id: str):
        """Get XPath for element by ID."""
        if element_id not in self._element_map:
            raise KeyError(f"Element ID '{element_id}' not found")

        node = self._element_map[element_id]
        return node.get_x_path()

    async def select(self, element_id: str):
        """Select element by ID and return the browser element.

        Args:
            element_id: Element ID from DOM (e.g., "button-0")

        Returns:
            Browser Element that can be interacted with (click, fill, type, etc.)
        """
        page = self._agent_browser.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")

        xpath = self._get_xpath(element_id)
        return await page.select_one(xpath)

    async def click(self, element_id: str) -> None:
        """Click element by ID."""
        element = await self.select(element_id)
        await element.click()

    async def fill(self, element_id: str, value: str) -> None:
        """Fill element by ID."""
        element = await self.select(element_id)
        await element.fill(value)

    async def type(self, element_id: str, text: str) -> None:
        """Type into element by ID."""
        element = await self.select(element_id)
        await element.type(text)

    async def upload(self, element_id: str, file_path: str) -> None:
        """Upload file to element by ID."""
        element = await self.select(element_id)
        await element.upload_file(file_path)

    async def navigate(self, url: str) -> None:
        """Navigate to URL and clear element map."""
        await self._agent_browser.navigate(url)
        self._element_map.clear()

    async def wait_for_idle(self, timeout: int = 30000) -> None:
        """Wait for page to be idle (network and DOM stable)."""
        await self._agent_browser.wait_for_idle(timeout=timeout)

    async def get_screenshot(self, full_page: bool = False) -> str:
        """Get screenshot as base64 string.

        Args:
            full_page: Whether to capture full page screenshot

        Returns:
            Base64-encoded screenshot string
        """
        import base64

        page = self._agent_browser.get_current_page()
        if page is None:
            # Return empty image if no page
            return ""

        # Get screenshot bytes
        screenshot_bytes = await page.screenshot(full_page=full_page)

        # Convert to base64
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    def get_current_url(self) -> str:
        """Get current page URL.

        Returns:
            Current URL or "about:blank" if no page
        """
        page = self._agent_browser.get_current_page()
        return page.url if page else "about:blank"

    async def get_dom_snapshot(self, include_element_ids: bool = True) -> str:
        """Get DOM snapshot as formatted string.

        Args:
            include_element_ids: Whether to include element IDs in the output

        Returns:
            Formatted DOM snapshot string with URL and interactive elements
        """
        page = self._agent_browser.get_current_page()
        if page is None:
            return "ERROR: No page opened yet.\nPlease use the navigate tool to navigate to a URL."

        # Build DOM context
        context_str, element_map = await DomContextBuilder.build_context(
            page=page, include_element_ids=include_element_ids
        )

        # Update element map if IDs are included
        if include_element_ids and element_map:
            self._element_map = element_map

        # Format with URL
        url = page.url
        lines = ["Page:"]
        if url:
            lines.append(f"  URL: {url}")
        lines.append("")

        if context_str is None:
            lines.append("ERROR: No visible interactive elements found on this page.")
            lines.append("")
            lines.append("Possible causes:")
            lines.append("- The page is still loading")
            lines.append("- The page has no interactive elements")
            lines.append("- All elements were filtered out")
        else:
            lines.append(context_str)

        return "\n".join(lines)
