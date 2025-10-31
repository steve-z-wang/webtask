"""Playwright browser implementation."""

from playwright.async_api import async_playwright, Browser as PlaywrightBrowserType
from ....browser import Browser


class PlaywrightBrowser(Browser):
    """
    Playwright implementation of Browser.

    Wraps Playwright's browser for lifecycle management.
    """

    def __init__(
        self, playwright, browser: PlaywrightBrowserType, headless: bool = False
    ):
        """
        Initialize PlaywrightBrowser (use create_browser factory instead).

        Args:
            playwright: Playwright instance
            browser: Playwright Browser instance
            headless: Whether browser is in headless mode
        """
        super().__init__(headless=headless)
        self._playwright = playwright
        self._browser = browser

    @classmethod
    async def create_browser(
        cls, headless: bool = False, browser_type: str = "chromium"
    ) -> "PlaywrightBrowser":
        """
        Create and launch a new Playwright browser instance.

        Args:
            headless: Whether to run browser in headless mode
            browser_type: Browser type ("chromium", "firefox", or "webkit")

        Returns:
            PlaywrightBrowser instance

        Example:
            >>> browser = await PlaywrightBrowser.create_browser(headless=True)
            >>> await browser.close()
        """
        playwright = await async_playwright().start()

        # Launch browser based on type
        if browser_type == "chromium":
            browser = await playwright.chromium.launch(headless=headless)
        elif browser_type == "firefox":
            browser = await playwright.firefox.launch(headless=headless)
        elif browser_type == "webkit":
            browser = await playwright.webkit.launch(headless=headless)
        else:
            raise ValueError(f"Unknown browser type: {browser_type}")

        return cls(playwright, browser, headless)

    async def create_session(self, cookies=None):
        """
        Create a new session/context in this browser.

        Args:
            cookies: Optional list of cookies for the session

        Returns:
            PlaywrightSession instance

        Example:
            >>> browser = await PlaywrightBrowser.create_browser()
            >>> session = await browser.create_session()
            >>> page = await session.create_page()
        """
        from .playwright_session import PlaywrightSession

        # Create new browser context
        context = await self._browser.new_context()

        # Set cookies if provided
        if cookies:
            from ....browser.cookies import Cookies

            cookie_dicts = Cookies.to_dict_list(cookies)
            await context.add_cookies(cookie_dicts)

        return PlaywrightSession(context, cookies)

    async def close(self):
        """Close the Playwright browser instance."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
