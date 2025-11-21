"""Agent - main interface for web automation."""

import logging
from typing import Dict, List, Optional, Type
from pydantic import BaseModel, Field
from webtask.llm import LLM
from webtask.browser import Context, Page
from webtask._internal.agent.task_runner import TaskRunner
from webtask._internal.agent.run import Result, Run
from .result import Status, Verdict
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

        # Create AgentBrowser once - shared across all do() calls
        # This preserves page state between tasks
        self.browser = AgentBrowser(context=context)

        # Create TaskRunner once - stateless executor reused across all do() calls
        self.task_runner = TaskRunner(llm=llm, browser=self.browser)

        # Store previous runs if stateful=True
        # Accumulates runs from all do() calls for multi-turn conversations
        self._previous_runs: List[Run] = []

    async def do(
        self,
        task: str,
        max_steps: int = 20,
        wait_after_action: float = 0.2,
        resources: Optional[Dict[str, str]] = None,
        output_schema: Optional[Type[BaseModel]] = None,
        mode: str = "accessibility",
    ) -> Result:
        """
        Execute a task using TaskRunner.

        Args:
            task: Task description in natural language
            max_steps: Maximum number of steps to execute (default: 20)
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            resources: Optional dict of file resources (name -> path)
            output_schema: Optional Pydantic model defining the expected output structure
            mode: DOM context mode - "accessibility" (default) or "dom"

        Returns:
            Result with status, output, and feedback
        """
        # Set task-specific browser settings
        self.browser.set_wait_after_action(wait_after_action)
        self.browser.set_mode(mode)

        run = await self.task_runner.run(
            task,
            max_steps,
            previous_runs=self._previous_runs if self.stateful else None,
            output_schema=output_schema,
            resources=resources,
        )

        if self.stateful:
            self._previous_runs.append(run)

        return run.result

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
            Verdict with passed (bool), feedback (str), and status (Status)
        """
        # Set task-specific browser settings
        self.browser.set_wait_after_action(wait_after_action)
        self.browser.set_mode(mode)

        # Run verification task with structured output
        task = f"Check if the following condition is true: {condition}"
        run = await self.task_runner.run(
            task,
            max_steps,
            previous_runs=self._previous_runs if self.stateful else None,
            output_schema=VerificationResult,
            resources=None,
        )

        if self.stateful:
            self._previous_runs.append(run)

        # Convert Result to Verdict using structured output
        if not run.result.output:
            raise RuntimeError("Verification failed: no structured output received")

        return Verdict(
            passed=run.result.output.verified,
            feedback=run.result.feedback or "",
            status=run.result.status or Status.ABORTED,
        )

    async def goto(self, url: str) -> None:
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to
        """
        await self.browser.navigate(url)

    def get_current_page(self) -> Optional[Page]:
        """
        Get the current active page.

        Returns:
            Current Page instance, or None if no page is active
        """
        return self.browser.get_current_page()
