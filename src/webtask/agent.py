"""Agent - main interface for web automation."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .llm import LLM
from ._internal.llm import TypedLLM
from .browser import Page, Session
from ._internal.agent.agent_browser import AgentBrowser
from ._internal.natural_selector import NaturalSelector
from ._internal.agent.task import Task, TaskExecution
from ._internal.agent.task_executor import TaskExecutor
from ._internal.agent.manager.manager import Manager
from ._internal.agent.worker.worker import Worker
from ._internal.agent.verifier.verifier import Verifier
from ._internal.config import Config


class Agent:
    """
    Main agent interface for web automation.

    Requires a Session for browser management and page operations.

    Two modes of operation:
    - High-level autonomous: execute(task) - Agent autonomously plans and executes with manager-worker architecture
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
        self.session = session
        self.use_screenshot = use_screenshot
        self.logger = logging.getLogger(__name__)

        self.typed_llm = TypedLLM(llm)
        self.typed_selector_llm = TypedLLM(selector_llm or llm)

        # Create shared browser (used by Worker for interactions, Verifier for screenshots)
        self.agent_browser = AgentBrowser(
            session=session, use_screenshot=use_screenshot
        )

        # Create roles (reused across tasks)
        self.manager = Manager(typed_llm=self.typed_llm)
        self.worker = Worker(typed_llm=self.typed_llm, agent_browser=self.agent_browser)
        self.verifier = Verifier(
            typed_llm=self.typed_llm, agent_browser=self.agent_browser
        )

    async def execute(
        self,
        task_description: str,
        max_cycles: int = 10,
        resources: Optional[Dict[str, str]] = None,
    ) -> TaskExecution:
        """
        Execute a task autonomously using manager-worker architecture.

        Args:
            task_description: Task description in natural language
            max_cycles: Maximum manager-worker cycles (default: 10)
            resources: Optional dict of file resources (name -> path)

        Returns:
            TaskExecution object with execution history (sessions and subtasks)

        Raises:
            RuntimeError: If no session is available
        """
        if not self.agent_browser.get_current_page():
            raise RuntimeError("No session available. Call set_session() first.")

        # Create task definition
        task = Task(
            description=task_description,
            resources=resources or {},
        )

        # Create task execution (state container)
        task_execution = TaskExecution(task=task)

        # Update roles for this task
        self.worker.set_resources(task.resources)

        # Create task executor
        task_executor = TaskExecutor(
            manager=self.manager,
            worker=self.worker,
            verifier=self.verifier,
        )

        # Run adaptive Manager→Worker→Verifier loop
        result = await task_executor.run(task_execution, max_cycles=max_cycles)

        # Save debug summary if enabled
        if Config().is_debug_enabled():
            debug_dir = Path(Config().get_debug_dir())
            debug_dir.mkdir(parents=True, exist_ok=True)
            summary_path = debug_dir / "summary.txt"
            with open(summary_path, "w") as f:
                f.write(str(result))
            logging.info(f"Debug summary saved to: {summary_path}")

        return result

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
        return await self.agent_browser.create_page(url)

    async def close_page(self, page: Optional[Page] = None) -> None:
        """
        Close a page (closes current page if page=None).

        Args:
            page: Page to close (defaults to current page)
        """
        await self.agent_browser.close_page(page)

    def get_current_page(self) -> Optional[Page]:
        """Get the current active page."""
        return self.agent_browser.get_current_page()

    def get_pages(self) -> List[Page]:
        """
        Get all open pages.

        Returns:
            List of Page instances
        """
        return self.agent_browser.get_pages()

    @property
    def page_count(self) -> int:
        """Number of open pages."""
        return self.agent_browser.page_count

    async def navigate(self, url: str):
        """
        Navigate to URL (low-level imperative mode).

        Auto-creates a page if none exists.

        Args:
            url: URL to navigate to
        """
        await self.agent_browser.navigate(url)

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
        selector = NaturalSelector(self.typed_selector_llm, self.agent_browser)
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
        await self.agent_browser.wait_for_idle(timeout=timeout)

    async def wait(self, seconds: float):
        """
        Wait for a specific amount of time.

        Args:
            seconds: Number of seconds to wait
        """
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
        return await self.agent_browser.screenshot(path=path, full_page=full_page)

    def set_page(self, page: Page) -> None:
        """
        Set/switch/inject a page as the current page.

        Supports injecting external pages, switching between managed pages, or setting a new page to work with.

        Args:
            page: Page instance to set as current
        """
        self.agent_browser.set_page(page)

    def set_session(self, session: Session) -> None:
        """
        Set or update the session.

        Enables multi-page operations after initialization.

        Args:
            session: Session instance for creating pages
        """
        self.session = session
        self.agent_browser.set_session(session)

    async def close(self) -> None:
        """Close the agent and cleanup all resources."""
        await self.agent_browser.close()

        if self.session:
            await self.session.close()
