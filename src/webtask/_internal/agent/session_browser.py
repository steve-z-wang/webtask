"""SessionBrowser - pure browser operations without element mapping."""

from typing import Dict, List, Optional
from webtask.browser import Page, Context


class SessionBrowser:
    """Pure browser operations for context management."""

    def __init__(
        self,
        context: Optional[Context] = None,
        use_screenshot: bool = True,
    ):
        self._context = context
        self._use_screenshot = use_screenshot
        self._pages: Dict[str, Page] = {}
        self._page_counter = 0
        self._current_page_id: Optional[str] = None

    def get_current_page(self) -> Optional[Page]:
        """Get current page or None if no page is active."""
        if self._current_page_id is None:
            return None
        return self._pages[self._current_page_id]

    def _get_page_id(self, page: Page) -> Optional[str]:
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
            raise ValueError("Page not managed by AgentBrowser")

        await page.close()
        del self._pages[page_id]

        if self._current_page_id == page_id:
            if self._pages:
                self._current_page_id = next(iter(self._pages.keys()))
            else:
                self._current_page_id = None

    async def navigate(self, url: str) -> None:
        """Navigate to URL."""
        page = self.get_current_page()
        if page is None:
            if self._context is None:
                raise RuntimeError(
                    "Cannot navigate: no page available and no context to create one. "
                    "Use set_page() to inject a page, or set_context() to enable page creation."
                )
            page = await self.create_page()

        await page.navigate(url)

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
