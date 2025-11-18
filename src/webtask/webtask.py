"""Webtask - main manager class for web automation."""

from typing import Optional, Union
from .browser import Browser, Context, Page
from .llm import LLM
from .agent import Agent


class Webtask:
    """
    Main manager class for web automation.

    Manages browser lifecycle and creates agents with various configurations.
    Browser is launched lazily on first agent creation.
    """

    def __init__(self, headless: bool = False, browser_type: str = "chromium"):
        """Initialize Webtask. Browser launches lazily on first agent creation."""
        self.headless = headless
        self.browser_type = browser_type
        self.browser: Optional[Browser] = None

    async def _ensure_browser(self) -> Browser:
        """Ensure browser is created (lazy initialization)."""
        if self.browser is None:
            from .integrations.browser.playwright import PlaywrightBrowser

            self.browser = await PlaywrightBrowser.create(
                headless=self.headless, browser_type=self.browser_type
            )

        return self.browser

    def _wrap_browser(self, browser) -> Browser:
        """Wrap raw Playwright browser if needed."""
        # If already our Browser interface, return as-is
        if isinstance(browser, Browser):
            return browser

        # Otherwise, assume it's a Playwright browser and wrap it
        try:
            from playwright.async_api import Browser as PlaywrightBrowserType
            from .integrations.browser.playwright import PlaywrightBrowser

            if isinstance(browser, PlaywrightBrowserType):
                # Wrap the Playwright browser (need playwright instance too)
                # For now, we'll just return it - user should use our wrapper if they want full support
                raise TypeError(
                    "Direct Playwright Browser wrapping not yet supported. "
                    "Please use PlaywrightBrowser.connect() or PlaywrightBrowser.create()"
                )
        except ImportError:
            pass

        # If not recognized, assume it's already our interface
        return browser

    def _wrap_context(self, context) -> Context:
        """Wrap raw Playwright BrowserContext if needed."""
        # If already our Context interface, return as-is
        if isinstance(context, Context):
            return context

        # Otherwise, assume it's a Playwright BrowserContext and wrap it
        try:
            from playwright.async_api import BrowserContext as PlaywrightContextType
            from .integrations.browser.playwright import PlaywrightContext

            if isinstance(context, PlaywrightContextType):
                return PlaywrightContext(context)
        except ImportError:
            pass

        # If not recognized, assume it's already our interface
        return context

    def _wrap_page(self, page) -> Page:
        """Wrap raw Playwright Page if needed."""
        # If already our Page interface, return as-is
        if isinstance(page, Page):
            return page

        # Otherwise, assume it's a Playwright Page and wrap it
        try:
            from playwright.async_api import Page as PlaywrightPageType
            from .integrations.browser.playwright import PlaywrightPage

            if isinstance(page, PlaywrightPageType):
                return PlaywrightPage(page)
        except ImportError:
            pass

        # If not recognized, assume it's already our interface
        return page

    async def create_agent(
        self,
        llm: LLM,
        cookies=None,
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
        wait_after_action: float = 0.2,
        mode: str = "accessibility",
    ) -> Agent:
        """Create agent with new browser context. Launches browser on first call.

        Args:
            llm: LLM instance for reasoning
            cookies: Optional cookies for the context
            use_screenshot: Use screenshots with bounding boxes (default: True)
            selector_llm: Optional separate LLM for element selection
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            mode: DOM context mode - "accessibility" (default) or "dom"

        Returns:
            Agent instance with new context
        """
        browser = await self._ensure_browser()
        context = await browser.create_context(cookies=cookies)
        agent = Agent(
            llm,
            context=context,
            use_screenshot=use_screenshot,
            selector_llm=selector_llm,
            wait_after_action=wait_after_action,
            mode=mode,
        )

        return agent

    async def create_agent_with_browser(
        self,
        llm: LLM,
        browser: Union[Browser, "PlaywrightBrowser"],
        cookies=None,
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
        wait_after_action: float = 0.2,
        mode: str = "accessibility",
        create_new_context: bool = False,
    ) -> Agent:
        """Create agent with existing browser.

        By default, uses existing browser context (window) if available.
        This prevents creating new windows when connecting to existing browsers.

        Args:
            llm: LLM instance for reasoning
            browser: Browser instance or raw Playwright Browser
            cookies: Optional cookies for the context
            use_screenshot: Use screenshots with bounding boxes (default: True)
            selector_llm: Optional separate LLM for element selection
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            mode: DOM context mode - "accessibility" (default) or "dom"
            create_new_context: Force creation of new isolated context (default: False)

        Returns:
            Agent instance with context from provided browser

        Example:
            >>> # Uses existing window - no new window created!
            >>> browser = await PlaywrightBrowser.connect("http://localhost:9222")
            >>> agent = await wt.create_agent_with_browser(llm=llm, browser=browser)
        """
        # Auto-wrap if needed (currently just validates it's our wrapper)
        wrapped_browser = self._wrap_browser(browser)

        # Smart context selection: use existing if available, create if needed
        if create_new_context or not wrapped_browser.contexts:
            # Create new isolated context
            context = await wrapped_browser.create_context(cookies=cookies)
        else:
            # Use existing default context (first window)
            context = wrapped_browser.get_default_context()
            if context is None:
                # Fallback: create new context
                context = await wrapped_browser.create_context(cookies=cookies)

        agent = Agent(
            llm,
            context=context,
            use_screenshot=use_screenshot,
            selector_llm=selector_llm,
            wait_after_action=wait_after_action,
            mode=mode,
        )

        return agent

    def create_agent_with_context(
        self,
        llm: LLM,
        context: Union[Context, "BrowserContext"],
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
        wait_after_action: float = 0.2,
        mode: str = "accessibility",
    ) -> Agent:
        """Create agent with existing context.

        Accepts either webtask Context or raw Playwright BrowserContext.
        Automatically wraps Playwright objects.

        Args:
            llm: LLM instance for reasoning
            context: Context instance or Playwright BrowserContext
            use_screenshot: Use screenshots with bounding boxes (default: True)
            selector_llm: Optional separate LLM for element selection
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            mode: DOM context mode - "accessibility" (default) or "dom"

        Returns:
            Agent instance with provided context
        """
        # Auto-wrap if needed
        wrapped_context = self._wrap_context(context)

        return Agent(
            llm,
            context=wrapped_context,
            use_screenshot=use_screenshot,
            selector_llm=selector_llm,
            wait_after_action=wait_after_action,
            mode=mode,
        )

    def create_agent_with_page(
        self,
        llm: LLM,
        page: Union[Page, "PlaywrightPage"],
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
        wait_after_action: float = 0.2,
        mode: str = "accessibility",
    ) -> Agent:
        """Create agent with existing page (context-less mode).

        Accepts either webtask Page or raw Playwright Page.
        Automatically wraps Playwright objects.

        Args:
            llm: LLM instance for reasoning
            page: Page instance or Playwright Page
            use_screenshot: Use screenshots with bounding boxes (default: True)
            selector_llm: Optional separate LLM for element selection
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            mode: DOM context mode - "accessibility" (default) or "dom"

        Returns:
            Agent instance with provided page
        """
        # Auto-wrap if needed
        wrapped_page = self._wrap_page(page)

        agent = Agent(
            llm,
            context=None,
            use_screenshot=use_screenshot,
            selector_llm=selector_llm,
            wait_after_action=wait_after_action,
            mode=mode,
        )
        agent.set_page(wrapped_page)
        return agent

    async def close(self) -> None:
        """Close and cleanup all resources."""
        if self.browser is not None:
            await self.browser.close()
