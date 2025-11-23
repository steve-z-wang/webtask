"""Agent - main interface for web automation."""

import logging
from typing import List, Optional, Type
from pydantic import BaseModel, Field
from webtask.llm import LLM
from webtask.llm.tool import Tool
from webtask.browser import Context, Page
from webtask._internal.agent.task_runner import TaskRunner
from webtask._internal.agent.run import Run, TaskStatus
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
)
from webtask.exceptions import (
    TaskAbortedError,
    VerificationAbortedError,
    ExtractionAbortedError,
)
from .result import Result, Verdict
from webtask._internal.agent.agent_browser import AgentBrowser


class VerificationResult(BaseModel):
    """Structured output for verification tasks."""

    verified: bool = Field(description="True if the condition is met, False otherwise")


class Agent:
    """
    Main agent interface for web automation.

    Requires a Context for browser management and page operations.

    Primary interface:
    - High-level autonomous: do(task) - Agent autonomously executes tasks with Worker
    - Supports stateful for multi-turn conversations
    """

    def __init__(
        self,
        llm: LLM,
        context: Context,
        stateful: bool = True,
    ):
        """
        Initialize agent.

        Args:
            llm: LLM instance for reasoning and task execution
            context: Context instance for browser management
            stateful: If True, maintain conversation history between do() calls (default: True)
        """
        self.llm = llm
        self.context = context
        self.stateful = stateful
        self.logger = logging.getLogger(__name__)

        # Get coordinate_scale from LLM if available (e.g., GeminiComputerUse)
        coordinate_scale = getattr(llm, "coordinate_scale", None)

        # Create AgentBrowser once - shared across all do() calls
        self.browser = AgentBrowser(context=context, coordinate_scale=coordinate_scale)

        # Store previous runs if stateful=True
        # Accumulates runs from all do() calls for multi-turn conversations
        self._previous_runs: List[Run] = []

    def _create_browser_tools(
        self, file_manager: Optional[FileManager] = None
    ) -> List[Tool]:
        """Create browser tools for task execution.

        Args:
            file_manager: Optional FileManager for upload tool

        Returns:
            List of browser tools
        """
        tools: List[Tool] = [
            GotoTool(self.browser),
            ClickTool(self.browser),
            FillTool(self.browser),
            TypeTool(self.browser),
            WaitTool(),
            OpenTabTool(self.browser),
            SwitchTabTool(self.browser),
        ]

        # Add upload tool only if file_manager is provided
        if file_manager is not None:
            tools.append(UploadTool(self.browser, file_manager))

        return tools

    async def _run_task(
        self,
        task: str,
        max_steps: int,
        wait_after_action: float,
        mode: str,
        output_schema: Optional[Type[BaseModel]] = None,
        files: Optional[List[str]] = None,
        exception_class: Type[Exception] = TaskAbortedError,
    ) -> Run:
        """
        Internal method to run a task and throw on abort.

        Args:
            task: Task description
            max_steps: Maximum steps
            wait_after_action: Wait time after each action
            mode: DOM context mode
            output_schema: Optional output schema
            files: Optional list of file paths for upload
            exception_class: Exception class to raise on abort

        Returns:
            Run object with completed result

        Raises:
            exception_class: If task is aborted
        """
        from webtask.llm.message import Content, TextContent

        self.browser.set_wait_after_action(wait_after_action)
        self.browser.set_mode(mode)

        # Create file manager for this run
        file_manager = FileManager(files) if files else None

        # Create browser tools (including upload tool if files provided)
        tools = self._create_browser_tools(file_manager)

        # Create get_context callback that includes page context + file context
        async def get_context() -> List[Content]:
            content: List[Content] = []

            # Add file context first (if files provided)
            if file_manager and not file_manager.is_empty():
                content.append(TextContent(text=file_manager.format_context()))

            # Add page context (tabs, DOM, screenshot)
            page_context = await self.browser.get_page_context()
            content.extend(page_context)

            return content

        # Create TaskRunner for this run with tools and context callback
        task_runner = TaskRunner(
            llm=self.llm,
            tools=tools,
            get_context=get_context,
        )

        run = await task_runner.run(
            task,
            max_steps,
            previous_runs=self._previous_runs if self.stateful else None,
            output_schema=output_schema,
        )

        if self.stateful:
            self._previous_runs.append(run)

        if run.result.status == TaskStatus.ABORTED:
            raise exception_class(run.result.feedback or "Task aborted")

        return run

    async def do(
        self,
        task: str,
        max_steps: int = 20,
        wait_after_action: float = 0.2,
        files: Optional[List[str]] = None,
        output_schema: Optional[Type[BaseModel]] = None,
        mode: str = "accessibility",
    ) -> Result:
        """
        Execute a task using TaskRunner.

        Args:
            task: Task description in natural language
            max_steps: Maximum number of steps to execute (default: 20)
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            files: Optional list of file paths for upload
            output_schema: Optional Pydantic model defining the expected output structure
            mode: DOM context mode - "accessibility" (default) or "dom"

        Returns:
            Result with output and feedback

        Raises:
            TaskAbortedError: If task is aborted
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
        wait_after_action: float = 0.2,
        mode: str = "accessibility",
    ) -> Verdict:
        """
        Verify a condition on the current page.

        Args:
            condition: Condition to verify in natural language (e.g., "cart has 7 items")
            max_steps: Maximum number of steps to execute (default: 10)
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            mode: DOM context mode - "accessibility" (default) or "dom"

        Returns:
            Verdict with passed (bool) and feedback (str)

        Raises:
            VerificationAbortedError: If verification is aborted
        """
        task = f"Check if the following condition is true: {condition}"
        run = await self._run_task(
            task=task,
            max_steps=max_steps,
            wait_after_action=wait_after_action,
            mode=mode,
            output_schema=VerificationResult,
            exception_class=VerificationAbortedError,
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
        wait_after_action: float = 0.2,
        mode: str = "accessibility",
    ):
        """
        Extract information from the current page.

        Args:
            what: What to extract in natural language (e.g., "total price", "product name")
            output_schema: Optional Pydantic model for structured output
            max_steps: Maximum steps to execute (default: 10)
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            mode: DOM context mode - "accessibility" (default) or "dom"

        Returns:
            str if no output_schema provided, otherwise instance of output_schema

        Raises:
            ExtractionAbortedError: If extraction is aborted
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
            exception_class=ExtractionAbortedError,
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
