"""Browser base class for browser lifecycle management."""

from abc import ABC, abstractmethod


class Browser(ABC):
    """
    Abstract base class for browser management.

    Manages browser lifecycle (launch, close, etc.).
    """

    def __init__(self, headless: bool = False):
        """
        Initialize the browser.

        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless

    @classmethod
    @abstractmethod
    async def create(cls, **kwargs):
        """
        Create and launch the browser instance (async factory method).

        Returns:
            Browser instance

        Example:
            >>> browser = await PlaywrightBrowser.create(headless=True)
        """
        pass

    @classmethod
    @abstractmethod
    async def connect(cls, **kwargs):
        """
        Connect to an existing browser instance (async factory method).

        Returns:
            Browser instance connected to existing browser

        Example:
            >>> browser = await PlaywrightBrowser.connect("http://localhost:9222")
        """
        pass

    @abstractmethod
    async def create_context(self, **kwargs):
        """
        Create a new context in this browser.

        Returns:
            Context instance

        Example:
            >>> browser = await PlaywrightBrowser.create()
            >>> context = await browser.create_context()
        """
        pass

    @abstractmethod
    async def close(self):
        """Close the browser instance."""
        pass
