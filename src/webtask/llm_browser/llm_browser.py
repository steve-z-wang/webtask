"""LLMBrowser - bridges text interface with browser operations."""

from typing import Dict, Optional
from ..browser import Page, Session
from ..dom.domnode import DomNode
from ..dom.dom_context_config import DomContextConfig
from ..llm import Block
from .web_context_builder import WebContextBuilder


class LLMBrowser:
    """
    Bridges text interface with browser operations.

    Manages multiple pages internally and provides context with element IDs.
    Does NOT depend on LLM - pure page management and context building.
    """

    def __init__(
        self,
        session: Optional[Session] = None,
        dom_context_config: Optional[DomContextConfig] = None,
    ):
        """
        Initialize with optional Session.

        Args:
            session: Optional Session instance for creating pages.
                     If None, use set_session() or set_page() to configure.
            dom_context_config: Configuration for DOM filtering. If None, uses defaults.
        """
        self.session = session
        self.dom_context_config = dom_context_config or DomContextConfig()
        self._pages: Dict[str, Page] = {}  # page_id -> Page
        self._page_counter = 0
        self.current_page_id: Optional[str] = None
        self.element_map: Dict[str, DomNode] = {}

    def _require_page(self) -> Page:
        """
        Get current page or raise error.

        Internal method for operations that require a page.

        Returns:
            Current Page instance

        Raises:
            RuntimeError: If no page is active
        """
        if self.current_page_id is None:
            raise RuntimeError(
                "No active page. Use set_page() to inject a page, "
                "or create_page() with a session."
            )
        return self._pages[self.current_page_id]

    def get_current_page(self) -> Optional[Page]:
        """
        Get current page.

        Returns:
            Current Page instance or None if no page is active
        """
        if self.current_page_id is None:
            return None
        return self._pages[self.current_page_id]

    def _get_page_id(self, page: Page) -> Optional[str]:
        """
        Get page_id from Page object.

        Args:
            page: Page instance

        Returns:
            Page ID string or None if not found
        """
        for page_id, p in self._pages.items():
            if p == page:
                return page_id
        return None

    def set_session(self, session: Session) -> None:
        """
        Set or update the session.

        Enables multi-tab operations via create_page().

        Args:
            session: Session instance for creating pages

        Example:
            >>> agent = Agent(llm, page=my_page)  # Single page mode
            >>> agent.llm_browser.set_session(my_session)  # Enable multi-page
            >>> await agent.open_page("https://google.com")  # Now works!
        """
        self.session = session

    async def create_page(self, url: Optional[str] = None) -> Page:
        """
        Create new page and switch to it.

        Requires a session. Use set_session() if not provided at init.

        Args:
            url: Optional URL to navigate to

        Returns:
            Page instance

        Raises:
            RuntimeError: If no session is available
        """
        if self.session is None:
            raise RuntimeError(
                "Cannot create page: no session available. "
                "Use set_session() first, or inject a page with set_page()."
            )

        page = await self.session.create_page()
        page_id = f"page-{self._page_counter}"
        self._page_counter += 1
        self._pages[page_id] = page
        self.current_page_id = page_id
        self.element_map.clear()

        if url:
            await page.navigate(url)

        return page

    def set_page(self, page: Page) -> None:
        """
        Set/inject/switch to a page as the current page.

        Handles multiple use cases:
        - If page is already managed, switches to it
        - If page is new, adds it to managed pages and switches to it

        Args:
            page: Page instance to set as current

        Examples:
            >>> # Inject external Playwright page
            >>> from webtask.integrations.browser.playwright import PlaywrightPage
            >>> wrapped_page = PlaywrightPage(my_playwright_page)
            >>> llm_browser.set_page(wrapped_page)
            >>>
            >>> # Switch between managed pages
            >>> llm_browser.set_page(page1)
        """
        # Check if page is already managed
        page_id = self._get_page_id(page)

        if page_id is None:
            # New page - add it to managed pages
            page_id = f"page-{self._page_counter}"
            self._page_counter += 1
            self._pages[page_id] = page

        # Switch to this page
        self.current_page_id = page_id
        self.element_map.clear()

    async def close_page(self, page: Optional[Page] = None) -> None:
        """
        Close page (closes current page if None).

        Args:
            page: Page to close (defaults to current page)

        Raises:
            ValueError: If page is not managed by this LLMBrowser
        """
        # Get page to close
        if page is None:
            if self.current_page_id is None:
                return  # No pages to close
            page = self._pages[self.current_page_id]

        # Find page_id
        page_id = self._get_page_id(page)
        if page_id is None:
            raise ValueError("Page not managed by LLMBrowser")

        # Close and remove
        await page.close()
        del self._pages[page_id]

        # If closed current page, switch to another or None
        if self.current_page_id == page_id:
            if self._pages:
                self.current_page_id = next(iter(self._pages.keys()))
                self.element_map.clear()
            else:
                self.current_page_id = None
                self.element_map.clear()

    async def build_context(self) -> Block:
        """
        Build formatted page context with element IDs for LLM.

        Returns:
            Block with formatted DOM and updates self.element_map

        Raises:
            RuntimeError: If no page is active
        """
        # Case 1: No page opened yet
        if self.current_page_id is None:
            self.element_map = {}
            return Block("Page:\nERROR: No page opened yet. Use set_page() to inject a page or navigate to a URL.")

        # Use WebContextBuilder to build context
        page = self._require_page()
        context_str, element_map = await WebContextBuilder.build_context(
            page=page,
            dom_context_config=self.dom_context_config
        )

        # Update element map
        self.element_map = element_map

        # Wrap in Block and return
        return Block(context_str)

    async def to_context_block(self) -> Block:
        """
        Get formatted page context with element IDs for LLM.

        DEPRECATED: Use build_context() instead.
        Kept for backwards compatibility.

        Returns:
            Block with formatted DOM
        """
        return await self.build_context()

    def _get_selector(self, element_id: str):
        """
        Convert element ID to selector (XPath or CSS).

        Args:
            element_id: Element ID (e.g., 'div-0', 'button-1')

        Returns:
            XPath object or CSS selector string

        Raises:
            KeyError: If element ID not found
        """
        if element_id not in self.element_map:
            raise KeyError(f"Element ID '{element_id}' not found")

        node = self.element_map[element_id]
        # Get the original unfiltered node to compute XPath from the full DOM tree
        original_node = node.metadata.get('original_node', node)
        # Use XPath for now (could be CSS selector in future)
        return original_node.get_x_path()

    async def navigate(self, url: str) -> None:
        """
        Navigate to URL.

        Auto-creates a page if none exists yet and session is available.

        Args:
            url: URL to navigate to

        Raises:
            RuntimeError: If no page exists and no session to create one
        """
        # Auto-create page if none exists (requires session)
        if self.current_page_id is None:
            if self.session is None:
                raise RuntimeError(
                    "Cannot navigate: no page available and no session to create one. "
                    "Use set_page() to inject a page, or set_session() to enable page creation."
                )
            await self.create_page()

        page = self._require_page()
        await page.navigate(url)

    async def click(self, element_id: str) -> None:
        """
        Click element by ID.

        Args:
            element_id: Element ID from context (e.g., 'button-0')

        Raises:
            KeyError: If element ID not found
            RuntimeError: If no page is active
        """
        page = self._require_page()
        selector = self._get_selector(element_id)
        element = await page.select_one(selector)
        await element.click()

    async def keyboard_type(self, text: str, clear: bool = False, delay: float = 80) -> None:
        """
        Type text using keyboard into the currently focused element.

        Does not require selecting an element. The element must be focused first
        (usually by clicking it).

        Args:
            text: Text to type
            clear: Clear existing text before typing (default: False)
            delay: Delay between keystrokes in milliseconds (default: 80ms)

        Raises:
            RuntimeError: If no page is active

        Example:
            >>> # Click to focus input
            >>> await llm_browser.click("input-0")
            >>> # Type into focused element
            >>> await llm_browser.keyboard_type("Hello World")
            >>>
            >>> # Clear and type
            >>> await llm_browser.click("input-1")
            >>> await llm_browser.keyboard_type("New text", clear=True)
        """
        page = self._require_page()
        await page.keyboard_type(text, clear=clear, delay=delay)
