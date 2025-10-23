"""LLMBrowser - bridges LLM text interface with browser operations."""

from typing import Dict, Optional
from ..browser import Page, Element, Session
from ..dom.filters import apply_visibility_filters, apply_semantic_filters
from ..dom.utils import add_node_reference
from ..dom.domnode import DomNode
from ..llm import Block, LLM


class LLMBrowser:
    """
    Bridges LLM text interface with browser operations.

    Manages multiple pages internally and provides context with element IDs.
    """

    def __init__(self, llm: LLM, session: Session):
        """
        Initialize with LLM and Session.

        Args:
            llm: LLM instance for natural language selection
            session: Session instance for creating pages
        """
        self.llm = llm
        self.session = session
        self._pages: Dict[str, Page] = {}  # page_id -> Page
        self._page_counter = 0
        self.current_page_id: Optional[str] = None
        self.element_map: Dict[str, DomNode] = {}

    def get_current_page(self) -> Page:
        """
        Get current page.

        Returns:
            Current Page instance

        Raises:
            RuntimeError: If no page is active
        """
        if self.current_page_id is None:
            raise RuntimeError("No active page. Create a page first.")
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

    async def create_page(self, url: Optional[str] = None) -> Page:
        """
        Create new page and switch to it.

        Args:
            url: Optional URL to navigate to

        Returns:
            Page instance
        """
        page = await self.session.create_page()
        page_id = f"page-{self._page_counter}"
        self._page_counter += 1
        self._pages[page_id] = page
        self.current_page_id = page_id
        self.element_map.clear()

        if url:
            await page.navigate(url)

        return page

    def switch_page(self, page: Page) -> None:
        """
        Switch to existing page.

        Args:
            page: Page instance to switch to

        Raises:
            ValueError: If page is not managed by this LLMBrowser
        """
        page_id = self._get_page_id(page)
        if page_id is None:
            raise ValueError("Page not managed by LLMBrowser")

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

    async def to_context_block(self) -> Block:
        """
        Get formatted page context with element IDs for LLM.

        Returns:
            Block with formatted DOM
        """
        # Case 1: No page opened yet
        if self.current_page_id is None:
            return Block("Page:\nERROR: No page opened yet. Please use the navigate tool to navigate to a URL.")

        # Get raw snapshot from current page
        page = self.get_current_page()
        snapshot = await page.get_snapshot()
        root = snapshot.root

        # Add node references (before filtering)
        root = add_node_reference(root)

        # Apply filters
        root = apply_visibility_filters(root)
        root = apply_semantic_filters(root)

        # Handle case where filtering removes everything
        if root is None:
            lines = ["Page:"]

            # Case 2: Page opened but no URL (not navigated)
            if not snapshot.url or snapshot.url == "about:blank":
                lines.append("  URL: (no page loaded)")
                lines.append("")
                lines.append("ERROR: No URL loaded yet.")
                lines.append("Please use the navigate tool to navigate to a URL.")
            # Case 3: Navigated to URL but no elements
            else:
                lines.append(f"  URL: {snapshot.url}")
                lines.append("")
                lines.append("ERROR: No visible interactive elements found on this page.")
                lines.append("")
                lines.append("Possible causes:")
                lines.append("- The page is still loading")
                lines.append("- The page has no interactive elements")
                lines.append("- All elements were filtered out")

            return Block("\n".join(lines))

        # Assign element IDs and build mapping
        self.element_map = {}
        tag_counters: Dict[str, int] = {}

        for node in root.traverse():
            if isinstance(node, DomNode):
                tag = node.tag
                count = tag_counters.get(tag, 0)
                element_id = f"{tag}-{count}"

                node.metadata['element_id'] = element_id
                self.element_map[element_id] = node

                tag_counters[tag] = count + 1

        # Serialize to markdown
        from ..dom.serializers import serialize_to_markdown
        lines = ["Page:"]

        if snapshot.url:
            lines.append(f"  URL: {snapshot.url}")
            lines.append("")

        lines.append(serialize_to_markdown(root))

        return Block("\n".join(lines))

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

        Auto-creates a page if none exists yet.

        Args:
            url: URL to navigate to
        """
        # Auto-create page if none exists
        if self.current_page_id is None:
            await self.create_page()

        page = self.get_current_page()
        await page.navigate(url)

    async def click(self, element_id: str) -> None:
        """
        Click element by ID.

        Args:
            element_id: Element ID from context (e.g., 'button-0')

        Raises:
            KeyError: If element ID not found
        """
        page = self.get_current_page()
        selector = self._get_selector(element_id)
        element = await page.select_one(selector)
        await element.click()

    async def fill(self, element_id: str, value: str) -> None:
        """
        Fill element by ID with value.

        Args:
            element_id: Element ID from context (e.g., 'input-0')
            value: Value to fill

        Raises:
            KeyError: If element ID not found
        """
        page = self.get_current_page()
        selector = self._get_selector(element_id)
        element = await page.select_one(selector)
        await element.fill(value)

    async def type(self, element_id: str, text: str, delay: float = 80) -> None:
        """
        Type text into element by ID character by character.

        Simulates realistic keyboard input with delays between keystrokes.

        Args:
            element_id: Element ID from context (e.g., 'input-0')
            text: Text to type
            delay: Delay between keystrokes in milliseconds (default: 80ms)

        Raises:
            KeyError: If element ID not found
        """
        page = self.get_current_page()
        selector = self._get_selector(element_id)
        element = await page.select_one(selector)
        await element.type(text, delay=delay)

    async def select(self, description: str) -> Element:
        """
        Select element by natural language description.

        Uses LLM to find the element_id that matches the description,
        then converts it to a selector and returns the browser Element.

        Args:
            description: Natural language description of element

        Returns:
            Browser Element instance

        Raises:
            ValueError: If LLM fails to find a matching element
        """
        from .selector import NaturalSelector

        selector = NaturalSelector(self.llm, self)
        return await selector.select(description)
