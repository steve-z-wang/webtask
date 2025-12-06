"""Agent - main interface for web automation."""

import logging
from typing import List, Optional, Type
from pydantic import BaseModel, Field
from webtask.llm import LLM
from webtask.llm.tool import Tool
from webtask.llm.message import Content, Text
from webtask.browser import Context, Page
from webtask._internal.agent.task_runner import TaskRunner
from webtask._internal.agent.run import Run, TaskStatus
from webtask._internal.agent.file_manager import FileManager
from webtask._internal.agent.tools import (
    GotoTool,
    ClickTool,
    TypeTool,
    SelectTool,
    UploadTool,
    OpenTabTool,
    SwitchTabTool,
    ClickAtTool,
    TypeAtTool,
    HoverAtTool,
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
from webtask._internal.prompts.worker_prompt import build_worker_prompt


class Agent:
    """
    Main agent interface for web automation.

    Requires a Context for browser management and page operations.

    Primary interface:
    - High-level autonomous: do(task) - Agent autonomously executes tasks with Worker
    - Maintains conversation history across do() calls (use clear_history() to reset)
    """

    # Valid modes for agent operation
    VALID_MODES = ("dom", "pixel")

    def __init__(
        self,
        llm: LLM,
        context: Context,
        mode: str = "dom",
        wait_after_action: float = 1.0,
    ):
        """
        Initialize agent.

        Args:
            llm: LLM instance for reasoning and task execution
            context: Context instance for browser management
            mode: Agent mode - "dom" (element IDs) or "pixel" (screen coordinates)
            wait_after_action: Wait time in seconds after each action (default: 1.0)
        """
        if mode not in self.VALID_MODES:
            raise ValueError(
                f"Invalid mode '{mode}'. Must be one of: {self.VALID_MODES}"
            )

        self.llm = llm
        self.context = context
        self.mode = mode
        self.wait_after_action = wait_after_action
        self.logger = logging.getLogger(__name__)

        # Get coordinate_scale from LLM if available (e.g., GeminiComputerUse)
        coordinate_scale = getattr(llm, "coordinate_scale", None)

        # Create AgentBrowser once - shared across all do() calls
        self.browser = AgentBrowser(context=context, coordinate_scale=coordinate_scale)

        # Accumulates runs from all do() calls for multi-turn conversations
        self._previous_runs: List[Run] = []

    def clear_history(self) -> None:
        """
        Clear conversation history.

        Resets the agent's memory of previous tasks, starting fresh.
        """
        self._previous_runs = []

    def _create_browser_tools(
        self, mode: str, file_manager: Optional[FileManager] = None
    ) -> List[Tool]:
        """Create browser tools based on agent mode.

        Args:
            mode: Agent mode - "dom" or "pixel"
            file_manager: Optional FileManager for upload tool

        Returns:
            List of browser tools appropriate for the mode
        """
        # Common tools for all modes (navigation + keyboard)
        common_tools: List[Tool] = [
            GotoTool(self.browser),
            GoBackTool(self.browser),
            GoForwardTool(self.browser),
            OpenTabTool(self.browser),
            SwitchTabTool(self.browser),
            KeyCombinationTool(self.browser),
        ]

        # DOM mode: element ID-based tools
        dom_tools: List[Tool] = [
            ClickTool(self.browser),
            TypeTool(self.browser),
            SelectTool(self.browser),
        ]

        # Pixel mode: coordinate-based tools
        pixel_tools: List[Tool] = [
            ClickAtTool(self.browser),
            TypeAtTool(self.browser),
            HoverAtTool(self.browser),
            ScrollAtTool(self.browser),
            ScrollDocumentTool(self.browser),
            DragAndDropTool(self.browser),
        ]

        # Build tool list based on mode
        if mode == "dom":
            tools = common_tools + dom_tools
        else:  # pixel
            tools = common_tools + pixel_tools

        # Add upload tool only if file_manager is provided (dom mode only)
        if file_manager is not None and mode == "dom":
            tools.append(UploadTool(self.browser, file_manager))

        return tools

    async def _run_task(
        self,
        task: str,
        max_steps: int,
        wait_after_action: Optional[float] = None,
        mode: Optional[str] = None,
        output_schema: Optional[Type[BaseModel]] = None,
        files: Optional[List[str]] = None,
        exception_class: Type[Exception] = TaskAbortedError,
    ) -> Run:
        """
        Internal method to run a task and throw on abort.

        Args:
            task: Task description
            max_steps: Maximum steps
            wait_after_action: Wait time after each action (uses agent default if not specified)
            mode: Agent mode - "dom" or "pixel" (uses agent default if not specified)
            output_schema: Optional output schema
            files: Optional list of file paths for upload
            exception_class: Exception class to raise on abort

        Returns:
            Run object with completed result

        Raises:
            exception_class: If task is aborted
            ValueError: If invalid mode is provided
        """
        # Resolve defaults
        wait_after_action = (
            wait_after_action
            if wait_after_action is not None
            else self.wait_after_action
        )
        mode = mode if mode is not None else self.mode

        # Validate mode
        if mode not in self.VALID_MODES:
            raise ValueError(
                f"Invalid mode '{mode}'. Must be one of: {self.VALID_MODES}"
            )

        self.browser.set_wait_after_action(wait_after_action)
        self.browser.set_mode("dom")

        # Create file manager for this run
        file_manager = FileManager(files) if files else None

        # Create browser tools (including upload tool if files provided)
        tools = self._create_browser_tools(mode, file_manager)

        # Determine context flags based on mode
        # Both modes get screenshots, only dom mode gets DOM context
        include_dom = mode == "dom"
        include_screenshot = True

        # Create get_context callback that includes page context + file context
        async def get_context() -> List[Content]:
            content: List[Content] = []

            # Add file context first (if files provided)
            if file_manager and not file_manager.is_empty():
                content.append(Text(text=file_manager.format_context()))

            # Add page context based on agent mode
            page_context = await self.browser.get_page_context(
                include_dom=include_dom, include_screenshot=include_screenshot
            )
            content.extend(page_context)

            return content

        # Create TaskRunner for this run with tools and context callback
        task_runner = TaskRunner(
            llm=self.llm,
            tools=tools,
            get_context=get_context,
            system_prompt=build_worker_prompt(),
        )

        run = await task_runner.run(
            task,
            max_steps,
            previous_runs=self._previous_runs,
            output_schema=output_schema,
        )

        self._previous_runs.append(run)

        if run.result.status == TaskStatus.ABORTED:
            raise exception_class(run.result.feedback or "Task aborted")

        return run

    async def do(
        self,
        task: str,
        max_steps: int = 20,
        wait_after_action: Optional[float] = None,
        mode: Optional[str] = None,
        files: Optional[List[str]] = None,
        output_schema: Optional[Type[BaseModel]] = None,
    ) -> Result:
        """
        Execute a task using TaskRunner.

        Args:
            task: Task description in natural language
            max_steps: Maximum number of steps to execute (default: 20)
            wait_after_action: Wait time in seconds after each action (uses agent default if not specified)
            mode: Agent mode - "dom" or "pixel" (uses agent default if not specified)
            files: Optional list of file paths for upload
            output_schema: Optional Pydantic model defining the expected output structure

        Returns:
            Result with output and feedback

        Raises:
            TaskAbortedError: If task is aborted
            ValueError: If invalid mode is provided
        """
        run = await self._run_task(
            task=task,
            max_steps=max_steps,
            wait_after_action=wait_after_action,
            mode=mode,
            output_schema=output_schema,
            files=files,
            exception_class=TaskAbortedError,
        )

        return Result(output=run.result.output, feedback=run.result.feedback)

    async def verify(
        self,
        condition: str,
        max_steps: int = 10,
        wait_after_action: Optional[float] = None,
        mode: Optional[str] = None,
    ) -> Verdict:
        """
        Verify a condition on the current page.

        Args:
            condition: Condition to verify in natural language (e.g., "cart has 7 items")
            max_steps: Maximum number of steps to execute (default: 10)
            wait_after_action: Wait time in seconds after each action (uses agent default if not specified)
            mode: Agent mode - "dom" or "pixel" (uses agent default if not specified)

        Returns:
            Verdict with passed (bool) and feedback (str)

        Raises:
            TaskAbortedError: If verification is aborted
            ValueError: If invalid mode is provided
        """

        class VerificationResult(BaseModel):
            """Structured output for verification."""

            verified: bool = Field(
                description="True if the condition is met, False otherwise"
            )

        task = f"Check if the following condition is true: {condition}"
        run = await self._run_task(
            task=task,
            max_steps=max_steps,
            wait_after_action=wait_after_action,
            mode=mode,
            output_schema=VerificationResult,
            exception_class=TaskAbortedError,
        )

        if not run.result.output:
            raise RuntimeError("Verification failed: no structured output received")

        return Verdict(
            passed=run.result.output.verified,
            feedback=run.result.feedback or "",
        )

    async def extract(
        self,
        what: str,
        output_schema: Optional[Type[BaseModel]] = None,
        max_steps: int = 10,
        wait_after_action: Optional[float] = None,
        mode: Optional[str] = None,
    ):
        """
        Extract information from the current page.

        Args:
            what: What to extract in natural language (e.g., "total price", "product name")
            output_schema: Optional Pydantic model for structured output
            max_steps: Maximum steps to execute (default: 10)
            wait_after_action: Wait time in seconds after each action (uses agent default if not specified)
            mode: Agent mode - "dom" or "pixel" (uses agent default if not specified)

        Returns:
            str if no output_schema provided, otherwise instance of output_schema

        Raises:
            TaskAbortedError: If extraction is aborted
            ValueError: If invalid mode is provided
        """

        # Default to str schema if none provided
        class StrOutput(BaseModel):
            """String output for extraction."""

            value: str = Field(description=f"The extracted {what}")

        schema = output_schema or StrOutput
        task = f"Extract the following information: {what}"

        run = await self._run_task(
            task=task,
            max_steps=max_steps,
            wait_after_action=wait_after_action,
            mode=mode,
            output_schema=schema,
            exception_class=TaskAbortedError,
        )

        # Return extracted value directly
        if output_schema:
            return run.result.output
        else:
            return run.result.output.value if run.result.output else ""

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

    async def wait_for_load(self, timeout: int = 10000) -> None:
        """
        Wait for the current page to fully load.

        Args:
            timeout: Maximum time to wait in milliseconds (default: 10000ms = 10s)

        Raises:
            RuntimeError: If no page is active
            TimeoutError: If page doesn't load within timeout
        """
        page = self.get_current_page()
        if page is None:
            raise RuntimeError(
                "No active page. Use goto() to navigate to a page first."
            )
        await page.wait_for_load(timeout=timeout)

    async def wait_for_network_idle(self, timeout: int = 10000) -> None:
        """
        Wait for network to be idle (no requests for 500ms).

        Useful for SPAs and pages with AJAX requests.

        Args:
            timeout: Maximum time to wait in milliseconds (default: 10000ms = 10s)

        Raises:
            RuntimeError: If no page is active
            TimeoutError: If network doesn't become idle within timeout
        """
        page = self.get_current_page()
        if page is None:
            raise RuntimeError(
                "No active page. Use goto() to navigate to a page first."
            )
        await page.wait_for_network_idle(timeout=timeout)

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

    async def get_debug_context(self) -> str:
        """
        Get the text context that the LLM sees (for debugging).

        Returns the DOM snapshot and tabs context as a string.
        Useful for debugging when elements can't be found in text mode.

        Returns:
            The text representation of the current page state
        """
        content_list = await self.browser.get_page_context(
            include_dom=True, include_screenshot=False
        )
        parts = []
        for content in content_list:
            if hasattr(content, "text"):
                parts.append(content.text)
        return "\n\n".join(parts)
