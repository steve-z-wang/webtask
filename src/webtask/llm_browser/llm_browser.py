"""LLMBrowser - bridges text interface with browser operations."""

from typing import Dict, Optional
from ..browser import Page, Session
from ..dom.domnode import DomNode
from ..dom.dom_context_config import DomContextConfig
from ..llm import Block
from .web_context_builder import WebContextBuilder


class LLMBrowser:
    """Bridges text interface with browser operations."""

    def __init__(
        self,
        session: Optional[Session] = None,
        dom_context_config: Optional[DomContextConfig] = None,
    ):
        """Initialize with optional Session and DOM configuration."""
        self.session = session
        self.dom_context_config = dom_context_config or DomContextConfig()
        self._pages: Dict[str, Page] = {}
        self._page_counter = 0
        self.current_page_id: Optional[str] = None
        self.element_map: Dict[str, DomNode] = {}

    def _require_page(self) -> Page:
        if self.current_page_id is None:
            raise RuntimeError(
                "No active page. Use set_page() to inject a page, "
                "or create_page() with a session."
            )
        return self._pages[self.current_page_id]

    def get_current_page(self) -> Optional[Page]:
        """Get current page or None if no page is active."""
        if self.current_page_id is None:
            return None
        return self._pages[self.current_page_id]

    def _get_page_id(self, page: Page) -> Optional[str]:
        for page_id, p in self._pages.items():
            if p == page:
                return page_id
        return None

    def set_session(self, session: Session) -> None:
        """Set or update the session for multi-page operations."""
        self.session = session

    async def create_page(self, url: Optional[str] = None) -> Page:
        """Create new page and switch to it. Requires a session."""
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
        """Set/inject/switch to a page as the current page."""
        page_id = self._get_page_id(page)

        if page_id is None:
            page_id = f"page-{self._page_counter}"
            self._page_counter += 1
            self._pages[page_id] = page

        self.current_page_id = page_id
        self.element_map.clear()

    async def close_page(self, page: Optional[Page] = None) -> None:
        """Close page (closes current page if None)."""
        if page is None:
            if self.current_page_id is None:
                return
            page = self._pages[self.current_page_id]

        page_id = self._get_page_id(page)
        if page_id is None:
            raise ValueError("Page not managed by LLMBrowser")

        await page.close()
        del self._pages[page_id]

        if self.current_page_id == page_id:
            if self._pages:
                self.current_page_id = next(iter(self._pages.keys()))
                self.element_map.clear()
            else:
                self.current_page_id = None
                self.element_map.clear()

    async def to_context_block(self) -> Block:
        """Get formatted page context with element IDs for LLM."""
        
        if self.current_page_id is None:
            self.element_map = {}
            return Block("Page:\nERROR: No page opened yet. Use set_page() to inject a page or navigate to a URL.")

        page = self._require_page()
        context_str, element_map = await WebContextBuilder.build_context(
            page=page,
            dom_context_config=self.dom_context_config
        )

        self.element_map = element_map
        return Block(context_str)

    def _get_selector(self, element_id: str):
        if element_id not in self.element_map:
            raise KeyError(f"Element ID '{element_id}' not found")

        node = self.element_map[element_id]
        # Get the original unfiltered node to compute XPath from the full DOM tree
        original_node = node.metadata.get('original_node', node)
        return original_node.get_x_path()

    async def navigate(self, url: str) -> None:
        """Navigate to URL. Auto-creates a page if none exists yet and session is available."""
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
        """Click element by ID."""
        page = self._require_page()
        selector = self._get_selector(element_id)
        element = await page.select_one(selector)
        await element.click()

    async def keyboard_type(self, text: str, clear: bool = False, delay: float = 80) -> None:
        """Type text using keyboard into the currently focused element.

        Does not require selecting an element. The element must be focused first
        (usually by clicking it).
        """
        page = self._require_page()
        await page.keyboard_type(text, clear=clear, delay=delay)
