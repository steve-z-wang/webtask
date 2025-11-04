"""Agent - main interface for web automation."""

import logging
from typing import Dict, List, Optional
from ..llm import LLM
from ..browser import Page, Session
from ..llm_browser import LLMBrowser
from .step import Step, TaskResult
from .task_manager import TaskManager


class Agent:
    """
    Main agent interface for web automation.

    Supports multi-page (with Session) and single-page (with injected Page) modes.
    Provides high-level execute() for autonomous task completion and low-level methods for imperative control.
    """

    def __init__(
        self,
        llm: LLM,
        session: Optional[Session] = None,
        page: Optional[Page] = None,
        action_delay: float = 1.0,
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
    ):
        """
        Initialize agent.

        Args:
            llm: LLM instance for reasoning (task planning, completion checking)
            session: Optional Session instance for multi-page support
            page: Optional Page instance to use as initial page
            action_delay: Delay in seconds after actions (default: 1.0)
            use_screenshot: Use screenshots with bounding boxes in LLM context (default: True)
            selector_llm: Optional separate LLM for element selection (defaults to main llm)
        """
        self.llm = llm
        self.selector_llm = selector_llm or llm
        self.session = session
        self.action_delay = action_delay
        self.use_screenshot = use_screenshot
        self.logger = logging.getLogger(__name__)

        self.llm_browser = LLMBrowser(session, use_screenshot)

        if page is not None:
            self.llm_browser.set_page(page)

        self.task_manager: Optional[TaskManager] = None

    async def execute(
        self,
        task: str,
        max_steps: int = 10,
        resources: Optional[Dict[str, str]] = None,
    ) -> TaskResult:
        """
        Execute a task autonomously.

        Args:
            task: Task description in natural language
            max_steps: Maximum number of steps before giving up
            resources: Optional dict of file resources (name -> path)

        Returns:
            TaskResult with completion status, steps, and final message
        """
        # Create task manager (creates task, throttler, roles internally)
        self.task_manager = TaskManager(
            task_description=task,
            llm=self.llm,
            llm_browser=self.llm_browser,
            action_delay=self.action_delay,
            max_steps=max_steps,
            resources=resources,
        )

        # Run autonomous execution loop
        return await self.task_manager.execute()

    def set_task(
        self,
        task: str,
        max_steps: int = 10,
        resources: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Set current task for step-by-step execution.

        Args:
            task: Task description in natural language
            max_steps: Maximum steps before giving up
            resources: Optional dict of file resources (name -> path)
        """
        # Create task manager (creates task, throttler, roles internally)
        self.task_manager = TaskManager(
            task_description=task,
            llm=self.llm,
            llm_browser=self.llm_browser,
            action_delay=self.action_delay,
            max_steps=max_steps,
            resources=resources,
        )

    async def run_step(self) -> Step:
        """
        Execute one step of the current task.

        Returns:
            Step with proposal and execution results

        Raises:
            RuntimeError: If no task is set (call set_task first)
        """
        if self.task_manager is None:
            raise RuntimeError("No task set. Call set_task() first.")

        # Delegate to task manager
        return await self.task_manager.run_step()

    async def open_page(self, url: Optional[str] = None) -> Page:
        """
        Open a new page and switch to it.

        Args:
            url: Optional URL to navigate to

        Returns:
            The new Page instance

        Raises:
            RuntimeError: If no session is available
        """
        return await self.llm_browser.create_page(url)

    async def close_page(self, page: Optional[Page] = None) -> None:
        """
        Close a page (closes current page if page=None).

        Args:
            page: Page to close (defaults to current page)
        """
        await self.llm_browser.close_page(page)

    async def get_current_page(self) -> Optional[Page]:
        return self.llm_browser.get_current_page()

    def get_pages(self) -> List[Page]:
        """
        Get all open pages.

        Returns:
            List of Page instances
        """
        return list(self.llm_browser._pages.values())

    @property
    def page_count(self) -> int:
        """Number of open pages."""
        return len(self.llm_browser._pages)

    async def navigate(self, url: str):
        """
        Navigate to URL (low-level imperative mode).

        Auto-creates a page if none exists.

        Args:
            url: URL to navigate to
        """
        await self.llm_browser.navigate(url)

    async def select(self, description: str):
        """
        Select element by natural language description (low-level imperative mode).

        Args:
            description: Natural language description of element

        Returns:
            Browser Element with .click(), .fill() methods

        Raises:
            RuntimeError: If no page is opened
            ValueError: If LLM fails to find a matching element
        """
        from ..llm_browser.selector import NaturalSelector

        selector = NaturalSelector(self.selector_llm, self.llm_browser)
        return await selector.select(description)

    async def wait_for_idle(self, timeout: int = 30000):
        """
        Wait for page to be idle (network and DOM stable).

        Args:
            timeout: Maximum time to wait in milliseconds (default: 30000ms)

        Raises:
            RuntimeError: If no page is opened
            TimeoutError: If page doesn't become idle within timeout
        """
        page = self.llm_browser._require_page()
        await page.wait_for_idle(timeout=timeout)

    async def wait(self, seconds: float):
        """
        Wait for a specific amount of time.

        Args:
            seconds: Number of seconds to wait
        """
        import asyncio

        await asyncio.sleep(seconds)

    async def screenshot(
        self, path: Optional[str] = None, full_page: bool = False
    ) -> bytes:
        """
        Take a screenshot of the current page.

        Args:
            path: Optional file path to save screenshot
            full_page: Whether to screenshot the full scrollable page (default: False)

        Returns:
            Screenshot as bytes (PNG format)

        Raises:
            RuntimeError: If no page is opened
        """
        page = self.llm_browser._require_page()
        return await page.screenshot(path=path, full_page=full_page)

    def set_page(self, page: Page) -> None:
        """
        Set/switch/inject a page as the current page.

        Supports injecting external pages, switching between managed pages, or setting a new page to work with.

        Args:
            page: Page instance to set as current
        """
        self.llm_browser.set_page(page)

    def set_session(self, session: Session) -> None:
        """
        Set or update the session.

        Enables multi-page operations after initialization.

        Args:
            session: Session instance for creating pages
        """
        self.session = session
        self.llm_browser.set_session(session)

    async def close(self) -> None:
        """Close the agent and cleanup all resources."""
        for page in list(self.llm_browser._pages.values()):
            await self.llm_browser.close_page(page)

        if self.session is not None:
            await self.session.close()
