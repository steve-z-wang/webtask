"""Agent - main interface for web automation."""

import logging
from typing import Dict, List, Optional, Any
from webtask.llm import LLM
from webtask.browser import Page, Context
from webtask._internal.agent.session_browser import SessionBrowser
from webtask._internal.agent.worker.worker import Worker
from webtask._internal.agent.worker.worker_session import WorkerSession
from webtask._internal.utils.wait import wait as custom_wait


class Agent:
    """
    Main agent interface for web automation.

    Requires a Context for browser management and page operations.

    Primary interface:
    - High-level autonomous: do(task) - Agent autonomously executes tasks with Worker
    - Supports persist_context for multi-turn conversations
    """

    def __init__(
        self,
        llm: LLM,
        context: Optional[Context] = None,
        wait_after_action: float = 0.2,
        use_screenshot: bool = True,
        mode: str = "accessibility",
        persist_context: bool = False,
    ):
        """
        Initialize agent.

        Args:
            llm: LLM instance for reasoning and task execution
            context: Optional context instance (can be set later with set_context())
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            use_screenshot: Use screenshots with bounding boxes in LLM context (default: True)
            mode: DOM context mode - "accessibility" (default) or "dom"
            persist_context: If True, maintain conversation history between do() calls (default: False)
        """
        self.llm = llm
        self.context = context
        self.use_screenshot = use_screenshot
        self.wait_after_action = wait_after_action
        self.mode = mode
        self.persist_context = persist_context
        self.logger = logging.getLogger(__name__)

        self.session_browser = SessionBrowser(
            context=context, use_screenshot=use_screenshot
        )

        # Store last WorkerSession if persist_context=True
        self.last_session: Optional[WorkerSession] = None

    async def do(
        self,
        task: str,
        max_steps: int = 20,
        resources: Optional[Dict[str, str]] = None,
        wait_after_action: Optional[float] = None,
        mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a task using Worker (new simplified interface).

        Args:
            task: Task description in natural language
            max_steps: Maximum number of steps to execute (default: 20)
            resources: Optional dict of file resources (name -> path)
            wait_after_action: Wait time in seconds after each action (overrides agent default if provided)
            mode: DOM context mode - "accessibility" or "dom" (overrides agent default if provided)

        Returns:
            Dict with status, output, and feedback:
            {
                "status": "completed" | "aborted" | "max_steps",
                "output": Any,  # Structured data from set_output tool
                "feedback": str  # Summary of what happened
            }

        Raises:
            RuntimeError: If no context is available
        """
        if not self.session_browser.get_current_page():
            await self.session_browser.create_page()

        # Check if current page is on a problematic URL (Shadow DOM issues)
        page = self.session_browser.get_current_page()
        if page and page.url.startswith("chrome://"):
            # Navigate away from chrome:// URLs which use Shadow DOM
            await page.navigate("about:blank")

        # Use task-level wait_after_action if provided, otherwise use agent default
        effective_wait = (
            wait_after_action
            if wait_after_action is not None
            else self.wait_after_action
        )

        # Use task-level mode if provided, otherwise use agent default
        effective_mode = mode if mode is not None else self.mode

        # Create worker
        worker = Worker(
            llm=self.llm,
            session_browser=self.session_browser,
            wait_after_action=effective_wait,
            resources=resources,
            mode=effective_mode,
        )

        # Execute with optional context persistence
        if self.persist_context:
            session = await worker.do(task, self.last_session, max_steps)
            self.last_session = session
        else:
            session = await worker.do(task, None, max_steps)

        # Convert WorkerSession to simple user-facing result
        return {
            "status": session.status.value,
            "output": session.output,
            "feedback": session.feedback,
        }

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
