"""Context base class for browser context management."""

from abc import ABC, abstractmethod


class Context(ABC):
    """
    Abstract base class for browser context management.

    Manages browser contexts (isolated browsing sessions) with pages.
    Equivalent to Playwright's BrowserContext.
    """

    @abstractmethod
    async def create_page(self):
        """
        Create a new page/tab in this context.

        Returns:
            Page instance

        Example:
            >>> context = await browser.create_context()
            >>> page = await context.create_page()
        """
        pass

    @abstractmethod
    async def close(self):
        """Close the context."""
        pass
