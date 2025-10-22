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

    Works with a Session to manage multiple tabs/pages.
    Provides high-level execute() for autonomous task completion
    and low-level methods for imperative control.
    """

    def __init__(self, llm: LLM, session: Session):
        """
        Initialize agent.

        Args:
            llm: LLM instance for reasoning
            session: Session instance (manages multiple tabs/pages)
        """
        self.llm = llm
        self.session = session

        # Tab management
        self.tabs: List[Page] = []
        self.current_tab: Optional[Page] = None

        # Infrastructure (rebuilt when switching tabs)
        self.llm_browser: Optional[LLMBrowser] = None
        self.tool_registry = ToolRegistry()
        self.step_history = StepHistory()

    async def _ensure_tab(self) -> Page:
        """
        Ensure we have a current tab, creating one if needed.

        Returns:
            Current Page instance
        """
        if self.current_tab is None:
            # Auto-create first tab
            await self.new_tab()

        return self.current_tab

    def _register_tools(self) -> None:
        """Register available tools in the registry."""
        if self.llm_browser is None:
            return

        from .tools.browser import NavigateTool, ClickTool, FillTool

        # Clear existing tools (keeps same registry instance)
        self.tool_registry.clear()

        # Re-register tools with current LLMBrowser
        self.tool_registry.register(NavigateTool(self.llm_browser))
        self.tool_registry.register(ClickTool(self.llm_browser))
        self.tool_registry.register(FillTool(self.llm_browser))

    # === Tab Management Methods ===

    async def new_tab(self, url: Optional[str] = None) -> Page:
        """
        Create and switch to a new tab.

        Args:
            url: Optional URL to navigate to

        Returns:
            The new Page instance

        Example:
            >>> page2 = await agent.new_tab("https://github.com")
        """
        # Create new page
        page = await self.session.create_page()
        self.tabs.append(page)

        # Switch to new tab
        self.current_tab = page
        self.llm_browser = LLMBrowser(page, self.llm)
        self._register_tools()

        # Navigate if URL provided
        if url:
            await page.navigate(url)

        return page

    async def switch_tab(self, page: Page) -> None:
        """
        Switch to a different tab.

        Args:
            page: Page to switch to

        Raises:
            ValueError: If page is not managed by this agent

        Example:
            >>> await agent.switch_tab(page1)
        """
        if page not in self.tabs:
            raise ValueError("Tab not managed by this agent")

        self.current_tab = page
        self.llm_browser = LLMBrowser(page, self.llm)
        self._register_tools()

    async def close_tab(self, page: Optional[Page] = None) -> None:
        """
        Close a tab (closes current tab if page=None).

        Args:
            page: Page to close (defaults to current tab)

        Raises:
            ValueError: If page is not managed by this agent

        Example:
            >>> await agent.close_tab(page2)
            >>> await agent.close_tab()  # Close current tab
        """
        page = page or self.current_tab

        if page is None:
            return  # No tabs to close

        if page not in self.tabs:
            raise ValueError("Tab not managed by this agent")

        await page.close()
        self.tabs.remove(page)

        # If closed current tab, switch to another or None
        if self.current_tab == page:
            self.current_tab = self.tabs[0] if self.tabs else None
            if self.current_tab:
                self.llm_browser = LLMBrowser(self.current_tab, self.llm)
                self._register_tools()
            else:
                self.llm_browser = None

    def get_tabs(self) -> List[Page]:
        """
        Get all open tabs.

        Returns:
            List of Page instances
        """
        return self.tabs.copy()

    @property
    def tab_count(self) -> int:
        """Number of open tabs."""
        return len(self.tabs)

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
        # Ensure we have a tab
        await self._ensure_tab()

        # Clear history if requested
        if clear_history:
            self.step_history.clear()

        # Create roles
        proposer = Proposer(
            self.llm, task, self.step_history, self.tool_registry, self.llm_browser
        )
        executer = Executer(self.tool_registry)
        verifier = Verifier(self.llm, task, self.step_history, self.llm_browser)

        # Agent loop
        for i in range(max_steps):
            # 1. Propose next action
            action = await proposer.propose()

            # 2. Execute action
            exec_result = await executer.execute(action)

            # 3. Verify if task complete
            verify_result = await verifier.verify(action, exec_result)

            # 4. Create step and add to history
            step = Step(
                proposal=action, execution=exec_result, verification=verify_result
            )
            self.step_history.add_step(step)

            # 5. Check if done
            if verify_result.complete:
                return TaskResult(
                    completed=True,
                    steps=self.step_history.get_all(),
                    message=verify_result.message,
                )

        # Max steps reached without completion
        return TaskResult(
            completed=False,
            steps=self.step_history.get_all(),
            message=f"Task not completed after {max_steps} steps",
        )

    # === Low-Level Imperative Mode ===

    async def navigate(self, url: str):
        """
        Navigate to URL (low-level imperative mode).

        Args:
            url: URL to navigate to

        Example:
            >>> await agent.navigate("https://google.com")
        """
        page = await self._ensure_tab()
        await page.navigate(url)

    async def select(self, description: str):
        """
        Select element by natural language description (low-level imperative mode).

        Args:
            description: Natural language description of element

        Returns:
            Browser Element with .click(), .fill() methods

        Example:
            >>> elem = await agent.select("the search button")
            >>> await elem.click()
        """
        await self._ensure_tab()
        return await self.llm_browser.select(description)

    async def wait_for_idle(self, timeout: int = 30000):
        """
        Wait for page to be idle (network and DOM stable).

        Waits for network activity to finish and DOM to stabilize.
        Useful after navigation, clicks, or dynamic content updates.

        Args:
            timeout: Maximum time to wait in milliseconds (default: 30000ms = 30s)

        Raises:
            TimeoutError: If page doesn't become idle within timeout

        Example:
            >>> await agent.navigate("https://example.com")
            >>> await agent.wait_for_idle()  # Wait for page to fully load
        """
        page = await self._ensure_tab()
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

    # === Cleanup ===

    async def close(self) -> None:
        """
        Close the agent and cleanup all resources.

        Closes all tabs and the session.
        """
        # Close all tabs
        for page in self.tabs[:]:
            await page.close()
        self.tabs.clear()
        self.current_tab = None
        self.llm_browser = None

        # Close session
        await self.session.close()
