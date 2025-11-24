"""Agent - main interface for web automation."""

import logging
from typing import List, Optional, Type

from pydantic import BaseModel, Field
from dodo import Agent as DodoAgent, Text, Image

from webtask.llm import LLM
from webtask.browser import Context, Page
from webtask._internal.agent.file_manager import FileManager
from webtask._internal.agent.tools import (
    GotoTool,
    ClickTool,
    FillTool,
    TypeTool,
    UploadTool,
    WaitTool,
    OpenTabTool,
    SwitchTabTool,
    ClickAtTool,
    HoverAtTool,
    TypeTextAtTool,
    ScrollAtTool,
    ScrollDocumentTool,
    DragAndDropTool,
    GoBackTool,
    GoForwardTool,
    KeyCombinationTool,
)
from webtask.exceptions import TaskAbortedError
from .result import Result, Verdict
from webtask._internal.agent.agent_browser import AgentBrowser


class Agent:
    """
    Main agent interface for web automation.

    Wraps dodo's Agent with browser-specific tools and context.

    Primary interface:
    - do(task) - Execute a task autonomously
    - verify(condition) - Check if a condition is true
    - extract(what) - Extract information from the page
    """

    # Valid modes for agent operation
    VALID_MODES = ("text", "visual", "full")

    def __init__(
        self,
        llm: LLM,
        context: Context,
        mode: str = "text",
        stateful: bool = True,
    ):
        """
        Initialize agent.

        Args:
            llm: LLM instance for reasoning and task execution
            context: Context instance for browser management
            mode: Agent mode - "text" (DOM tools), "visual" (pixel tools), "full" (both)
            stateful: If True, maintain conversation history between do() calls (default: True)
        """
        if mode not in self.VALID_MODES:
            raise ValueError(
                f"Invalid mode '{mode}'. Must be one of: {self.VALID_MODES}"
            )

        self.llm = llm
        self.context = context
        self.mode = mode
        self.stateful = stateful
        self.logger = logging.getLogger(__name__)

        # Get coordinate_scale from LLM if available (e.g., GeminiComputerUse)
        coordinate_scale = getattr(llm, "coordinate_scale", None)

        # Create AgentBrowser once - shared across all do() calls
        self.browser = AgentBrowser(context=context, coordinate_scale=coordinate_scale)

        # Configuration for tasks (set by do/verify/extract)
        self._wait_after_action: float = 0.2
        self._dom_mode: str = "accessibility"
        self._file_manager: Optional[FileManager] = None

        # Dodo agent (created lazily for each configuration)
        self._dodo_agent: Optional[DodoAgent] = None

    def _create_browser_tools(self) -> List:
        """Create browser tools based on agent mode.

        Returns:
            List of browser tools appropriate for the mode
        """
        # Common tools for all modes
        common_tools = [
            WaitTool(),
            GotoTool(self.browser),
            GoBackTool(self.browser),
            GoForwardTool(self.browser),
            OpenTabTool(self.browser),
            SwitchTabTool(self.browser),
            ScrollDocumentTool(self.browser),
            KeyCombinationTool(self.browser),
        ]

        # Text mode: DOM-based tools (element IDs)
        text_tools = [
            ClickTool(self.browser),
            FillTool(self.browser),
            TypeTool(self.browser),
        ]

        # Visual mode: Pixel-based tools (coordinates)
        visual_tools = [
            ClickAtTool(self.browser),
            TypeTextAtTool(self.browser),
            HoverAtTool(self.browser),
            ScrollAtTool(self.browser),
            DragAndDropTool(self.browser),
        ]

        # Build tool list based on mode
        if self.mode == "text":
            tools = common_tools + text_tools
        elif self.mode == "visual":
            tools = common_tools + visual_tools
        else:  # full
            tools = common_tools + text_tools + visual_tools

        # Add upload tool only if file_manager is provided (text/full modes only)
        if self._file_manager is not None and self.mode in ("text", "full"):
            tools.append(UploadTool(self.browser, self._file_manager))

        return tools

    async def _observe(self) -> List:
        """Get current page context for the LLM.

        Returns context with lifespan=1 so old page states don't pollute history.
        """
        content = []

        # Add file context first (if files provided)
        if self._file_manager and not self._file_manager.is_empty():
            content.append(
                Text(text=self._file_manager.format_context(), lifespan=1)
            )

        # Determine context flags based on agent mode
        include_dom = self.mode in ("text", "full")
        include_screenshot = self.mode in ("visual", "full")

        # Get page context from browser
        page_context = await self.browser.get_page_context(
            include_dom=include_dom, include_screenshot=include_screenshot
        )

        # Convert webtask content to dodo content with lifespan=1
        for item in page_context:
            if hasattr(item, "text"):
                content.append(Text(text=item.text, lifespan=1))
            elif hasattr(item, "data"):
                # Image content
                content.append(Image(base64=item.data, lifespan=1))

        return content

    def _create_dodo_agent(self) -> DodoAgent:
        """Create dodo agent with current configuration."""
        tools = self._create_browser_tools()
        return DodoAgent(
            llm=self.llm,
            tools=tools,
            observe=self._observe,
            stateful=self.stateful,
        )

    async def do(
        self,
        task: str,
        max_steps: int = 20,
        wait_after_action: float = 0.2,
        files: Optional[List[str]] = None,
        output_schema: Optional[Type[BaseModel]] = None,
        dom_mode: str = "accessibility",
    ) -> Result:
        """
        Execute a task using dodo's Agent.

        Args:
            task: Task description in natural language
            max_steps: Maximum number of steps to execute (default: 20)
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            files: Optional list of file paths for upload
            output_schema: Optional Pydantic model defining the expected output structure
            dom_mode: DOM serialization mode - "accessibility" (default) or "dom"

        Returns:
            Result with output and feedback

        Raises:
            TaskAbortedError: If task is aborted
        """
        # Configure browser
        self.browser.set_wait_after_action(wait_after_action)
        self.browser.set_mode(dom_mode)
        self._wait_after_action = wait_after_action
        self._dom_mode = dom_mode
        self._file_manager = FileManager(files) if files else None

        # Create dodo agent with current configuration
        dodo_agent = self._create_dodo_agent()

        try:
            result = await dodo_agent.do(
                task=task,
                max_iterations=max_steps,
                output_schema=output_schema,
            )
            return Result(output=result.output, feedback=result.feedback)
        except Exception as e:
            if "aborted" in str(e).lower():
                raise TaskAbortedError(str(e))
            raise

    async def verify(
        self,
        condition: str,
        max_steps: int = 10,
        wait_after_action: float = 0.2,
        dom_mode: str = "accessibility",
    ) -> Verdict:
        """
        Verify a condition on the current page.

        Args:
            condition: Condition to verify in natural language (e.g., "cart has 7 items")
            max_steps: Maximum number of steps to execute (default: 10)
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            dom_mode: DOM serialization mode - "accessibility" (default) or "dom"

        Returns:
            Verdict with passed (bool) and feedback (str)

        Raises:
            TaskAbortedError: If verification is aborted
        """
        # Configure browser
        self.browser.set_wait_after_action(wait_after_action)
        self.browser.set_mode(dom_mode)
        self._wait_after_action = wait_after_action
        self._dom_mode = dom_mode
        self._file_manager = None

        # Create dodo agent
        dodo_agent = self._create_dodo_agent()

        try:
            verdict = await dodo_agent.check(
                condition=condition,
                max_iterations=max_steps,
            )
            return Verdict(passed=verdict.passed, feedback=verdict.reason)
        except Exception as e:
            if "aborted" in str(e).lower():
                raise TaskAbortedError(str(e))
            raise

    async def extract(
        self,
        what: str,
        output_schema: Optional[Type[BaseModel]] = None,
        max_steps: int = 10,
        wait_after_action: float = 0.2,
        dom_mode: str = "accessibility",
    ):
        """
        Extract information from the current page.

        Args:
            what: What to extract in natural language (e.g., "total price", "product name")
            output_schema: Optional Pydantic model for structured output
            max_steps: Maximum steps to execute (default: 10)
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            dom_mode: DOM serialization mode - "accessibility" (default) or "dom"

        Returns:
            str if no output_schema provided, otherwise instance of output_schema

        Raises:
            TaskAbortedError: If extraction is aborted
        """
        # Configure browser
        self.browser.set_wait_after_action(wait_after_action)
        self.browser.set_mode(dom_mode)
        self._wait_after_action = wait_after_action
        self._dom_mode = dom_mode
        self._file_manager = None

        # Create dodo agent
        dodo_agent = self._create_dodo_agent()

        try:
            return await dodo_agent.tell(
                what=what,
                schema=output_schema,
                max_iterations=max_steps,
            )
        except Exception as e:
            if "aborted" in str(e).lower():
                raise TaskAbortedError(str(e))
            raise

    async def goto(self, url: str) -> None:
        """
        Go to a URL.

        Args:
            url: URL to go to
        """
        if not self.browser.has_current_page():
            await self.browser.open_tab()
        page = self.browser.get_current_page()
        await page.goto(url)

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
            RuntimeError: If no page is active
        """
        page = self.get_current_page()
        if page is None:
            raise RuntimeError(
                "No active page. Use goto() to navigate to a page first."
            )

        return await page.screenshot(path=path, full_page=full_page)

    async def wait(self, seconds: float) -> None:
        """
        Wait for a specific amount of time.

        Args:
            seconds: Number of seconds to wait
        """
        from webtask._internal.utils.wait import wait

        await wait(seconds)

    def get_current_page(self) -> Optional[Page]:
        """
        Get the current active page.

        Returns:
            Current Page instance, or None if no page is active
        """
        if not self.browser.has_current_page():
            return None
        return self.browser.get_current_page()

    def focus_tab(self, page: Page) -> None:
        """
        Focus a specific tab.

        Args:
            page: Page instance to focus
        """
        self.browser.focus_tab(page)
