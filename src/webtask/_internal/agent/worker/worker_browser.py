"""WorkerBrowser - browser interface for Worker with page management and LLMDomContext."""

from typing import Dict, List, Optional
from webtask.browser import Page, Context
from ...context import LLMDomContext
from ...utils.wait import wait
import base64


class WorkerBrowser:
    """Worker browser with page management and interactive element mapping."""

    def __init__(
        self,
        context: Optional[Context] = None,
        wait_after_action: float = 0.2,
    ):
        self._context = context
        self._wait_after_action = wait_after_action

        # Page management (from SessionBrowser)
        self._pages: Dict[str, Page] = {}
        self._page_counter = 0
        self._current_page_id: Optional[str] = None

        # DOM context for element mapping
        self._dom_context: Optional[LLMDomContext] = None

    # Page management methods

    def get_current_page(self) -> Optional[Page]:
        """Get current page or None if no page is active."""
        if self._current_page_id is None:
            return None
        return self._pages[self._current_page_id]

    def _get_page_id(self, page: Page) -> Optional[str]:
        """Get page ID for a given page."""
        for page_id, p in self._pages.items():
            if p == page:
                return page_id
        return None

    def set_context(self, context: Context) -> None:
        """Set or update the context."""
        self._context = context

    async def create_page(self, url: Optional[str] = None) -> Page:
        """Create new page and switch to it."""
        if self._context is None:
            raise RuntimeError(
                "Cannot create page: no context available. "
                "Use set_context() first, or inject a page with set_page()."
            )

        page = await self._context.create_page()
        page_id = f"page-{self._page_counter}"
        self._page_counter += 1
        self._pages[page_id] = page
        self._current_page_id = page_id

        if url:
            await page.navigate(url)
            await wait(self._wait_after_action)

        return page

    def set_page(self, page: Page) -> None:
        """Set page as current page."""
        page_id = self._get_page_id(page)

        if page_id is None:
            page_id = f"page-{self._page_counter}"
            self._page_counter += 1
            self._pages[page_id] = page

        self._current_page_id = page_id

    async def close_page(self, page: Optional[Page] = None) -> None:
        """Close page."""
        if page is None:
            if self._current_page_id is None:
                return
            page = self._pages[self._current_page_id]

        page_id = self._get_page_id(page)
        if page_id is None:
            raise ValueError("Page not managed by WorkerBrowser")

        await page.close()
        del self._pages[page_id]

        if self._current_page_id == page_id:
            if self._pages:
                self._current_page_id = next(iter(self._pages.keys()))
            else:
                self._current_page_id = None

    def get_pages(self) -> List[Page]:
        """Get all managed pages."""
        return list(self._pages.values())

    @property
    def page_count(self) -> int:
        """Get number of managed pages."""
        return len(self._pages)

    async def close(self) -> None:
        """Close all managed pages."""
        for page in list(self._pages.values()):
            await self.close_page(page)

    # Browser operation methods

    def get_current_url(self) -> str:
        """Get current page URL."""
        page = self.get_current_page()
        return page.url if page else "about:blank"

    async def wait_for_load(self, timeout: int = 10000) -> None:
        """Wait for page to fully load."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        await page.wait_for_load(timeout=timeout)

    async def screenshot(
        self, path: Optional[str] = None, full_page: bool = False
    ) -> bytes:
        """Take screenshot of current page."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        return await page.screenshot(path=path, full_page=full_page)

    async def get_screenshot(self, full_page: bool = False) -> str:
        """Get screenshot as base64 string."""
        # Wait for page to be fully loaded before capturing (safety check)
        await self.wait_for_load(timeout=10000)

        screenshot_bytes = await self.screenshot(full_page=full_page)
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    async def get_dom_snapshot(self, mode: str = "accessibility") -> str:
        """Get DOM snapshot with interactive elements.

        Args:
            mode: "accessibility" (default) or "dom"
                - accessibility: Clean, filtered, role-based IDs (button-0)
                - dom: Complete, tag-based IDs (input-0), includes file inputs
        """

        # Wait for page to be fully loaded before capturing (safety check)
        await self.wait_for_load(timeout=10000)

        page = self.get_current_page()
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
        page = self.get_current_page()
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
        page = self.get_current_page()
        if page is None:
            if self._context is None:
                raise RuntimeError(
                    "Cannot navigate: no page available and no context to create one. "
                    "Use set_page() to inject a page, or set_context() to enable page creation."
                )
            page = await self.create_page()

        await page.navigate(url)
        self._dom_context = None
        await wait(self._wait_after_action)
