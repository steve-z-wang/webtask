"""Page base class for browser page management."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Any, List, Optional, Union
from pathlib import Path
from .element import Element

if TYPE_CHECKING:
    from ..dom.snapshot import DomSnapshot


class Page(ABC):
    """
    Abstract base class for browser page management.

    Simple adapter over browser automation libraries (Playwright, Selenium, etc.).
    """

    def __str__(self) -> str:
        """String representation of the page."""
        return f"Page(url={self.url!r})"

    @abstractmethod
    async def navigate(self, url: str):
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to
        """
        pass

    @abstractmethod
    async def get_cdp_snapshot(self) -> Dict[str, Any]:
        """
        Get a CDP (Chrome DevTools Protocol) snapshot of the current page.

        Returns:
            CDP snapshot data (raw dictionary from DOMSnapshot.captureSnapshot)
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
    async def wait_for_idle(self, timeout: int = 30000):
        """
        Wait for page to be idle (network and DOM stable).

        Args:
            timeout: Maximum time to wait in milliseconds (default: 30000)

        Raises:
            TimeoutError: If page doesn't become idle within timeout
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

    async def get_snapshot(self) -> "DomSnapshot":
        """
        Get DOM snapshot of the current page.

        Returns:
            DomSnapshot with parsed DOM tree
        """
        from ..dom import DomSnapshot

        cdp_snapshot = await self.get_cdp_snapshot()
        return DomSnapshot.from_cdp(cdp_snapshot, url=self.url)
