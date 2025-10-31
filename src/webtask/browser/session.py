"""Session base class for browser session management."""

from abc import ABC, abstractmethod
from typing import Optional, List
from .cookies import Cookie


class Session(ABC):
    """
    Abstract base class for browser session management.

    Manages browser sessions with cookies and context.
    """

    def __init__(self, cookies: Optional[List[Cookie]] = None):
        """
        Initialize the session.

        Args:
            cookies: Optional list of cookies to set for this session
        """
        self.cookies = cookies or []

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
