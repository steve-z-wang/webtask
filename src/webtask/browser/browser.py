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
    async def create_browser(cls, **kwargs):
        """
        Create and launch the browser instance (async factory method).

        Returns:
            Browser instance

        Example:
            >>> browser = await PlaywrightBrowser.create_browser(headless=True)
        """
        pass

    @abstractmethod
    async def create_session(self, **kwargs):
        """
        Create a new session/context in this browser.

        Returns:
            Session instance

        Example:
            >>> browser = await PlaywrightBrowser.create_browser()
            >>> session = await browser.create_session()
        """
        pass

    @abstractmethod
    async def close(self):
        """Close the browser instance."""
        pass
