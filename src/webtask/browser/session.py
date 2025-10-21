"""Session base class for browser session management."""

from abc import ABC, abstractmethod
from typing import Optional, List
from .cookies import Cookie


class Session(ABC):
    """
    Abstract base class for browser session management.

    Manages browser sessions with cookies and context.
    Concrete implementations (PlaywrightSession, etc.) inherit from this.
    """

    def __init__(self, cookies: Optional[List[Cookie]] = None):
        """
        Initialize the session.

        Args:
            cookies: Optional list of cookies to set for this session
        """
        self.cookies = cookies or []

    @classmethod
    @abstractmethod
    async def create_session(cls, **kwargs):
        """
        Create a new browser session/context (async factory method).

        Subclasses should implement this as a classmethod that creates
        and returns a new session instance.

        Returns:
            Session instance (concrete implementation type)

        Example:
            >>> session = await PlaywrightSession.create_session(browser, cookies=[...])
            >>> await session.close()
        """
        pass

    @abstractmethod
    async def close(self):
        """Close the session/context."""
        pass
