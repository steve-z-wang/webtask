"""Page base class for browser page management."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from .element import Element


class Page(ABC):
    """
    Abstract base class for browser page management.

    Simple adapter over browser automation libraries (Playwright, Selenium, etc.).
    Concrete implementations (PlaywrightPage, etc.) inherit from this.
    """

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

        Waits for network activity to finish and DOM to stabilize.
        Useful after navigation, clicks, or dynamic content updates.

        Args:
            timeout: Maximum time to wait in milliseconds (default: 30000ms = 30s)

        Raises:
            TimeoutError: If page doesn't become idle within timeout
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

    async def get_snapshot(self) -> 'DomSnapshot':
        """
        Get DOM snapshot of the current page.

        Returns:
            DomSnapshot with parsed DOM tree (no filtering or element IDs)
        """
        from ..dom import DomSnapshot

        cdp_snapshot = await self.get_cdp_snapshot()
        return DomSnapshot.from_cdp(cdp_snapshot, url=self.url)
