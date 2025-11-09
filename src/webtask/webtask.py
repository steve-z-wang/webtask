"""Webtask - main manager class for web automation."""

from typing import Optional
from .browser import Browser, Session, Page
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

            self.browser = await PlaywrightBrowser.create_browser(
                headless=self.headless, browser_type=self.browser_type
            )

        return self.browser

    async def create_agent(
        self,
        llm: LLM,
        cookies=None,
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
    ) -> Agent:
        """Create agent with new browser session. Launches browser on first call.

        Args:
            llm: LLM instance for reasoning
            cookies: Optional cookies for the session
            use_screenshot: Use screenshots with bounding boxes (default: True)
            selector_llm: Optional separate LLM for element selection

        Returns:
            Agent instance with new session
        """
        browser = await self._ensure_browser()
        session = await browser.create_session(cookies=cookies)
        agent = Agent(
            llm,
            session=session,
            use_screenshot=use_screenshot,
            selector_llm=selector_llm,
        )

        return agent

    async def create_agent_with_browser(
        self,
        llm: LLM,
        browser: Browser,
        cookies=None,
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
    ) -> Agent:
        """Create agent with existing browser.

        Args:
            llm: LLM instance for reasoning
            browser: Existing Browser instance
            cookies: Optional cookies for the session
            use_screenshot: Use screenshots with bounding boxes (default: True)
            selector_llm: Optional separate LLM for element selection

        Returns:
            Agent instance with new session from provided browser
        """
        session = await browser.create_session(cookies=cookies)
        agent = Agent(
            llm,
            session=session,
            use_screenshot=use_screenshot,
            selector_llm=selector_llm,
        )

        return agent

    def create_agent_with_session(
        self,
        llm: LLM,
        session: Session,
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
    ) -> Agent:
        """Create agent with existing session.

        Args:
            llm: LLM instance for reasoning
            session: Existing Session instance
            use_screenshot: Use screenshots with bounding boxes (default: True)
            selector_llm: Optional separate LLM for element selection

        Returns:
            Agent instance with provided session
        """
        return Agent(
            llm,
            session=session,
            use_screenshot=use_screenshot,
            selector_llm=selector_llm,
        )

    def create_agent_with_page(
        self,
        llm: LLM,
        page: Page,
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
    ) -> Agent:
        """Create agent with existing page (session-less mode).

        Args:
            llm: LLM instance for reasoning
            page: Existing Page instance
            use_screenshot: Use screenshots with bounding boxes (default: True)
            selector_llm: Optional separate LLM for element selection

        Returns:
            Agent instance with provided page
        """
        agent = Agent(
            llm,
            session=None,
            use_screenshot=use_screenshot,
            selector_llm=selector_llm,
        )
        agent.set_page(page)
        return agent

    async def close(self) -> None:
        """Close and cleanup all resources."""
        if self.browser is not None:
            await self.browser.close()
