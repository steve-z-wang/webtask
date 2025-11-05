"""Session base class for browser session management."""

from abc import ABC, abstractmethod


class Session(ABC):
    """
    Abstract base class for browser session management.

    Manages browser sessions (contexts) with pages.
    """

    @abstractmethod
    async def create_page(self):
        """
        Create a new page/tab in this session.

        Returns:
            Page instance

        Example:
            >>> session = await PlaywrightSession.create_session(browser)
            >>> page = await session.create_page()
        """
        pass

    @abstractmethod
    async def close(self):
        """Close the session/context."""
        pass
