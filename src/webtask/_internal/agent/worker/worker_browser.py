"""WorkerBrowser - browser interface for Worker with LLMDomContext."""

import asyncio
from typing import Optional
from ..session_browser import SessionBrowser
from ...context import LLMDomContext


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
        import base64

        screenshot_bytes = await self._session_browser.screenshot(full_page=full_page)
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    async def get_dom_snapshot(self) -> str:
        """Get DOM snapshot with interactive elements."""
        page = self._session_browser.get_current_page()
        if page is None:
            return "ERROR: No page opened yet."

        # Build LLMDomContext from current page
        self._dom_context = await LLMDomContext.from_page(page)

        # Get context string
        context_str = self._dom_context.get_context()

        # Format with URL
        url = page.url
        lines = ["Page:"]
        if url:
            lines.append(f"  URL: {url}")
        lines.append("")

        if not context_str:
            lines.append("ERROR: No interactive elements found.")
        else:
            lines.append(context_str)

        return "\n".join(lines)

    async def _select(self, interactive_id: str):
        """Select element by interactive ID."""
        page = self._session_browser.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")

        if self._dom_context is None:
            raise RuntimeError("Context not built yet. Call get_dom_snapshot() first.")

        dom_node = self._dom_context.get_dom_node(interactive_id)
        if dom_node is None:
            raise KeyError(f"Interactive ID '{interactive_id}' not found")

        xpath = dom_node.get_x_path()
        return await page.select_one(xpath)

    async def click(self, interactive_id: str) -> None:
        """Click element by interactive ID."""
        element = await self._select(interactive_id)
        await element.click()
        await asyncio.sleep(self._wait_after_action)

    async def fill(self, interactive_id: str, value: str) -> None:
        """Fill element by interactive ID."""
        element = await self._select(interactive_id)
        await element.fill(value)
        await asyncio.sleep(self._wait_after_action)

    async def type(self, interactive_id: str, text: str) -> None:
        """Type into element by interactive ID."""
        element = await self._select(interactive_id)
        await element.type(text)
        await asyncio.sleep(self._wait_after_action)

    async def upload(self, interactive_id: str, file_path: str) -> None:
        """Upload file to element by interactive ID."""
        element = await self._select(interactive_id)
        await element.upload_file(file_path)
        await asyncio.sleep(self._wait_after_action)

    async def navigate(self, url: str) -> None:
        """Navigate to URL and clear context."""
        await self._session_browser.navigate(url)
        self._dom_context = None
        await asyncio.sleep(self._wait_after_action)

    async def wait_for_idle(self, timeout: int = 30000) -> None:
        """Wait for page to be idle."""
        await self._session_browser.wait_for_idle(timeout=timeout)
