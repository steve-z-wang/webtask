"""Agent - main interface for web automation."""

import logging
from typing import Dict, List, Optional
from webtask.llm import LLM
from webtask.browser import Context
from webtask._internal.agent.task_runner import TaskRunner
from webtask._internal.agent.run import Result, Run
from webtask._internal.agent.agent_browser import AgentBrowser


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
        stateful: bool = False,
        wait_after_action: float = 0.2,
        mode: str = "accessibility",
    ):
        """
        Initialize agent.

        Args:
            llm: LLM instance for reasoning and task execution
            context: Context instance for browser management
            wait_after_action: Wait time in seconds after each action (default: 0.2)
            mode: DOM context mode - "accessibility" (default) or "dom"
            stateful: If True, maintain conversation history between do() calls (default: False)
        """
        self.llm = llm
        self.context = context
        self.wait_after_action = wait_after_action
        self.mode = mode
        self.stateful = stateful
        self.logger = logging.getLogger(__name__)

        # Create AgentBrowser once - shared across all do() calls
        # This preserves page state between tasks
        self.browser = AgentBrowser(
            context=context, wait_after_action=wait_after_action
        )

        # Store previous runs if stateful=True
        # Accumulates runs from all do() calls for multi-turn conversations
        self._previous_runs: List[Run] = []

    async def do(
        self,
        task: str,
        max_steps: int = 20,
        resources: Optional[Dict[str, str]] = None,
        wait_after_action: Optional[float] = None,
        mode: Optional[str] = None,
    ) -> Result:
        """
        Execute a task using TaskRunner.

        Args:
            task: Task description in natural language
            max_steps: Maximum number of steps to execute (default: 20)
            resources: Optional dict of file resources (name -> path)
            wait_after_action: Wait time in seconds after each action (overrides agent default if provided)
            mode: DOM context mode - "accessibility" or "dom" (overrides agent default if provided)

        Returns:
            Result with status, output, and feedback
        """
        # Temporarily override wait_after_action if provided
        original_wait = None
        if wait_after_action is not None:
            original_wait = self.browser._wait_after_action
            self.browser.set_wait_after_action(wait_after_action)

        effective_mode = mode if mode is not None else self.mode

        try:
            runner = TaskRunner(
                llm=self.llm,
                browser=self.browser,
                resources=resources,
                mode=effective_mode,
            )

            run = await runner.run(
                task,
                previous_runs=self._previous_runs if self.stateful else None,
                max_steps=max_steps,
            )

            if self.stateful:
                self._previous_runs.append(run)

            return run.result
        finally:
            # Restore original wait_after_action if it was overridden
            if original_wait is not None:
                self.browser.set_wait_after_action(original_wait)

    async def close(self) -> None:
        """Close the agent and cleanup context."""
        if self.context:
            await self.context.close()
