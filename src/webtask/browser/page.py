"""Page base class for browser page management."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Any, List, Optional, Union
from pathlib import Path
from .element import Element

if TYPE_CHECKING:
    from .context import Context


class Page(ABC):
    """
    Abstract base class for browser page management.

    Simple adapter over browser automation libraries (Playwright, Selenium, etc.).
    """

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Check if this is the same page as another."""
        pass

    @abstractmethod
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        pass

    @property
    @abstractmethod
    def context(self) -> "Context":
        """Get the context this page belongs to."""
        pass

    def __str__(self) -> str:
        """String representation of the page."""
        return f"Page(url={self.url!r})"

    @abstractmethod
    async def goto(self, url: str):
        """
        Go to a URL.

        Args:
            url: URL to go to
        """
        pass

    @abstractmethod
    async def get_cdp_dom_snapshot(self) -> Dict[str, Any]:
        """
        Get a CDP (Chrome DevTools Protocol) DOM snapshot of the current page.

        Returns:
            CDP DOM snapshot data (raw dictionary from DOMSnapshot.captureSnapshot)
        """
        pass

    @abstractmethod
    async def get_cdp_accessibility_tree(self) -> Dict[str, Any]:
        """
        Get a CDP accessibility tree of the current page.

        Returns:
            CDP accessibility tree data (raw dictionary from Accessibility.getFullAXTree)
        """
        pass

    @abstractmethod
    async def select(self, selector: str) -> List[Element]:
        """
        Select all elements matching the selector.

        Args:
            selector: CSS selector or XPath string

        Returns:
            List of Elements (may be empty)
        """
        pass

    @abstractmethod
    async def select_one(self, selector: str) -> Element:
        """
        Select a single element matching the selector.

        Args:
            selector: CSS selector or XPath string

        Returns:
            Single Element

        Raises:
            ValueError: If no elements match or multiple elements match
        """
        pass

    @abstractmethod
    async def close(self):
        """Close the page."""
        pass

    @abstractmethod
    async def wait_for_load(self, timeout: int = 10000):
        """
        Wait for page to fully load.

        Args:
            timeout: Maximum time to wait in milliseconds (default: 10000)

        Raises:
            TimeoutError: If page doesn't load within timeout
        """
        pass

    @abstractmethod
    async def wait_for_network_idle(self, timeout: int = 10000):
        """
        Wait for network to be idle (no requests for 500ms).

        Useful for SPAs and pages with AJAX requests.

        Args:
            timeout: Maximum time to wait in milliseconds (default: 10000)

        Raises:
            TimeoutError: If network doesn't become idle within timeout
        """
        pass

    @abstractmethod
    async def screenshot(
        self, path: Optional[Union[str, Path]] = None, full_page: bool = False
    ) -> bytes:
        """
        Take a screenshot of the current page.

        Args:
            path: Optional file path to save screenshot
            full_page: Whether to screenshot the full scrollable page (default: False)

        Returns:
            Screenshot as bytes (PNG format)

        Example:
            >>> await page.screenshot("step1.png")
        """
        pass

    @abstractmethod
    async def keyboard_type(
        self, text: str, clear: bool = False, delay: float = 80
    ) -> None:
        """
        Type text using keyboard into the currently focused element.

        Args:
            text: Text to type
            clear: Clear existing text before typing (default: False)
            delay: Delay between keystrokes in milliseconds (default: 80)

        Example:
            >>> element = await page.select_one("#input")
            >>> await element.click()
            >>> await page.keyboard_type("Hello World")
        """
        pass

    @abstractmethod
    async def evaluate(self, script: str) -> Any:
        """
        Execute JavaScript in the page context.

        Args:
            script: JavaScript code to execute

        Returns:
            Result of the script execution (JSON-serializable values)

        Example:
            >>> result = await page.evaluate("document.title")
            >>> ratio = await page.evaluate("window.devicePixelRatio")
        """
        pass

    @property
    @abstractmethod
    def url(self) -> str:
        """
        Get current page URL.

        Returns:
            Current URL of the page
        """
        pass

    @abstractmethod
    def viewport_size(self) -> tuple[int, int]:
        """
        Get the viewport size.

        Returns:
            Tuple of (width, height) in pixels
        """
        pass

    @abstractmethod
    async def mouse_click(self, x: int, y: int) -> None:
        """
        Click at specific screen coordinates.

        Args:
            x: X coordinate in pixels
            y: Y coordinate in pixels
        """
        pass

    @abstractmethod
    async def mouse_move(self, x: int, y: int) -> None:
        """
        Move mouse to specific screen coordinates.

        Args:
            x: X coordinate in pixels
            y: Y coordinate in pixels
        """
        pass

    @abstractmethod
    async def mouse_wheel(self, x: int, y: int, delta_x: int, delta_y: int) -> None:
        """
        Scroll at specific coordinates.

        Args:
            x: X coordinate in pixels
            y: Y coordinate in pixels
            delta_x: Horizontal scroll amount
            delta_y: Vertical scroll amount
        """
        pass

    @abstractmethod
    async def mouse_drag(self, x: int, y: int, dest_x: int, dest_y: int) -> None:
        """
        Drag from one position to another.

        Args:
            x: Start X coordinate
            y: Start Y coordinate
            dest_x: Destination X coordinate
            dest_y: Destination Y coordinate
        """
        pass

    @abstractmethod
    async def keyboard_press(self, key: str) -> None:
        """
        Press a keyboard key or combination.

        Args:
            key: Key to press (e.g., "Enter", "Control+C", "PageDown")
        """
        pass

    @abstractmethod
    async def go_back(self) -> None:
        """Navigate back in browser history."""
        pass

    @abstractmethod
    async def go_forward(self) -> None:
        """Navigate forward in browser history."""
        pass
