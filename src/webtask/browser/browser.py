"""Browser base class for browser lifecycle management."""

from abc import ABC, abstractmethod


class Browser(ABC):
    """
    Abstract base class for browser management.

    Manages browser lifecycle (launch, close, etc.).
    Concrete implementations (PlaywrightBrowser, etc.) inherit from this.
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

        Subclasses should implement this as a classmethod that creates
        and returns a new browser instance.

        Returns:
            Browser instance (concrete implementation type)

        Example:
            >>> browser = await PlaywrightBrowser.create_browser(headless=True)
            >>> await browser.close()
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
            >>> await session.close()
        """
        pass

    @abstractmethod
    async def close(self):
        """Close the browser instance."""
        pass
