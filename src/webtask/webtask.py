"""Webtask - main manager class for web automation."""

from typing import Optional
from .browser import Browser
from .llm import LLM
from .agent import Agent
from .llm_browser.dom_filter_config import DomFilterConfig


class Webtask:
    """
    Main manager class for web automation.

    Manages browser lifecycle and creates agents with sessions.
    Browser is launched lazily on first agent creation.
    """

    def __init__(self, headless: bool = False, browser_type: str = "chromium"):
        """Initialize Webtask. Browser launches lazily on first agent creation."""
        self.headless = headless
        self.browser_type = browser_type
        self.browser: Optional[Browser] = None

    async def _ensure_browser(self) -> Browser:
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
        action_delay: float = 1.0,
        dom_filter_config: Optional[DomFilterConfig] = None,
        use_screenshot: bool = True,
    ) -> Agent:
        """Create agent with new session. Launches browser on first call.

        Args:
            llm: LLM instance for reasoning
            cookies: Optional cookies for the session
            action_delay: Delay in seconds after actions (default: 1.0)
            dom_filter_config: Configuration for DOM filtering
            use_screenshot: Use screenshots with bounding boxes in LLM context (default: True)
        """
        browser = await self._ensure_browser()
        session = await browser.create_session(cookies=cookies)
        agent = Agent(
            llm,
            session=session,
            action_delay=action_delay,
            dom_filter_config=dom_filter_config,
            use_screenshot=use_screenshot,
        )

        return agent

    async def close(self) -> None:
        """Close and cleanup all resources."""
        if self.browser is not None:
            await self.browser.close()
