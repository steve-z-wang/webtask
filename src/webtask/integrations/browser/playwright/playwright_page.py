"""Playwright page implementation."""

from typing import TYPE_CHECKING, Dict, Any, List, Union, Optional
from pathlib import Path
from playwright.async_api import Page as PlaywrightPageType
from ....browser import Page
from ....utils import normalize_url
from ....dom import XPath

if TYPE_CHECKING:
    from .playwright_element import PlaywrightElement


class PlaywrightPage(Page):
    """
    Playwright implementation of Page.

    Wraps Playwright's Page for page management.
    """

    def __init__(self, page: PlaywrightPageType):
        """
        Initialize PlaywrightPage.

        Args:
            page: Playwright Page instance
        """
        self._page = page

    async def navigate(self, url: str):
        """
        Navigate to a URL.

        Automatically adds https:// if no protocol is specified.

        Args:
            url: URL to navigate to (e.g., "google.com" or "https://google.com")
        """
        url = normalize_url(url)
        await self._page.goto(url)

    async def get_cdp_snapshot(self) -> Dict[str, Any]:
        """
        Get a CDP (Chrome DevTools Protocol) snapshot of the current page.

        Returns:
            CDP snapshot data (raw dictionary from DOMSnapshot.captureSnapshot)
        """
        # Get CDP session
        cdp = await self._page.context.new_cdp_session(self._page)

        # Capture snapshot
        snapshot = await cdp.send(
            "DOMSnapshot.captureSnapshot",
            {
                "computedStyles": ["display", "visibility", "opacity"],
                "includePaintOrder": True,
                "includeDOMRects": True,
            },
        )

        return snapshot

    async def select(self, selector: Union[str, XPath]) -> List["PlaywrightElement"]:
        """
        Select all elements matching the selector.

        Args:
            selector: CSS selector string or XPath object

        Returns:
            List of PlaywrightElement (may be empty)
        """
        from .playwright_element import PlaywrightElement

        if isinstance(selector, XPath):
            elements = await self._page.locator(selector.for_playwright()).all()
        else:
            elements = await self._page.query_selector_all(selector)

        return [PlaywrightElement(el) for el in elements]

    async def select_one(self, selector: Union[str, XPath]) -> "PlaywrightElement":
        """
        Select a single element matching the selector.

        Args:
            selector: CSS selector string or XPath object

        Returns:
            Single PlaywrightElement

        Raises:
            ValueError: If no elements match or multiple elements match
        """
        # Use the existing select() method
        elements = await self.select(selector)

        if len(elements) == 0:
            raise ValueError(f"No elements found matching selector: {selector}")
        elif len(elements) > 1:
            raise ValueError(
                f"Multiple elements ({len(elements)}) found matching selector: {selector}"
            )

        return elements[0]

    async def wait_for_idle(self, timeout: int = 30000):
        """
        Wait for page to be idle (network and DOM stable).

        Waits for network activity to finish and DOM to stabilize.
        Useful after navigation, clicks, or dynamic content updates.

        Args:
            timeout: Maximum time to wait in milliseconds (default: 30000ms = 30s)

        Raises:
            TimeoutError: If page doesn't become idle within timeout
        """
        await self._page.wait_for_load_state("networkidle", timeout=timeout)

    async def close(self):
        """Close the page."""
        await self._page.close()

    async def screenshot(
        self, path: Optional[Union[str, Path]] = None, full_page: bool = False
    ) -> bytes:
        """
        Take a screenshot of the current page.

        Args:
            path: Optional file path to save screenshot. If None, doesn't save to disk.
            full_page: Whether to screenshot the full scrollable page (default: False)

        Returns:
            Screenshot as bytes (PNG format)
        """
        return await self._page.screenshot(path=path, full_page=full_page)

    async def keyboard_type(
        self, text: str, clear: bool = False, delay: float = 80
    ) -> None:
        """
        Type text using keyboard into the currently focused element.

        Args:
            text: Text to type
            clear: Clear existing text before typing (default: False)
            delay: Delay between keystrokes in milliseconds (default: 80ms)
        """
        if clear:
            # Select all text and delete
            await self._page.keyboard.press("Control+A")
            await self._page.keyboard.press("Backspace")

        # Type the text
        await self._page.keyboard.type(text, delay=delay)

    async def evaluate(self, script: str) -> Any:
        """
        Execute JavaScript in the page context.

        Args:
            script: JavaScript code to execute

        Returns:
            Result of the script execution (JSON-serializable values)
        """
        return await self._page.evaluate(script)

    @property
    def url(self) -> str:
        """
        Get current page URL.

        Returns:
            Current URL of the page
        """
        return self._page.url
