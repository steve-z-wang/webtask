"""Webtask - main manager class for web automation."""

from typing import Optional
from .browser import Browser, Session
from .llm import LLM
from .agent import Agent


class Webtask:
    """
    Main manager class for web automation.

    Manages browser lifecycle and creates agents with sessions.
    Browser is launched lazily on first agent creation.
    """

    def __init__(self, headless: bool = False, browser_type: str = "chromium"):
        """
        Initialize Webtask.

        Browser is not launched until first agent is created (lazy initialization).

        Args:
            headless: Whether to run browser in headless mode (default: False)
            browser_type: Browser type - "chromium", "firefox", or "webkit" (default: "chromium")

        Example:
            >>> webtask = Webtask(headless=False)  # No await needed!
            >>> agent = await webtask.create_agent(llm=my_llm)
        """
        self.headless = headless
        self.browser_type = browser_type
        self.browser: Optional[Browser] = None

    async def _ensure_browser(self) -> Browser:
        """
        Ensure browser is launched (lazy initialization).

        Returns:
            Browser instance
        """
        if self.browser is None:
            from .integrations.browser.playwright import PlaywrightBrowser

            self.browser = await PlaywrightBrowser.create_browser(
                headless=self.headless,
                browser_type=self.browser_type
            )

        return self.browser

    async def create_agent(self, llm: LLM, cookies=None, action_delay: float = 1.0) -> Agent:
        """
        Create a new agent with a new session.

        Launches browser on first call (lazy initialization).

        Args:
            llm: LLM instance for reasoning
            cookies: Optional list of cookies for the session
            action_delay: Minimum delay in seconds between actions (default: 1.0)

        Returns:
            Agent instance ready to use

        Example:
            >>> from webtask.integration.llm import OpenAILLM
            >>> webtask = Webtask()  # No await needed!
            >>> llm = OpenAILLM.create(model="gpt-4")
            >>> agent = await webtask.create_agent(llm=llm, action_delay=2.0)
            >>> await agent.execute("Search for Python tutorials")
        """
        # Ensure browser is launched (lazy initialization)
        browser = await self._ensure_browser()

        # Create a new session
        session = await browser.create_session(cookies=cookies)

        # Create agent with session and LLM
        agent = Agent(llm, session, action_delay)

        return agent

    async def close(self) -> None:
        """
        Close the Webtask and cleanup all resources.

        Closes the browser and all associated sessions/pages.
        """
        if self.browser is not None:
            await self.browser.close()
