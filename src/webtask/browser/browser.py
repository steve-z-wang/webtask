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

    @property
    @abstractmethod
    def contexts(self):
        """
        Get all existing browser contexts.

        Returns:
            List of context objects

        Example:
            >>> browser = await PlaywrightBrowser.connect("http://localhost:9222")
            >>> existing_contexts = browser.contexts
        """
        pass

    def get_default_context(self):
        """
        Get the default (first) existing context, or None if no contexts exist.

        This is a convenience method that returns the first context if any exist.

        Returns:
            Context instance or None

        Example:
            >>> browser = await PlaywrightBrowser.connect("http://localhost:9222")
            >>> context = browser.get_default_context()  # First existing window
        """
        # Concrete implementation using abstract contexts property
        # Subclasses should wrap the raw context appropriately
        return None  # Subclasses override to return wrapped context

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
