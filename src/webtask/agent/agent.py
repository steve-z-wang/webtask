"""Agent - main interface for web automation."""

from typing import List, Optional
from ..llm import LLM
from ..browser import Page, Session
from ..llm_browser import LLMBrowser
from .tool import ToolRegistry
from .step_history import StepHistory
from .step import Step, TaskResult
from .role import Proposer, Executer, Verifier


class Agent:
    """
    Main agent interface for web automation.

    Supports two modes:
    - Multi-page mode: Works with a Session to manage multiple pages
    - Single-page mode: Works with an injected Page (no session required)

    Provides high-level execute() for autonomous task completion
    and low-level methods for imperative control.
    """

    def __init__(
        self,
        llm: LLM,
        session: Optional[Session] = None,
        page: Optional[Page] = None,
        action_delay: float = 1.0
    ):
        """
        Initialize agent.

        Args:
            llm: LLM instance for reasoning
            session: Optional Session instance for multi-page support.
                     If None, agent works in single-page mode.
            page: Optional Page instance to use as initial page.
                  Can be set later with set_page().
            action_delay: Delay in seconds after actions like click/navigate (default: 1.0)

        Examples:
            >>> # Multi-page mode with session
            >>> agent = Agent(llm, session=my_session)
            >>> await agent.open_page("https://google.com")
            >>>
            >>> # Single-page mode with existing page
            >>> agent = Agent(llm, page=my_page)
            >>> await agent.execute("click login")
            >>>
            >>> # Start empty, configure later
            >>> agent = Agent(llm)
            >>> agent.set_page(my_page)
        """
        self.llm = llm
        self.session = session
        self.action_delay = action_delay

        # LLMBrowser manages pages internally
        self.llm_browser = LLMBrowser(llm, session)

        # Set initial page if provided
        if page is not None:
            self.llm_browser.set_page(page)

        # Infrastructure
        self.tool_registry = ToolRegistry()
        self.step_history = StepHistory()

        # Register tools immediately
        self._register_tools()

        # Task state (for step-by-step execution)
        self.current_task: Optional[str] = None
        self.proposer: Optional[Proposer] = None
        self.executer: Optional[Executer] = None
        self.verifier: Optional[Verifier] = None

    def _register_tools(self) -> None:
        """Register available tools in the registry."""
        from .tools.browser import NavigateTool, ClickTool, FillTool, TypeTool

        # Clear existing tools (keeps same registry instance)
        self.tool_registry.clear()

        # Re-register tools with current LLMBrowser
        self.tool_registry.register(NavigateTool(self.llm_browser))
        self.tool_registry.register(ClickTool(self.llm_browser))
        self.tool_registry.register(FillTool(self.llm_browser))
        self.tool_registry.register(TypeTool(self.llm_browser))

    # === High-Level Autonomous Mode ===

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
        # Set task (initializes roles and clears history if requested)
        self.set_task(task, clear_history=clear_history)

        # Execute steps until done or max_steps reached
        for i in range(max_steps):
            step = await self.run_step()

            # Check if done
            if step.verification.complete:
                return TaskResult(
                    completed=True,
                    steps=self.step_history.get_all(),
                    message=step.verification.message,
                )

        # Max steps reached without completion
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

        Example:
            >>> agent.set_task("search for cats")
            >>> result = await agent.execute_step()
        """
        self.current_task = task

        # Clear history if requested
        if clear_history:
            self.step_history.clear()

        # Create roles
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

        Example:
            >>> agent.set_task("search for cats")
            >>> step = await agent.execute_step()
            >>> print(step.verification.complete)
        """
        from ..utils import wait

        # Check that task is set
        if self.current_task is None or self.proposer is None:
            raise RuntimeError("No task set. Call set_task() first.")

        # 1. Propose next actions
        actions = await self.proposer.propose()

        # 2. Execute actions
        exec_results = await self.executer.execute(actions)

        # 3. Wait for page to stabilize before verification
        if actions:  # Only wait if actions were executed
            await wait(self.action_delay)

        # 4. Verify if task complete
        verify_result = await self.verifier.verify(actions, exec_results)

        # 5. Create step and add to history
        step = Step(
            proposals=actions, executions=exec_results, verification=verify_result
        )
        self.step_history.add_step(step)

        return step

    def clear_history(self) -> None:
        """
        Clear step history and task state.

        Resets the agent to a clean state, ready for a new task.

        Example:
            >>> agent.clear_history()
            >>> agent.set_task("new task")
        """
        self.step_history.clear()
        self.current_task = None
        self.proposer = None
        self.executer = None
        self.verifier = None

    # === Page Management Methods ===

    async def open_page(self, url: Optional[str] = None) -> Page:
        """
        Open a new page and switch to it.

        Requires a session. Raises error if no session available.

        Args:
            url: Optional URL to navigate to

        Returns:
            The new Page instance

        Raises:
            RuntimeError: If no session is available

        Example:
            >>> page2 = await agent.open_page("https://github.com")
        """
        return await self.llm_browser.create_page(url)

    async def close_page(self, page: Optional[Page] = None) -> None:
        """
        Close a page (closes current page if page=None).

        Args:
            page: Page to close (defaults to current page)

        Example:
            >>> await agent.close_page(page2)
            >>> await agent.close_page()  # Close current page
        """
        await self.llm_browser.close_page(page)

    def get_pages(self) -> List[Page]:
        """
        Get all open pages.

        Returns:
            List of Page instances

        Example:
            >>> pages = agent.get_pages()
            >>> print(f"Open pages: {len(pages)}")
        """
        return list(self.llm_browser._pages.values())

    @property
    def page_count(self) -> int:
        """Number of open pages."""
        return len(self.llm_browser._pages)

    # === Low-Level Imperative Mode ===

    async def navigate(self, url: str):
        """
        Navigate to URL (low-level imperative mode).

        Auto-creates a page if none exists.

        Args:
            url: URL to navigate to

        Example:
            >>> await agent.navigate("https://google.com")
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

        Example:
            >>> elem = await agent.select("the search button")
            >>> await elem.click()
        """
        return await self.llm_browser.select(description)

    async def wait_for_idle(self, timeout: int = 30000):
        """
        Wait for page to be idle (network and DOM stable).

        Waits for network activity to finish and DOM to stabilize.
        Useful after navigation, clicks, or dynamic content updates.

        Args:
            timeout: Maximum time to wait in milliseconds (default: 30000ms = 30s)

        Raises:
            RuntimeError: If no page is opened
            TimeoutError: If page doesn't become idle within timeout

        Example:
            >>> await agent.navigate("https://example.com")
            >>> await agent.wait_for_idle()  # Wait for page to fully load
        """
        page = self.llm_browser._require_page()
        await page.wait_for_idle(timeout=timeout)

    async def wait(self, seconds: float):
        """
        Wait for a specific amount of time.

        Simple delay/sleep. Useful for waiting for animations or timed events.

        Args:
            seconds: Number of seconds to wait

        Example:
            >>> await agent.click("submit button")
            >>> await agent.wait(2)  # Wait 2 seconds for animation
        """
        import asyncio

        await asyncio.sleep(seconds)

    async def screenshot(
        self,
        path: Optional[str] = None,
        full_page: bool = False
    ) -> bytes:
        """
        Take a screenshot of the current page.

        Args:
            path: Optional file path to save screenshot. If None, doesn't save to disk.
            full_page: Whether to screenshot the full scrollable page (default: False)

        Returns:
            Screenshot as bytes (PNG format)

        Raises:
            RuntimeError: If no page is opened

        Example:
            >>> # Save screenshot to file
            >>> await agent.screenshot("step1.png")
            >>>
            >>> # Get screenshot bytes
            >>> screenshot_bytes = await agent.screenshot()
            >>>
            >>> # Full page screenshot
            >>> await agent.screenshot("fullpage.png", full_page=True)
        """
        page = self.llm_browser._require_page()
        return await page.screenshot(path=path, full_page=full_page)

    # === Configuration Methods ===

    def set_page(self, page: Page) -> None:
        """
        Set/switch/inject a page as the current page.

        This method handles multiple use cases:
        - Inject an external page into the agent
        - Switch focus to an existing managed page
        - Set a new page to work with

        Args:
            page: Page instance to set as current

        Examples:
            >>> # Inject existing Playwright page
            >>> from webtask.integrations.browser.playwright import PlaywrightPage
            >>> wrapped_page = PlaywrightPage(my_playwright_page)
            >>> agent.set_page(wrapped_page)
            >>>
            >>> # Switch between managed pages
            >>> page1 = await agent.open_page("https://google.com")
            >>> page2 = await agent.open_page("https://github.com")
            >>> agent.set_page(page1)  # Switch back to google
        """
        self.llm_browser.set_page(page)

    def set_session(self, session: Session) -> None:
        """
        Set or update the session.

        Enables multi-page operations after initialization.

        Args:
            session: Session instance for creating pages

        Example:
            >>> # Start with single page, upgrade to multi-page
            >>> agent = Agent(llm, page=my_page)
            >>> agent.set_session(my_session)
            >>> await agent.open_page("https://github.com")  # Now works!
        """
        self.session = session
        self.llm_browser.set_session(session)

    # === Cleanup ===

    async def close(self) -> None:
        """
        Close the agent and cleanup all resources.

        Closes all pages and the session (if available).
        """
        # Close all pages via LLMBrowser
        for page in list(self.llm_browser._pages.values()):
            await self.llm_browser.close_page(page)

        # Close session if available
        if self.session is not None:
            await self.session.close()
