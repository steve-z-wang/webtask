"""AgentBrowser - pure browser operations without element mapping."""

from typing import Dict, List, Optional
from webtask.browser import Page, Session


class AgentBrowser:
    """Pure browser operations for Agent.

    Manages pages and basic browser operations.
    NO element mapping - that's in WorkerBrowser.
    NO throttling - that's in Worker and Verifier.

    Shared by Worker (via WorkerBrowser wrapper) and Verifier (for screenshots).
    """

    def __init__(
        self,
        session: Optional[Session] = None,
        use_screenshot: bool = True,
    ):
        """Initialize AgentBrowser.

        Args:
            session: Optional browser session
            use_screenshot: Whether to include screenshots in context
        """
        self._session = session
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

    def set_session(self, session: Session) -> None:
        """Set or update the session for multi-page operations."""
        self._session = session

    async def create_page(self, url: Optional[str] = None) -> Page:
        """Create new page and switch to it. Requires a session."""
        if self._session is None:
            raise RuntimeError(
                "Cannot create page: no session available. "
                "Use set_session() first, or inject a page with set_page()."
            )

        page = await self._session.create_page()
        page_id = f"page-{self._page_counter}"
        self._page_counter += 1
        self._pages[page_id] = page
        self._current_page_id = page_id

        if url:
            await page.navigate(url)

        return page

    def set_page(self, page: Page) -> None:
        """Set/inject/switch to a page as the current page."""
        page_id = self._get_page_id(page)

        if page_id is None:
            page_id = f"page-{self._page_counter}"
            self._page_counter += 1
            self._pages[page_id] = page

        self._current_page_id = page_id

    async def close_page(self, page: Optional[Page] = None) -> None:
        """Close page (closes current page if None)."""
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
        """Navigate to URL. Auto-creates a page if none exists yet and session is available."""
        page = self.get_current_page()
        if page is None:
            if self._session is None:
                raise RuntimeError(
                    "Cannot navigate: no page available and no session to create one. "
                    "Use set_page() to inject a page, or set_session() to enable page creation."
                )
            page = await self.create_page()

        await page.navigate(url)

    async def wait_for_idle(self, timeout: int = 30000) -> None:
        """
        Wait for page to be idle (network and DOM stable).

        Args:
            timeout: Maximum time to wait in milliseconds (default: 30000ms)

        Raises:
            RuntimeError: If no page is opened
            TimeoutError: If page doesn't become idle within timeout
        """
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        await page.wait_for_idle(timeout=timeout)

    async def screenshot(
        self, path: Optional[str] = None, full_page: bool = False
    ) -> bytes:
        """
        Take a screenshot of the current page.

        Args:
            path: Optional file path to save screenshot
            full_page: Whether to screenshot the full scrollable page (default: False)

        Returns:
            Screenshot as bytes (PNG format)

        Raises:
            RuntimeError: If no page is opened
        """
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        return await page.screenshot(path=path, full_page=full_page)

    def get_pages(self) -> List[Page]:
        """Get all managed pages.

        Returns:
            List of all Page instances
        """
        return list(self._pages.values())

    @property
    def page_count(self) -> int:
        """Get number of managed pages.

        Returns:
            Number of pages
        """
        return len(self._pages)

    async def close(self) -> None:
        """Close all managed pages."""
        for page in list(self._pages.values()):
            await self.close_page(page)
