"""AgentBrowser - browser interface for agent with page management and LLMDomContext."""

from typing import List, Literal, Optional, Tuple, Union
from webtask.browser import Page, Context
from webtask.llm.message import Content, TextContent, ImageContent, ImageMimeType
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
        coordinate_scale: Optional[int] = None,
    ):
        self._context = context
        self._wait_after_action = wait_after_action
        self._mode = mode
        self._coordinate_scale = coordinate_scale
        self._pages: List[Page] = []
        self._current_page_index: Optional[int] = None
        self._dom_context: Optional[LLMDomContext] = None

    # Setters

    def set_context(self, context: Context) -> None:
        """Set or update the context."""
        self._context = context

    def set_wait_after_action(self, wait_after_action: float) -> None:
        """Set wait_after_action duration."""
        self._wait_after_action = wait_after_action

    def set_mode(self, mode: str) -> None:
        """Set DOM snapshot mode."""
        self._mode = mode

    def set_coordinate_scale(self, scale: Optional[int]) -> None:
        """Set coordinate scale for pixel-based tools."""
        self._coordinate_scale = scale

    # Getters

    def get_current_page(self) -> Optional[Page]:
        """Get current page or None if no page is active."""
        if self._current_page_index is None:
            return None
        if self._current_page_index >= len(self._pages):
            return None
        return self._pages[self._current_page_index]

    def get_current_url(self) -> str:
        """Get current page URL."""
        page = self.get_current_page()
        return page.url if page else "about:blank"

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

    # Page operations

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

    async def get_page_context(self) -> List[Content]:
        """Get current page context (tabs, DOM, screenshot) as Content list."""
        content: List[Content] = []
        tabs_context = self._get_tabs_context()
        content.append(TextContent(text=tabs_context, tag="tabs_context"))
        dom_snapshot = await self._get_dom_snapshot()
        if dom_snapshot:
            content.append(TextContent(text=dom_snapshot, tag="dom_snapshot"))
        screenshot_b64 = await self._get_screenshot()
        if screenshot_b64:
            content.append(
                ImageContent(
                    data=screenshot_b64, mime_type=ImageMimeType.PNG, tag="screenshot"
                )
            )
        return content

    # DOM-based actions

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

    async def goto(self, url: str) -> None:
        """Go to URL and clear context."""
        page = self.get_current_page()
        if page is None:
            if self._context is None:
                raise RuntimeError(
                    "Cannot goto: no tab available and no context to create one."
                )
            page = await self.open_tab()
        await page.goto(url)
        self._dom_context = None
        await wait(self._wait_after_action)

    # Pixel-based actions (for Computer Use)

    async def click_at(self, x: int, y: int) -> None:
        """Click at screen coordinates."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        x, y = self._scale_coordinates(x, y)
        await page.mouse_click(x, y)
        await wait(self._wait_after_action)

    async def hover_at(self, x: int, y: int) -> None:
        """Hover at screen coordinates."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        x, y = self._scale_coordinates(x, y)
        await page.mouse_move(x, y)
        await wait(self._wait_after_action)

    async def type_text_at(
        self,
        x: int,
        y: int,
        text: str,
        press_enter: bool = True,
        clear_before_typing: bool = True,
    ) -> None:
        """Click at coordinates and type text."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        x, y = self._scale_coordinates(x, y)
        await page.mouse_click(x, y)
        if clear_before_typing:
            await page.keyboard_press("Control+a")
            await page.keyboard_press("Backspace")
        await page.keyboard_type(text)
        if press_enter:
            await page.keyboard_press("Enter")
        await wait(self._wait_after_action)

    async def scroll_at(
        self,
        x: int,
        y: int,
        direction: Literal["up", "down", "left", "right"],
        magnitude: int = 800,
    ) -> None:
        """Scroll at specific coordinates."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        x, y = self._scale_coordinates(x, y)
        delta_x, delta_y = 0, 0
        if direction == "up":
            delta_y = -magnitude
        elif direction == "down":
            delta_y = magnitude
        elif direction == "left":
            delta_x = -magnitude
        elif direction == "right":
            delta_x = magnitude
        await page.mouse_wheel(x, y, delta_x, delta_y)
        await wait(self._wait_after_action)

    async def scroll_document(
        self, direction: Literal["up", "down", "left", "right"]
    ) -> None:
        """Scroll the entire document."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        key = {
            "up": "PageUp",
            "down": "PageDown",
            "left": "Home",
            "right": "End",
        }.get(direction, "PageDown")
        await page.keyboard_press(key)
        await wait(self._wait_after_action)

    async def drag_and_drop(self, x: int, y: int, dest_x: int, dest_y: int) -> None:
        """Drag from one position to another."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        x, y = self._scale_coordinates(x, y)
        dest_x, dest_y = self._scale_coordinates(dest_x, dest_y)
        await page.mouse_drag(x, y, dest_x, dest_y)
        await wait(self._wait_after_action)

    # Navigation

    async def go_back(self) -> None:
        """Navigate back in browser history."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        await page.go_back()
        self._dom_context = None
        await wait(self._wait_after_action)

    async def go_forward(self) -> None:
        """Navigate forward in browser history."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        await page.go_forward()
        self._dom_context = None
        await wait(self._wait_after_action)

    async def search(self) -> None:
        """Navigate to default search engine."""
        await self.goto("https://www.google.com")

    async def key_combination(self, keys: List[str]) -> None:
        """Press keyboard key combination."""
        page = self.get_current_page()
        if page is None:
            raise RuntimeError("No page is currently open")
        key_combo = "+".join(keys)
        await page.keyboard_press(key_combo)
        await wait(self._wait_after_action)

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

    def _scale_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Scale normalized coordinates to actual pixels."""
        if not self._coordinate_scale:
            return x, y
        viewport = self.get_viewport_size()
        return (
            int(x / self._coordinate_scale * viewport[0]),
            int(y / self._coordinate_scale * viewport[1]),
        )

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
        page = self.get_current_page()
        if page is None:
            return None
        await self.wait_for_load(timeout=10000)
        screenshot_bytes = await self.screenshot(full_page=full_page)
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    async def _get_dom_snapshot(self) -> str:
        """Get DOM snapshot with interactive elements."""
        page = self.get_current_page()
        if page is None:
            return ""
        await self.wait_for_load(timeout=10000)
        self._dom_context = await LLMDomContext.from_page(page)
        context_str = self._dom_context.get_context(mode=self._mode)
        lines = ["Current Tab:"]
        if not context_str:
            lines.append("(no interactive elements found)")
        else:
            lines.append(context_str)
        return "\n".join(lines)

    async def _select(self, id: str):
        """Select element by ID."""
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
