"""Agent - main interface for web automation."""

import logging
from typing import Dict, List, Optional
from webtask.llm import LLM
from webtask.browser import Page, Context
from webtask._internal.agent.session_browser import SessionBrowser
from webtask._internal.natural_selector import NaturalSelector
from webtask._internal.agent.task_execution import TaskResult
from webtask._internal.agent.task_executor import TaskExecutor
from webtask._internal.utils.wait import wait as custom_wait


class Agent:
    """
    Main agent interface for web automation.

    Requires a Context for browser management and page operations.

    Two modes of operation:
    - High-level autonomous: execute(task) - Agent autonomously executes with Worker/Verifier loop
    - Low-level imperative: navigate(), select(), wait() - Direct control for manual workflows
    """

    def __init__(
        self,
        llm: LLM,
        context: Optional[Context] = None,
        wait_after_action: float = 0.2,
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
        mode: str = "accessibility",
    ):
        """
        Initialize agent.

        Args:
            llm: LLM instance for reasoning (task planning, completion checking)
            context: Optional context instance (can be set later with set_context())
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            use_screenshot: Use screenshots with bounding boxes in LLM context (default: True)
            selector_llm: Optional separate LLM for element selection (defaults to main llm)
            mode: DOM context mode - "accessibility" (default) or "dom"
        """
        self.llm = llm
        self.context = context
        self.use_screenshot = use_screenshot
        self.wait_after_action = wait_after_action
        self.mode = mode
        self.logger = logging.getLogger(__name__)

        self.session_browser = SessionBrowser(
            context=context, use_screenshot=use_screenshot
        )

        self._selector = NaturalSelector(
            llm=selector_llm or llm,
            session_browser=self.session_browser,
            include_screenshot=False,
            mode=mode,
        )

    async def execute(
        self,
        task_description: str,
        max_correction_attempts: int = 3,
        resources: Optional[Dict[str, str]] = None,
        wait_after_action: Optional[float] = None,
        mode: Optional[str] = None,
    ) -> TaskResult:
        """
        Execute a task autonomously using Worker/Verifier loop.

        Args:
            task_description: Task description in natural language
            max_correction_attempts: Maximum correction retry attempts (default: 3)
            resources: Optional dict of file resources (name -> path)
            wait_after_action: Wait time in seconds after each action (overrides agent default if provided)
            mode: DOM context mode - "accessibility" or "dom" (overrides agent default if provided)

        Returns:
            TaskResult with status, output, feedback, and execution history

        Raises:
            RuntimeError: If no context is available
        """
        if not self.session_browser.get_current_page():
            await self.session_browser.create_page()

        # Use task-level wait_after_action if provided, otherwise use agent default
        effective_wait = (
            wait_after_action
            if wait_after_action is not None
            else self.wait_after_action
        )

        # Use task-level mode if provided, otherwise use agent default
        effective_mode = mode if mode is not None else self.mode

        task_executor = TaskExecutor(
            llm=self.llm,
            session_browser=self.session_browser,
            wait_after_action=effective_wait,
            resources=resources,
            mode=effective_mode,
        )

        result = await task_executor.run(
            task_description=task_description,
            max_correction_attempts=max_correction_attempts,
        )

        return result

    async def open_page(self, url: Optional[str] = None) -> Page:
        """
        Open a new page and switch to it.

        Args:
            url: Optional URL to navigate to

        Returns:
            The new Page instance

        Raises:
            RuntimeError: If no context is available
        """
        return await self.session_browser.create_page(url)

    async def close_page(self, page: Optional[Page] = None) -> None:
        """
        Close a page (closes current page if page=None).

        Args:
            page: Page to close (defaults to current page)
        """
        await self.session_browser.close_page(page)

    def get_current_page(self) -> Optional[Page]:
        """Get the current active page."""
        return self.session_browser.get_current_page()

    def get_pages(self) -> List[Page]:
        """
        Get all open pages.

        Returns:
            List of Page instances
        """
        return self.session_browser.get_pages()

    @property
    def page_count(self) -> int:
        """Number of open pages."""
        return self.session_browser.page_count

    async def navigate(self, url: str):
        """
        Navigate to URL (low-level imperative mode).

        Auto-creates a page if none exists.

        Args:
            url: URL to navigate to
        """
        await self.session_browser.navigate(url)

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
        return await self._selector.select(description)

    async def wait_for_load(self, timeout: int = 10000):
        """
        Wait for page to fully load.

        Args:
            timeout: Maximum time to wait in milliseconds (default: 10000ms)

        Raises:
            RuntimeError: If no page is opened
            TimeoutError: If page doesn't load within timeout
        """
        await self.session_browser.wait_for_load(timeout=timeout)

    async def wait(self, seconds: float):
        """
        Wait for a specific amount of time.

        Args:
            seconds: Number of seconds to wait
        """
        await custom_wait(seconds)

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
        return await self.session_browser.screenshot(path=path, full_page=full_page)

    def set_page(self, page: Page) -> None:
        """
        Set/switch/inject a page as the current page.

        Supports injecting external pages, switching between managed pages, or setting a new page to work with.

        Args:
            page: Page instance to set as current
        """
        self.session_browser.set_page(page)

    def set_context(self, context: Context) -> None:
        """
        Set or update the context.

        Enables multi-page operations after initialization.

        Args:
            context: Context instance for creating pages
        """
        self.context = context
        self.session_browser.set_context(context)

    async def close(self) -> None:
        """Close the agent and cleanup all resources."""
        await self.session_browser.close()

        if self.context:
            await self.context.close()
