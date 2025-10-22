"""Webtask - main manager class for web automation."""

from typing import Optional
from .browser import Browser, Session
from .llm import LLM
from .agent import Agent


class Webtask:
    """
    Main manager class for web automation.

    Manages browser lifecycle and creates agents with sessions.
    Use the create() factory method to instantiate.
    """

    def __init__(self, browser: Browser):
        """
        Initialize Webtask (use create factory instead).

        Args:
            browser: Browser instance to manage
        """
        self.browser = browser

    @classmethod
    async def create(
        cls,
        headless: bool = False,
        browser_type: str = "chromium"
    ) -> 'Webtask':
        """
        Create a Webtask instance with a new browser.

        Args:
            headless: Whether to run browser in headless mode
            browser_type: Browser type ("chromium", "firefox", or "webkit")

        Returns:
            Webtask instance

        Example:
            >>> webtask = await Webtask.create(headless=False)
            >>> agent = await webtask.create_agent(llm=my_llm)
        """
        from .integration.browser.playwright import PlaywrightBrowser

        browser = await PlaywrightBrowser.create_browser(
            headless=headless,
            browser_type=browser_type
        )

        return cls(browser)

    async def create_agent(self, llm: LLM, cookies=None) -> Agent:
        """
        Create a new agent with a new session.

        Args:
            llm: LLM instance for reasoning
            cookies: Optional list of cookies for the session

        Returns:
            Agent instance ready to use

        Example:
            >>> from webtask.integration.llm import OpenAILLM
            >>> llm = OpenAILLM.create(model="gpt-4")
            >>> agent = await webtask.create_agent(llm=llm)
            >>> await agent.execute("Search for Python tutorials")
        """
        # Create a new session
        session = await self.browser.create_session(cookies=cookies)

        # Create agent with session and LLM
        agent = Agent(llm, session)

        return agent

    async def close(self) -> None:
        """
        Close the Webtask and cleanup all resources.

        Closes the browser and all associated sessions/pages.
        """
        await self.browser.close()
