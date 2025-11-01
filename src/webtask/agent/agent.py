"""Agent - main interface for web automation."""

import logging
from typing import List, Optional
from ..llm import LLM
from ..browser import Page, Session
from ..llm_browser import LLMBrowser
from ..llm_browser.dom_filter_config import DomFilterConfig
from .tool import ToolRegistry
from .step_history import StepHistory
from .step import Step, TaskResult
from .role import Proposer, Executer, Verifier


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
        dom_filter_config: Optional[DomFilterConfig] = None,
        use_screenshot: bool = True,
    ):
        """
        Initialize agent.

        Args:
            llm: LLM instance for reasoning
            session: Optional Session instance for multi-page support
            page: Optional Page instance to use as initial page
            action_delay: Delay in seconds after actions (default: 1.0)
            dom_filter_config: Configuration for DOM filtering
            use_screenshot: Use screenshots with bounding boxes in LLM context (default: True)
        """
        self.llm = llm
        self.session = session
        self.action_delay = action_delay
        self.dom_filter_config = dom_filter_config
        self.use_screenshot = use_screenshot
        self.logger = logging.getLogger(__name__)

        self.llm_browser = LLMBrowser(session, dom_filter_config, use_screenshot)

        if page is not None:
            self.llm_browser.set_page(page)

        self.tool_registry = ToolRegistry()
        self.step_history = StepHistory()

        self._register_tools()

        self.current_task: Optional[str] = None
        self.proposer: Optional[Proposer] = None
        self.executer: Optional[Executer] = None
        self.verifier: Optional[Verifier] = None

    def _register_tools(self) -> None:
        from .tools.browser import NavigateTool, ClickTool, FillTool, TypeTool

        self.tool_registry.clear()

        self.tool_registry.register(NavigateTool(self.llm_browser))
        self.tool_registry.register(ClickTool(self.llm_browser))
        self.tool_registry.register(FillTool(self.llm_browser))
        self.tool_registry.register(TypeTool(self.llm_browser))

    async def execute(
        self, task: str, max_steps: int = 10, clear_history: bool = True
    ) -> TaskResult:
        """
        Execute a task autonomously.

        Args:
            task: Task description in natural language
            max_steps: Maximum number of steps before giving up
            clear_history: Clear step history before starting (default: True)

        Returns:
            TaskResult with completion status, steps, and final message
        """
        self.set_task(task, clear_history=clear_history)

        for i in range(max_steps):
            step = await self.run_step()

            if step.verification.complete:
                return TaskResult(
                    completed=True,
                    steps=self.step_history.get_all(),
                    message=step.verification.message,
                )

        return TaskResult(
            completed=False,
            steps=self.step_history.get_all(),
            message=f"Task not completed after {max_steps} steps",
        )

    def set_task(self, task: str, clear_history: bool = True) -> None:
        """
        Set current task for step-by-step execution.

        Args:
            task: Task description in natural language
            clear_history: Clear step history before starting (default: True)
        """
        self.current_task = task

        if clear_history:
            self.step_history.clear()

        self.proposer = Proposer(
            self.llm, task, self.step_history, self.tool_registry, self.llm_browser
        )
        self.executer = Executer(self.tool_registry, self.action_delay)
        self.verifier = Verifier(self.llm, task, self.step_history, self.llm_browser)

    async def run_step(self) -> Step:
        """
        Execute one step of the current task.

        Returns:
            Step with proposals, executions, and verification result

        Raises:
            RuntimeError: If no task is set (call set_task first)
        """
        from ..utils import wait

        if self.current_task is None or self.proposer is None:
            raise RuntimeError("No task set. Call set_task() first.")

        step_num = len(self.step_history.get_all()) + 1
        self.logger.debug(f"=== Starting Step {step_num} ===")

        self.logger.debug("Phase 1: Proposing actions...")
        actions = await self.proposer.propose()
        self.logger.debug(f"Proposed {len(actions)} action(s)")
        for i, action in enumerate(actions, 1):
            self.logger.debug(f"  Action {i}: {action.tool_name}")
            self.logger.debug(f"    Reason: {action.reason}")
            self.logger.debug(f"    Parameters: {action.parameters}")

        self.logger.debug("Phase 2: Executing actions...")
        exec_results = await self.executer.execute(actions)
        success_count = sum(1 for r in exec_results if r.success)
        self.logger.debug(
            f"Execution complete: {success_count}/{len(exec_results)} successful"
        )

        # Wait for page to stabilize before verification
        if actions:
            self.logger.debug(
                f"Phase 3: Waiting {self.action_delay}s for page to stabilize..."
            )
            await wait(self.action_delay)

        self.logger.debug("Phase 4: Verifying task completion...")
        verify_result = await self.verifier.verify(actions, exec_results)
        self.logger.debug(
            f"Verification result: {'Complete' if verify_result.complete else 'Incomplete'}"
        )
        self.logger.debug(f"Verification message: {verify_result.message}")

        step = Step(
            proposals=actions, executions=exec_results, verification=verify_result
        )
        self.step_history.add_step(step)

        self.logger.debug(f"=== Step {step_num} Complete ===\n")

        return step

    def clear_history(self) -> None:
        """Clear step history and task state."""
        self.step_history.clear()
        self.current_task = None
        self.proposer = None
        self.executer = None
        self.verifier = None

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

        selector = NaturalSelector(self.llm, self.llm_browser)
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
