"""AgentBrowser - browser interface for agent with page management and LLMDomContext."""

from typing import List, Optional, Tuple, Union
from webtask.browser import Page, Context, Element
from webtask.llm.message import Content, ImageMimeType
from .message import AgentText, AgentImage
from ..context import LLMDomContext
import base64


class AgentBrowser:
    """Agent browser with page management and interactive element mapping."""

    def __init__(
        self,
        context: Optional[Context] = None,
        mode: str = "accessibility",
        coordinate_scale: Optional[int] = None,
    ):
        self._context = context
        self._mode = mode
        self._coordinate_scale = coordinate_scale
        self._pages: List[Page] = []
        self._current_page_index: Optional[int] = None
        self._dom_context: Optional[LLMDomContext] = None

    # Setters

    def set_context(self, context: Context) -> None:
        """Set or update the context."""
        self._context = context

    def set_mode(self, mode: str) -> None:
        """Set DOM snapshot mode."""
        self._mode = mode

    def set_coordinate_scale(self, scale: Optional[int]) -> None:
        """Set coordinate scale for pixel-based tools."""
        self._coordinate_scale = scale

    # Getters

    def has_current_page(self) -> bool:
        """Check if there is an active page."""
        if self._current_page_index is None:
            return False
        if self._current_page_index >= len(self._pages):
            return False
        return True

    def get_current_page(self) -> Page:
        """Get current page. Raises RuntimeError if no page is active."""
        if self._current_page_index is None:
            raise RuntimeError("No page is currently open")
        if self._current_page_index >= len(self._pages):
            raise RuntimeError("No page is currently open")
        return self._pages[self._current_page_index]

    def get_current_url(self) -> str:
        """Get current page URL."""
        if not self.has_current_page():
            return "about:blank"
        return self.get_current_page().url

    def get_viewport_size(self) -> Tuple[int, int]:
        """Get current page viewport size as (width, height)."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        return page.viewport_size()

    # Tab management

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
        """Focus a tab by index (0-based) or page reference."""
        self._sync_pages()
        if isinstance(tab, int):
            if tab < 0 or tab >= len(self._pages):
                raise IndexError(
                    f"Tab index {tab} out of range (0-{len(self._pages) - 1})"
                )
            self._current_page_index = tab
        else:
            for i, p in enumerate(self._pages):
                if p == tab:
                    self._current_page_index = i
                    return
            raise ValueError("Tab not found")

    async def close(self) -> None:
        """Close all managed pages."""
        for page in list(self._pages):
            await page.close()
        self._pages = []
        self._current_page_index = None

    # Context building

    async def get_page_context(
        self, include_dom: bool = True, include_screenshot: bool = True
    ) -> List[Content]:
        """Get current page context as Content list.

        Args:
            include_dom: Include DOM snapshot (default: True)
            include_screenshot: Include screenshot (default: True)
        """
        content: List[Content] = []
        tabs_context = self._get_tabs_context()
        content.append(AgentText(text=tabs_context, lifespan=1))
        if include_dom:
            dom_snapshot = await self._get_dom_snapshot()
            if dom_snapshot:
                content.append(AgentText(text=dom_snapshot, lifespan=1))
        if include_screenshot:
            screenshot_b64 = await self._get_screenshot()
            if screenshot_b64:
                content.append(
                    AgentImage(
                        data=screenshot_b64,
                        mime_type=ImageMimeType.PNG,
                        lifespan=2,
                    )
                )
        return content

    async def screenshot(
        self, path: Optional[str] = None, full_page: bool = False
    ) -> bytes:
        """Take screenshot of current page."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        return await page.screenshot(path=path, full_page=full_page)

    # Element resolution

    async def select(self, id: str) -> Element:
        """Select element by ID, returns Element for direct interaction."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        if self._dom_context is None:
            raise RuntimeError("Context not built yet.")
        dom_node = self._dom_context.get_dom_node(id)
        if dom_node is None:
            raise KeyError(f"Element ID '{id}' not found")
        xpath = dom_node.get_x_path()
        return await page.select_one(xpath)

    # Coordinate scaling

    def scale_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Scale normalized coordinates to actual pixels."""
        if not self._coordinate_scale:
            return x, y
        viewport = self.get_viewport_size()
        return (
            int(x / self._coordinate_scale * viewport[0]),
            int(y / self._coordinate_scale * viewport[1]),
        )

    # Private methods

    def _sync_pages(self) -> None:
        """Sync internal page list with context.pages."""
        if self._context is None:
            return
        context_pages = self._context.pages
        from webtask.integrations.browser.playwright import PlaywrightPage

        wrapped_context_pages = []
        for p in context_pages:
            if isinstance(p, Page):
                wrapped_context_pages.append(p)
            else:
                wrapped_context_pages.append(PlaywrightPage(p))
        self._pages = [
            p for p in self._pages if any(p == cp for cp in wrapped_context_pages)
        ]
        for cp in wrapped_context_pages:
            if not any(cp == p for p in self._pages):
                self._pages.append(cp)
        if self._current_page_index is not None:
            if self._current_page_index >= len(self._pages):
                self._current_page_index = len(self._pages) - 1 if self._pages else None

    def _get_tabs_context(self) -> str:
        """Get tabs context string for LLM."""
        self._sync_pages()
        if not self._pages:
            return "Tabs:\n(no tabs open)"
        lines = ["Tabs:"]
        for idx, page in enumerate(self._pages):
            url = page.url if page.url else "about:blank"
            current_marker = " (current)" if idx == self._current_page_index else ""
            lines.append(f"- [{idx}] {url}{current_marker}")
        return "\n".join(lines)

    async def _get_screenshot(self, full_page: bool = False) -> Optional[str]:
        """Get screenshot as base64 string, or None if no page is open."""
        if not self.has_current_page():
            return None
        screenshot_bytes = await self.screenshot(full_page=full_page)
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    async def _get_dom_snapshot(self) -> Optional[str]:
        """Get DOM snapshot with interactive elements, or None if no page is open."""
        if not self.has_current_page():
            return None
        page = self.get_current_page()
        self._dom_context = await LLMDomContext.from_page(page)
        context_str = self._dom_context.get_context(mode=self._mode)
        lines = ["Current Tab:"]
        if not context_str:
            lines.append("(no interactive elements found)")
        else:
            lines.append(context_str)
        return "\n".join(lines)
