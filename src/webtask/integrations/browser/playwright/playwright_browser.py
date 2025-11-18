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
        Initialize PlaywrightBrowser (use create factory instead).

        Args:
            playwright: Playwright instance
            browser: Playwright Browser instance
            headless: Whether browser is in headless mode
        """
        super().__init__(headless=headless)
        self._playwright = playwright
        self._browser = browser

    @classmethod
    async def create(
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
            >>> browser = await PlaywrightBrowser.create(headless=True)
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

    @classmethod
    async def connect(
        cls, cdp_url: str = "http://localhost:9222"
    ) -> "PlaywrightBrowser":
        """
        Connect to an existing Chrome/Chromium browser via CDP.

        Customer must launch Chrome with debugging enabled:
            chrome --remote-debugging-port=9222

        Args:
            cdp_url: CDP endpoint URL (default: http://localhost:9222)

        Returns:
            PlaywrightBrowser instance connected to existing browser

        Example:
            >>> # Customer launches: chrome --remote-debugging-port=9222
            >>> browser = await PlaywrightBrowser.connect("http://localhost:9222")
            >>> session = await browser.create_session()
        """
        playwright = await async_playwright().start()

        # Connect to existing browser via CDP
        browser = await playwright.chromium.connect_over_cdp(cdp_url)

        return cls(playwright, browser, headless=False)

    async def create_context(self, cookies=None):
        """
        Create a new context in this browser.

        Args:
            cookies: Optional list of cookies for the context

        Returns:
            PlaywrightContext instance

        Example:
            >>> browser = await PlaywrightBrowser.create()
            >>> context = await browser.create_context()
            >>> page = await context.create_page()
        """
        from .playwright_context import PlaywrightContext

        # Create new browser context
        browser_context = await self._browser.new_context()

        # Set cookies if provided
        if cookies:
            from ....browser.cookies import Cookies

            cookie_dicts = Cookies.to_dict_list(cookies)
            await browser_context.add_cookies(cookie_dicts)

        return PlaywrightContext(browser_context)

    async def close(self):
        """Close the Playwright browser instance."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
