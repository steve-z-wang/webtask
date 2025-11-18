"""Playwright context implementation."""

from typing import TYPE_CHECKING
from playwright.async_api import BrowserContext
from ....browser import Context

if TYPE_CHECKING:
    from .playwright_page import PlaywrightPage


class PlaywrightContext(Context):
    """
    Playwright implementation of Context.

    Wraps Playwright's BrowserContext for context management.
    Users should set cookies directly on the BrowserContext before passing it in.
    """

    def __init__(self, browser_context: BrowserContext):
        """
        Initialize PlaywrightContext.

        Args:
            browser_context: Playwright BrowserContext instance
        """
        super().__init__()
        self._context = browser_context

    @property
    def pages(self):
        """
        Get all existing pages in this context.

        Returns:
            List of Playwright Page objects

        Example:
            >>> context = await browser.create_context()
            >>> existing_pages = context.pages
        """
        return self._context.pages

    async def create_page(self) -> "PlaywrightPage":
        """
        Create a new page/tab in this context.

        Returns:
            PlaywrightPage instance

        Example:
            >>> context = await browser.create_context()
            >>> page1 = await context.create_page()
            >>> page2 = await context.create_page()  # New tab in same context
        """
        from .playwright_page import PlaywrightPage

        playwright_page = await self._context.new_page()
        return PlaywrightPage(playwright_page)

    async def close(self):
        """Close the context."""
        if self._context:
            await self._context.close()
