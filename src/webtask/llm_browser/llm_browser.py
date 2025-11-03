"""LLMBrowser - bridges text interface with browser operations."""

from typing import Dict, List, Optional, Union
from ..browser import Page, Session
from ..dom.domnode import DomNode
from ..llm import Block
from .dom_context_builder import DomContextBuilder
from .bounding_box_renderer import BoundingBoxRenderer


class LLMBrowser:
    """Bridges text interface with browser operations."""

    def __init__(
        self,
        session: Optional[Session] = None,
        use_screenshot: bool = True,
    ):
        """Initialize with optional Session and screenshot setting."""
        self._session = session
        self._use_screenshot = use_screenshot
        self._pages: Dict[str, Page] = {}
        self._page_counter = 0
        self._current_page_id: Optional[str] = None
        self._element_map: Dict[str, DomNode] = {}

    def _require_page(self) -> Page:
        if self._current_page_id is None:
            raise RuntimeError(
                "No active page. Use set_page() to inject a page, "
                "or create_page() with a session."
            )
        return self._pages[self._current_page_id]

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
        self._element_map.clear()

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
        self._element_map.clear()

    async def close_page(self, page: Optional[Page] = None) -> None:
        """Close page (closes current page if None)."""
        if page is None:
            if self._current_page_id is None:
                return
            page = self._pages[self._current_page_id]

        page_id = self._get_page_id(page)
        if page_id is None:
            raise ValueError("Page not managed by LLMBrowser")

        await page.close()
        del self._pages[page_id]

        if self._current_page_id == page_id:
            if self._pages:
                self._current_page_id = next(iter(self._pages.keys()))
                self._element_map.clear()
            else:
                self._current_page_id = None
                self._element_map.clear()

    async def get_page_context(self, full_page: bool = False) -> Block:
        """Get formatted page context for LLM.

        Args:
            full_page: Capture full scrollable page (default: False, viewport only)
                      Use True for element selection, False for agent actions.

        Returns:
            Block with text context and optional screenshot image (based on self.use_screenshot)
        """

        if self._current_page_id is None:
            self._element_map = {}
            lines = ["Page:"]
            lines.append("  URL: (no page loaded)")
            lines.append("")
            lines.append("ERROR: No page opened yet.")
            lines.append("Please use the navigate tool to navigate to a URL.")
            return Block("\n".join(lines))

        page = self._require_page()
        url = page.url

        context_str, element_map = await DomContextBuilder.build_context(page=page)

        self._element_map = element_map

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

        # Optionally include screenshot with bounding boxes
        image = None
        if self._use_screenshot and element_map:
            # Filter to only interactive elements for bounding boxes
            # (All elements have IDs in text context, but only show boxes for interactive ones)
            from ..dom_processing.knowledge import is_interactive

            interactive_elements = {
                element_id: node
                for element_id, node in element_map.items()
                if is_interactive(node)
            }

            image = await BoundingBoxRenderer.render(
                page=page, element_map=interactive_elements, full_page=full_page
            )

        return Block(text="\n".join(lines), image=image)

    def _get_xpath(self, element_id: str):
        """Get XPath for element by ID."""
        if element_id not in self._element_map:
            raise KeyError(f"Element ID '{element_id}' not found")

        # element_map already contains original unfiltered nodes from DomContextBuilder
        node = self._element_map[element_id]
        return node.get_x_path()

    async def navigate(self, url: str) -> None:
        """Navigate to URL. Auto-creates a page if none exists yet and session is available."""
        if self._current_page_id is None:
            if self._session is None:
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
        xpath = self._get_xpath(element_id)
        element = await page.select_one(xpath)
        await element.click()

    async def fill(self, element_id: str, value: str) -> None:
        """Fill element by ID with value."""
        page = self._require_page()
        xpath = self._get_xpath(element_id)
        element = await page.select_one(xpath)
        await element.fill(value)

    async def type(self, element_id: str, text: str, delay: float = 80) -> None:
        """Type text into element by ID character by character."""
        page = self._require_page()
        xpath = self._get_xpath(element_id)
        element = await page.select_one(xpath)
        await element.type(text, delay=delay)

    async def keyboard_type(
        self, text: str, clear: bool = False, delay: float = 80
    ) -> None:
        """Type text using keyboard into the currently focused element.

        Does not require selecting an element. The element must be focused first
        (usually by clicking it).
        """
        page = self._require_page()
        await page.keyboard_type(text, clear=clear, delay=delay)

    async def upload(self, element_id: str, file_paths: Union[str, List[str]]) -> None:
        """
        Upload file(s) to input element.

        Args:
            element_id: Element ID from DOM (e.g., "input-5")
            file_paths: Single file path or list of file paths
        """
        page = self._require_page()
        xpath = self._get_xpath(element_id)
        element = await page.select_one(xpath)
        await element.upload_file(file_paths)
