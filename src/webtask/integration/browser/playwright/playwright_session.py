"""Playwright session implementation."""

from typing import Optional, List
from playwright.async_api import BrowserContext
from ....browser import Session, Cookie
from ....browser.cookies import Cookies
from .playwright_browser import PlaywrightBrowser


class PlaywrightSession(Session):
    """
    Playwright implementation of Session.

    Wraps Playwright's BrowserContext for session management.
    """

    def __init__(self, context: BrowserContext, cookies: Optional[List[Cookie]] = None):
        """
        Initialize PlaywrightSession (use create_session factory instead).

        Args:
            context: Playwright BrowserContext instance
            cookies: Optional list of cookies for this session
        """
        super().__init__(cookies=cookies)
        self._context = context

    async def create_page(self) -> 'PlaywrightPage':
        """
        Create a new page/tab in this session.

        Returns:
            PlaywrightPage instance

        Example:
            >>> session = await PlaywrightSession.create_session(browser)
            >>> page1 = await session.create_page()
            >>> page2 = await session.create_page()  # New tab in same session
        """
        from .playwright_page import PlaywrightPage

        playwright_page = await self._context.new_page()
        return PlaywrightPage(playwright_page)

    async def close(self):
        """Close the session/context."""
        if self._context:
            await self._context.close()
