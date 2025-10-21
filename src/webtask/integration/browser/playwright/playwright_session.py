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

    @classmethod
    async def create_session(
        cls,
        browser: PlaywrightBrowser,
        cookies: Optional[List[Cookie]] = None
    ) -> 'PlaywrightSession':
        """
        Create a new Playwright browser session/context.

        Args:
            browser: PlaywrightBrowser instance
            cookies: Optional list of cookies to set for this session

        Returns:
            PlaywrightSession instance

        Example:
            >>> browser = await PlaywrightBrowser.create_browser()
            >>> session = await PlaywrightSession.create_session(browser, cookies=[...])
            >>> await session.close()
        """
        # Create new browser context
        context = await browser._browser.new_context()

        # Set cookies if provided
        if cookies:
            cookie_dicts = Cookies.to_dict_list(cookies)
            await context.add_cookies(cookie_dicts)

        return cls(context, cookies)

    async def close(self):
        """Close the session/context."""
        if self._context:
            await self._context.close()
