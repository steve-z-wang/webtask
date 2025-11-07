"""Agent - main interface for web automation."""

import logging
from typing import Dict, List, Optional
from ..llm import LLM
from ..browser import Page, Session
from ..llm_browser import LLMBrowser
from .task import TaskExecution
from .task_executor import TaskExecutor


class Agent:
    """
    Main agent interface for web automation.

    Requires a Session for browser management and page operations.

    Two modes of operation:
    - High-level autonomous: execute(task) - Agent autonomously plans and executes with scheduler-worker architecture
    - Low-level imperative: navigate(), select(), wait() - Direct control for manual workflows
    """

    def __init__(
        self,
        llm: LLM,
        session: Optional[Session] = None,
        action_delay: float = 1.0,
        use_screenshot: bool = True,
        selector_llm: Optional[LLM] = None,
    ):
        """
        Initialize agent.

        Args:
            llm: LLM instance for reasoning (task planning, completion checking)
            session: Optional session instance (can be set later with set_session())
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

        self.llm_browser = LLMBrowser(session, action_delay=action_delay, use_screenshot=use_screenshot) if session else None

    async def execute(
        self,
        task_description: str,
        max_cycles: int = 10,
        resources: Optional[Dict[str, str]] = None,
    ) -> TaskExecution:
        """
        Execute a task autonomously using scheduler-worker architecture.

        Args:
            task_description: Task description in natural language
            max_cycles: Maximum scheduler-worker cycles (default: 10)
            resources: Optional dict of file resources (name -> path)

        Returns:
            TaskExecution object with execution history (sessions and subtasks)

        Raises:
            RuntimeError: If no session is available
        """
        if not self.llm_browser:
            raise RuntimeError("No session available. Call set_session() first.")

        # Create task execution
        task = TaskExecution(
            description=task_description,
            resources=resources or {},
        )

        # Create execution logger
        from .execution_logger import ExecutionLogger
        execution_logger = ExecutionLogger()

        # Create planner, worker, and verifier
        from .planner.planner import Planner
        from .worker.worker import Worker
        from .verifier.verifier import Verifier

        planner = Planner(
            llm=self.llm,
            llm_browser=self.llm_browser,
            logger=execution_logger,
        )
        worker = Worker(
            llm=self.llm,
            llm_browser=self.llm_browser,
            resources=task.resources,
            logger=execution_logger,
        )
        verifier = Verifier(
            llm=self.llm,
            llm_browser=self.llm_browser,
            logger=execution_logger,
        )

        # Create task executor
        task_executor = TaskExecutor(
            planner=planner,
            worker=worker,
            verifier=verifier,
            logger=execution_logger,
        )

        # Run adaptive Planner→Worker→Verifier loop
        return await task_executor.run(task, max_cycles=max_cycles)

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

    def get_current_page(self) -> Optional[Page]:
        """Get the current active page."""
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
        from ..naturalselector import NaturalSelector

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
        if self.llm_browser is None:
            self.llm_browser = LLMBrowser(None, self.use_screenshot)
        self.llm_browser.set_page(page)

    def set_session(self, session: Session) -> None:
        """
        Set or update the session.

        Enables multi-page operations after initialization.

        Args:
            session: Session instance for creating pages
        """
        self.session = session
        if self.llm_browser is None:
            self.llm_browser = LLMBrowser(session, self.use_screenshot)
        else:
            self.llm_browser.set_session(session)

    async def close(self) -> None:
        """Close the agent and cleanup all resources."""
        if self.llm_browser:
            for page in list(self.llm_browser._pages.values()):
                await self.llm_browser.close_page(page)

        if self.session:
            await self.session.close()
