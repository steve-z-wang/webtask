"""AgentBrowser - browser interface for agent with page management and LLMDomContext."""

from typing import List, Optional, Union
from webtask.browser import Page, Context
from ..context import LLMDomContext
from ..utils.wait import wait
import base64


class AgentBrowser:
    """Agent browser with page management and interactive element mapping."""

    def __init__(
        self,
        context: Optional[Context] = None,
        wait_after_action: float = 0.2,
        mode: str = "accessibility",
    ):
        self._context = context
        self._wait_after_action = wait_after_action
        self._mode = mode

        # Page management - ordered list of pages
        self._pages: List[Page] = []
        self._current_page_index: Optional[int] = None

        # DOM context for element mapping
        self._dom_context: Optional[LLMDomContext] = None

    # Page management methods

    def _sync_pages(self) -> None:
        """Sync internal page list with context.pages.

        Adds new pages from context, removes closed pages.
        Maintains our own ordering (new pages appended).
        """
        if self._context is None:
            return

        context_pages = self._context.pages

        # Wrap raw pages if needed (context.pages may return raw Playwright pages)
        from webtask.integrations.browser.playwright import PlaywrightPage

        wrapped_context_pages = []
        for p in context_pages:
            if isinstance(p, Page):
                wrapped_context_pages.append(p)
            else:
                # Assume it's a raw Playwright page
                wrapped_context_pages.append(PlaywrightPage(p))

        # Remove pages that no longer exist in context
        self._pages = [
            p for p in self._pages if any(p == cp for cp in wrapped_context_pages)
        ]

        # Add new pages from context (append to maintain order)
        for cp in wrapped_context_pages:
            if not any(cp == p for p in self._pages):
                self._pages.append(cp)

        # Fix current_page_index if it's now invalid
        if self._current_page_index is not None:
            if self._current_page_index >= len(self._pages):
                self._current_page_index = len(self._pages) - 1 if self._pages else None

    def get_current_page(self) -> Optional[Page]:
        """Get current page or None if no page is active."""
        if self._current_page_index is None:
            return None
        if self._current_page_index >= len(self._pages):
            return None
        return self._pages[self._current_page_index]

    def set_context(self, context: Context) -> None:
        """Set or update the context."""
        self._context = context

    def set_wait_after_action(self, wait_after_action: float) -> None:
        """Set wait_after_action duration."""
        self._wait_after_action = wait_after_action

    def set_mode(self, mode: str) -> None:
        """Set DOM snapshot mode."""
        self._mode = mode

    async def open_tab(self) -> Page:
        """Open a new blank tab and focus it."""
        if self._context is None:
            raise RuntimeError(
                "Cannot open tab: no context available. Use set_context() first."
            )

        page = await self._context.create_page()
        self._pages.append(page)
        self._current_page_index = len(self._pages) - 1

        return page

    def focus_tab(self, tab: Union[int, Page]) -> None:
        """Focus a tab by number (1-based) or page reference.

        Args:
            tab: Either a 1-based tab number or a Page object
        """
        self._sync_pages()

        if isinstance(tab, int):
            # By number (1-based)
            if tab < 1 or tab > len(self._pages):
                raise IndexError(
                    f"Tab number {tab} out of range (1-{len(self._pages)})"
                )
            self._current_page_index = tab - 1
        else:
            # By page reference
            for i, p in enumerate(self._pages):
                if p == tab:
                    self._current_page_index = i
                    return
            raise ValueError("Tab not found")

    def get_tabs_context(self) -> str:
        """Get tabs context string for LLM.

        Returns:
            Formatted tabs section showing all open tabs with 1-based numbers.
            Example:
                Tabs:
                1. https://google.com
                2. https://example.com (current)
        """
        self._sync_pages()

        if not self._pages:
            return "Tabs:\n(no pages open)"

        lines = ["Tabs:"]
        for idx, page in enumerate(self._pages):
            url = page.url if page.url else "about:blank"
            current_marker = " (current)" if idx == self._current_page_index else ""
            lines.append(f"{idx + 1}. {url}{current_marker}")

        return "\n".join(lines)

    async def close(self) -> None:
        """Close all managed pages."""
        for page in list(self._pages):
            await page.close()
        self._pages = []
        self._current_page_index = None

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

    async def get_screenshot(self, full_page: bool = False) -> Optional[str]:
        """Get screenshot as base64 string.

        Returns None if no page is open.
        """
        page = self.get_current_page()
        if page is None:
            return None

        # Wait for page to be fully loaded before capturing (safety check)
        await self.wait_for_load(timeout=10000)

        screenshot_bytes = await self.screenshot(full_page=full_page)
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    async def get_dom_snapshot(self) -> str:
        """Get DOM snapshot with interactive elements.

        Uses the current mode setting (set via set_mode()).

        Returns:
            DOM snapshot string, or empty string if no page is open
        """
        page = self.get_current_page()
        if page is None:
            return ""

        # Wait for page to be fully loaded before capturing (safety check)
        await self.wait_for_load(timeout=10000)

        # Build LLMDomContext from current page
        self._dom_context = await LLMDomContext.from_page(page)

        # Get context string with current mode
        context_str = self._dom_context.get_context(mode=self._mode)

        # Simple format: Current Tab: followed by DOM content
        lines = ["Current Tab:"]
        if not context_str:
            lines.append("(no interactive elements found)")
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
                    "Cannot navigate: no tab available and no context to create one. "
                    "Use focus_tab() to select a tab, or set_context() to enable tab creation."
                )
            page = await self.open_tab()

        await page.navigate(url)
        self._dom_context = None
        await wait(self._wait_after_action)
