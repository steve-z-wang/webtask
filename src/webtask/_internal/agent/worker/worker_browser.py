"""WorkerBrowser - browser interface for Worker with LLMDomContext."""

from typing import Optional
from ..session_browser import SessionBrowser
from ...context import LLMDomContext
from ...utils.wait import wait
import base64


class WorkerBrowser:
    """Worker-specific browser with interactive element mapping."""

    def __init__(self, session_browser: SessionBrowser, wait_after_action: float):
        self._session_browser = session_browser
        self._dom_context: Optional[LLMDomContext] = None
        self._wait_after_action = wait_after_action

    def get_current_url(self) -> str:
        """Get current page URL."""
        page = self._session_browser.get_current_page()
        return page.url if page else "about:blank"

    async def get_screenshot(self, full_page: bool = False) -> str:
        """Get screenshot as base64 string."""
        # Wait for page to be fully loaded before capturing (safety check)
        await self._session_browser.wait_for_load(timeout=10000)

        screenshot_bytes = await self._session_browser.screenshot(full_page=full_page)
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    async def get_dom_snapshot(self, mode: str = "accessibility") -> str:
        """Get DOM snapshot with interactive elements.

        Args:
            mode: "accessibility" (default) or "dom"
                - accessibility: Clean, filtered, role-based IDs (button-0)
                - dom: Complete, tag-based IDs (input-0), includes file inputs
        """

        # Wait for page to be fully loaded before capturing (safety check)
        await self._session_browser.wait_for_load(timeout=10000)

        page = self._session_browser.get_current_page()
        if page is None:
            return "ERROR: No page opened yet."

        # Build LLMDomContext from current page
        self._dom_context = await LLMDomContext.from_page(page)

        # Get context string with mode
        context_str = self._dom_context.get_context(mode=mode)

        # Format with URL and element ID explanation
        url = page.url
        lines = ["Page:"]
        if url:
            lines.append(f"  URL: {url}")
        lines.append("")

        # Add format explanation based on mode
        if mode == "accessibility":
            lines.append(
                "Elements use role-based IDs (e.g., button-0, combobox-1, link-2)."
            )
            lines.append("Always use the exact element IDs shown below.")
        else:  # dom mode
            lines.append("Elements use tag-based IDs (e.g., input-0, button-1, a-2).")
            lines.append("Always use the exact element IDs shown below.")
        lines.append("")

        if not context_str:
            lines.append("ERROR: No interactive elements found.")
        else:
            lines.append(context_str)

        return "\n".join(lines)

    async def _select(self, id: str):
        """Select element by ID (role_id or tag_id depending on mode)."""
        page = self._session_browser.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")

        if self._dom_context is None:
            raise RuntimeError("Context not built yet. Call get_dom_snapshot() first.")

        dom_node = self._dom_context.get_dom_node(id)
        if dom_node is None:
            raise KeyError(f"Element ID '{id}' not found")

        xpath = dom_node.get_x_path()
        return await page.select_one(xpath)

    async def click(self, id: str) -> None:
        """Click element by ID."""
        element = await self._select(id)
        await element.click()
        await wait(self._wait_after_action)

    async def fill(self, id: str, value: str) -> None:
        """Fill element by ID."""
        element = await self._select(id)
        await element.fill(value)
        await wait(self._wait_after_action)

    async def type(self, id: str, text: str) -> None:
        """Type into element by ID."""
        element = await self._select(id)
        await element.type(text)
        await wait(self._wait_after_action)

    async def upload(self, id: str, file_path: str) -> None:
        """Upload file to element by ID."""
        element = await self._select(id)
        await element.upload_file(file_path)
        await wait(self._wait_after_action)

    async def navigate(self, url: str) -> None:
        """Navigate to URL and clear context."""
        await self._session_browser.navigate(url)
        self._dom_context = None
        await wait(self._wait_after_action)

    async def wait_for_load(self, timeout: int = 10000) -> None:
        """Wait for page to fully load."""
        await self._session_browser.wait_for_load(timeout=timeout)
