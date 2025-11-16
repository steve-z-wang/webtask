"""Page base class for browser page management."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from .element import Element


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
