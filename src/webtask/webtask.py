"""Webtask - main manager class for web automation."""

from typing import Optional
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
        browser: Browser,
        cookies=None,
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
        wait_after_action: float = 0.2,
        mode: str = "accessibility",
    ) -> Agent:
        """Create agent with existing browser.

        Args:
            llm: LLM instance for reasoning
            browser: Existing Browser instance
            cookies: Optional cookies for the context
            use_screenshot: Use screenshots with bounding boxes (default: True)
            selector_llm: Optional separate LLM for element selection
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            mode: DOM context mode - "accessibility" (default) or "dom"

        Returns:
            Agent instance with new context from provided browser
        """
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

    def create_agent_with_context(
        self,
        llm: LLM,
        context: Context,
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
        wait_after_action: float = 0.2,
        mode: str = "accessibility",
    ) -> Agent:
        """Create agent with existing context.

        Args:
            llm: LLM instance for reasoning
            context: Existing Context instance
            use_screenshot: Use screenshots with bounding boxes (default: True)
            selector_llm: Optional separate LLM for element selection
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            mode: DOM context mode - "accessibility" (default) or "dom"

        Returns:
            Agent instance with provided context
        """
        return Agent(
            llm,
            context=context,
            use_screenshot=use_screenshot,
            selector_llm=selector_llm,
            wait_after_action=wait_after_action,
            mode=mode,
        )

    def create_agent_with_page(
        self,
        llm: LLM,
        page: Page,
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
        wait_after_action: float = 0.2,
        mode: str = "accessibility",
    ) -> Agent:
        """Create agent with existing page (context-less mode).

        Args:
            llm: LLM instance for reasoning
            page: Existing Page instance
            use_screenshot: Use screenshots with bounding boxes (default: True)
            selector_llm: Optional separate LLM for element selection
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            mode: DOM context mode - "accessibility" (default) or "dom"

        Returns:
            Agent instance with provided page
        """
        agent = Agent(
            llm,
            context=None,
            use_screenshot=use_screenshot,
            selector_llm=selector_llm,
            wait_after_action=wait_after_action,
            mode=mode,
        )
        agent.set_page(page)
        return agent

    async def close(self) -> None:
        """Close and cleanup all resources."""
        if self.browser is not None:
            await self.browser.close()
